"""The Airly integration."""
import asyncio
from datetime import timedelta
import logging
from math import ceil

from aiohttp.client_exceptions import ClientConnectorError
from airly import Airly
from airly.exceptions import AirlyError
import async_timeout

from openpeerpower.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE
from openpeerpower.core import Config, OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ATTR_API_ADVICE,
    ATTR_API_CAQI,
    ATTR_API_CAQI_DESCRIPTION,
    ATTR_API_CAQI_LEVEL,
    CONF_USE_NEAREST,
    DOMAIN,
    MAX_REQUESTS_PER_DAY,
    NO_AIRLY_SENSORS,
)

PLATFORMS = ["air_quality", "sensor"]

_LOGGER = logging.getLogger(__name__)


def set_update_interval(opp, instances):
    """Set update_interval to another configured Airly instances."""
    # We check how many Airly configured instances are and calculate interval to not
    # exceed allowed numbers of requests.
    interval = timedelta(minutes=ceil(24 * 60 / MAX_REQUESTS_PER_DAY) * instances)

    if opp.data.get(DOMAIN):
        for instance in opp.data[DOMAIN].values():
            instance.update_interval = interval

    return interval


async def async_setup(opp: OpenPeerPower, config: Config) -> bool:
    """Set up configured Airly."""
    return True


async def async_setup_entry(opp, config_entry):
    """Set up Airly as config entry."""
    api_key = config_entry.data[CONF_API_KEY]
    latitude = config_entry.data[CONF_LATITUDE]
    longitude = config_entry.data[CONF_LONGITUDE]
    use_nearest = config_entry.data.get(CONF_USE_NEAREST, False)

    # For backwards compat, set unique ID
    if config_entry.unique_id is None:
        opp.config_entries.async_update_entry(
            config_entry, unique_id=f"{latitude}-{longitude}"
        )

    websession = async_get_clientsession(opp)
    # Change update_interval for other Airly instances
    update_interval = set_update_interval(
        opp, len(opp.config_entries.async_entries(DOMAIN))
    )

    coordinator = AirlyDataUpdateCoordinator(
        opp, websession, api_key, latitude, longitude, update_interval, use_nearest
    )
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][config_entry.entry_id] = coordinator

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    return True


async def async_unload_entry(opp, config_entry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(config_entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        opp.data[DOMAIN].pop(config_entry.entry_id)

    # Change update_interval for other Airly instances
    set_update_interval(opp, len(opp.data[DOMAIN]))

    return unload_ok


class AirlyDataUpdateCoordinator(DataUpdateCoordinator):
    """Define an object to hold Airly data."""

    def __init__(
        self,
        opp,
        session,
        api_key,
        latitude,
        longitude,
        update_interval,
        use_nearest,
    ):
        """Initialize."""
        self.latitude = latitude
        self.longitude = longitude
        self.airly = Airly(api_key, session)
        self.use_nearest = use_nearest

        super().__init__(opp, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_update_data(self):
        """Update data via library."""
        data = {}
        if self.use_nearest:
            measurements = self.airly.create_measurements_session_nearest(
                self.latitude, self.longitude, max_distance_km=5
            )
        else:
            measurements = self.airly.create_measurements_session_point(
                self.latitude, self.longitude
            )
        with async_timeout.timeout(20):
            try:
                await measurements.update()
            except (AirlyError, ClientConnectorError) as error:
                raise UpdateFailed(error) from error

        _LOGGER.debug(
            "Requests remaining: %s/%s",
            self.airly.requests_remaining,
            self.airly.requests_per_day,
        )

        values = measurements.current["values"]
        index = measurements.current["indexes"][0]
        standards = measurements.current["standards"]

        if index["description"] == NO_AIRLY_SENSORS:
            raise UpdateFailed("Can't retrieve data: no Airly sensors in this area")
        for value in values:
            data[value["name"]] = value["value"]
        for standard in standards:
            data[f"{standard['pollutant']}_LIMIT"] = standard["limit"]
            data[f"{standard['pollutant']}_PERCENT"] = standard["percent"]
        data[ATTR_API_CAQI] = index["value"]
        data[ATTR_API_CAQI_LEVEL] = index["level"].lower().replace("_", " ")
        data[ATTR_API_CAQI_DESCRIPTION] = index["description"]
        data[ATTR_API_ADVICE] = index["advice"]
        return data
