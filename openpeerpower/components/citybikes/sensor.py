"""Sensor for the CityBikes data."""
import asyncio
from datetime import timedelta
import logging

import aiohttp
import async_timeout
import voluptuous as vol

from openpeerpower.components.sensor import (
    ENTITY_ID_FORMAT,
    PLATFORM_SCHEMA,
    SensorEntity,
)
from openpeerpower.const import (
    ATTR_ATTRIBUTION,
    ATTR_ID,
    ATTR_LATITUDE,
    ATTR_LOCATION,
    ATTR_LONGITUDE,
    ATTR_NAME,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    CONF_RADIUS,
    LENGTH_FEET,
    LENGTH_METERS,
)
from openpeerpower.exceptions import PlatformNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.entity import async_generate_entity_id
from openpeerpower.helpers.event import async_track_time_interval
from openpeerpower.util import distance, location

_LOGGER = logging.getLogger(__name__)

ATTR_EMPTY_SLOTS = "empty_slots"
ATTR_EXTRA = "extra"
ATTR_FREE_BIKES = "free_bikes"
ATTR_NETWORK = "network"
ATTR_NETWORKS_LIST = "networks"
ATTR_STATIONS_LIST = "stations"
ATTR_TIMESTAMP = "timestamp"
ATTR_UID = "uid"

CONF_NETWORK = "network"
CONF_STATIONS_LIST = "stations"

DEFAULT_ENDPOINT = "https://api.citybik.es/{uri}"
PLATFORM = "citybikes"

MONITORED_NETWORKS = "monitored-networks"

NETWORKS_URI = "v2/networks"

REQUEST_TIMEOUT = 5  # In seconds; argument to asyncio.timeout

SCAN_INTERVAL = timedelta(minutes=5)  # Timely, and doesn't suffocate the API

STATIONS_URI = "v2/networks/{uid}?fields=network.stations"

CITYBIKES_ATTRIBUTION = (
    "Information provided by the CityBikes Project (https://citybik.es/#about)"
)

CITYBIKES_NETWORKS = "citybikes_networks"

PLATFORM_SCHEMA = vol.All(
    cv.has_at_least_one_key(CONF_RADIUS, CONF_STATIONS_LIST),
    PLATFORM_SCHEMA.extend(
        {
            vol.Optional(CONF_NAME, default=""): cv.string,
            vol.Optional(CONF_NETWORK): cv.string,
            vol.Inclusive(CONF_LATITUDE, "coordinates"): cv.latitude,
            vol.Inclusive(CONF_LONGITUDE, "coordinates"): cv.longitude,
            vol.Optional(CONF_RADIUS, "station_filter"): cv.positive_int,
            vol.Optional(CONF_STATIONS_LIST, "station_filter"): vol.All(
                cv.ensure_list, vol.Length(min=1), [cv.string]
            ),
        }
    ),
)

NETWORK_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ID): cv.string,
        vol.Required(ATTR_NAME): cv.string,
        vol.Required(ATTR_LOCATION): vol.Schema(
            {
                vol.Required(ATTR_LATITUDE): cv.latitude,
                vol.Required(ATTR_LONGITUDE): cv.longitude,
            },
            extra=vol.REMOVE_EXTRA,
        ),
    },
    extra=vol.REMOVE_EXTRA,
)

NETWORKS_RESPONSE_SCHEMA = vol.Schema(
    {vol.Required(ATTR_NETWORKS_LIST): [NETWORK_SCHEMA]}
)

STATION_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_FREE_BIKES): cv.positive_int,
        vol.Required(ATTR_EMPTY_SLOTS): vol.Any(cv.positive_int, None),
        vol.Required(ATTR_LATITUDE): cv.latitude,
        vol.Required(ATTR_LONGITUDE): cv.longitude,
        vol.Required(ATTR_ID): cv.string,
        vol.Required(ATTR_NAME): cv.string,
        vol.Required(ATTR_TIMESTAMP): cv.string,
        vol.Optional(ATTR_EXTRA): vol.Schema(
            {vol.Optional(ATTR_UID): cv.string}, extra=vol.REMOVE_EXTRA
        ),
    },
    extra=vol.REMOVE_EXTRA,
)

STATIONS_RESPONSE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_NETWORK): vol.Schema(
            {vol.Required(ATTR_STATIONS_LIST): [STATION_SCHEMA]}, extra=vol.REMOVE_EXTRA
        )
    }
)


class CityBikesRequestError(Exception):
    """Error to indicate a CityBikes API request has failed."""


async def async_citybikes_request(opp, uri, schema):
    """Perform a request to CityBikes API endpoint, and parse the response."""
    try:
        session = async_get_clientsession(opp)

        with async_timeout.timeout(REQUEST_TIMEOUT):
            req = await session.get(DEFAULT_ENDPOINT.format(uri=uri))

        json_response = await req.json()
        return schema(json_response)
    except (asyncio.TimeoutError, aiohttp.ClientError):
        _LOGGER.error("Could not connect to CityBikes API endpoint")
    except ValueError:
        _LOGGER.error("Received non-JSON data from CityBikes API endpoint")
    except vol.Invalid as err:
        _LOGGER.error("Received unexpected JSON from CityBikes API endpoint: %s", err)
    raise CityBikesRequestError


async def async_setup_platform(opp, config, async_add_entities, discovery_info=None):
    """Set up the CityBikes platform."""
    if PLATFORM not in opp.data:
        opp.data[PLATFORM] = {MONITORED_NETWORKS: {}}

    latitude = config.get(CONF_LATITUDE, opp.config.latitude)
    longitude = config.get(CONF_LONGITUDE, opp.config.longitude)
    network_id = config.get(CONF_NETWORK)
    stations_list = set(config.get(CONF_STATIONS_LIST, []))
    radius = config.get(CONF_RADIUS, 0)
    name = config[CONF_NAME]
    if not opp.config.units.is_metric:
        radius = distance.convert(radius, LENGTH_FEET, LENGTH_METERS)

    # Create a single instance of CityBikesNetworks.
    networks = opp.data.setdefault(CITYBIKES_NETWORKS, CityBikesNetworks(opp))

    if not network_id:
        network_id = await networks.get_closest_network_id(latitude, longitude)

    if network_id not in opp.data[PLATFORM][MONITORED_NETWORKS]:
        network = CityBikesNetwork(opp, network_id)
        opp.data[PLATFORM][MONITORED_NETWORKS][network_id] = network
        opp.async_create_task(network.async_refresh())
        async_track_time_interval(opp, network.async_refresh, SCAN_INTERVAL)
    else:
        network = opp.data[PLATFORM][MONITORED_NETWORKS][network_id]

    await network.ready.wait()

    devices = []
    for station in network.stations:
        dist = location.distance(
            latitude, longitude, station[ATTR_LATITUDE], station[ATTR_LONGITUDE]
        )
        station_id = station[ATTR_ID]
        station_uid = str(station.get(ATTR_EXTRA, {}).get(ATTR_UID, ""))

        if radius > dist or stations_list.intersection((station_id, station_uid)):
            if name:
                uid = "_".join([network.network_id, name, station_id])
            else:
                uid = "_".join([network.network_id, station_id])
            entity_id = async_generate_entity_id(ENTITY_ID_FORMAT, uid, opp=opp)
            devices.append(CityBikesStation(network, station_id, entity_id))

    async_add_entities(devices, True)


class CityBikesNetworks:
    """Represent all CityBikes networks."""

    def __init__(self, opp):
        """Initialize the networks instance."""
        self.opp = opp
        self.networks = None
        self.networks_loading = asyncio.Condition()

    async def get_closest_network_id(self, latitude, longitude):
        """Return the id of the network closest to provided location."""
        try:
            await self.networks_loading.acquire()
            if self.networks is None:
                networks = await async_citybikes_request(
                    self.opp, NETWORKS_URI, NETWORKS_RESPONSE_SCHEMA
                )
                self.networks = networks[ATTR_NETWORKS_LIST]
            result = None
            minimum_dist = None
            for network in self.networks:
                network_latitude = network[ATTR_LOCATION][ATTR_LATITUDE]
                network_longitude = network[ATTR_LOCATION][ATTR_LONGITUDE]
                dist = location.distance(
                    latitude, longitude, network_latitude, network_longitude
                )
                if minimum_dist is None or dist < minimum_dist:
                    minimum_dist = dist
                    result = network[ATTR_ID]

            return result
        except CityBikesRequestError as err:
            raise PlatformNotReady from err
        finally:
            self.networks_loading.release()


class CityBikesNetwork:
    """Thin wrapper around a CityBikes network object."""

    def __init__(self, opp, network_id):
        """Initialize the network object."""
        self.opp = opp
        self.network_id = network_id
        self.stations = []
        self.ready = asyncio.Event()

    async def async_refresh(self, now=None):
        """Refresh the state of the network."""
        try:
            network = await async_citybikes_request(
                self.opp,
                STATIONS_URI.format(uid=self.network_id),
                STATIONS_RESPONSE_SCHEMA,
            )
            self.stations = network[ATTR_NETWORK][ATTR_STATIONS_LIST]
            self.ready.set()
        except CityBikesRequestError as err:
            if now is not None:
                self.ready.clear()
            else:
                raise PlatformNotReady from err


class CityBikesStation(SensorEntity):
    """CityBikes API Sensor."""

    def __init__(self, network, station_id, entity_id):
        """Initialize the sensor."""
        self._network = network
        self._station_id = station_id
        self._station_data = {}
        self.entity_id = entity_id

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._station_data.get(ATTR_FREE_BIKES)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._station_data.get(ATTR_NAME)

    async def async_update(self):
        """Update station state."""
        for station in self._network.stations:
            if station[ATTR_ID] == self._station_id:
                self._station_data = station
                break

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if self._station_data:
            return {
                ATTR_ATTRIBUTION: CITYBIKES_ATTRIBUTION,
                ATTR_UID: self._station_data.get(ATTR_EXTRA, {}).get(ATTR_UID),
                ATTR_LATITUDE: self._station_data[ATTR_LATITUDE],
                ATTR_LONGITUDE: self._station_data[ATTR_LONGITUDE],
                ATTR_EMPTY_SLOTS: self._station_data[ATTR_EMPTY_SLOTS],
                ATTR_TIMESTAMP: self._station_data[ATTR_TIMESTAMP],
            }
        return {ATTR_ATTRIBUTION: CITYBIKES_ATTRIBUTION}

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "bikes"

    @property
    def icon(self):
        """Return the icon."""
        return "mdi:bike"
