"""Support for NSW Rural Fire Service Feeds."""
from datetime import timedelta
import logging
from typing import Optional

from aio_geojson_nsw_rfs_incidents import NswRuralFireServiceIncidentsFeedManager
import voluptuous as vol

from openpeerpower.components.geo_location import PLATFORM_SCHEMA, GeolocationEvent
from openpeerpower.const import (
    ATTR_ATTRIBUTION,
    ATTR_LOCATION,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_RADIUS,
    CONF_SCAN_INTERVAL,
    EVENT_OPENPEERPOWER_START,
    EVENT_OPENPEERPOWER_STOP,
    LENGTH_KILOMETERS,
)
from openpeerpower.core import callback
from openpeerpower.helpers import aiohttp_client, config_validation as cv
from openpeerpower.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from openpeerpower.helpers.event import async_track_time_interval
from openpeerpower.helpers.typing import ConfigType, OpenPeerPowerType

_LOGGER = logging.getLogger(__name__)

ATTR_CATEGORY = "category"
ATTR_COUNCIL_AREA = "council_area"
ATTR_EXTERNAL_ID = "external_id"
ATTR_FIRE = "fire"
ATTR_PUBLICATION_DATE = "publication_date"
ATTR_RESPONSIBLE_AGENCY = "responsible_agency"
ATTR_SIZE = "size"
ATTR_STATUS = "status"
ATTR_TYPE = "type"

CONF_CATEGORIES = "categories"

DEFAULT_RADIUS_IN_KM = 20.0

SCAN_INTERVAL = timedelta(minutes=5)

SIGNAL_DELETE_ENTITY = "nsw_rural_fire_service_feed_delete_{}"
SIGNAL_UPDATE_ENTITY = "nsw_rural_fire_service_feed_update_{}"

SOURCE = "nsw_rural_fire_service_feed"

VALID_CATEGORIES = ["Advice", "Emergency Warning", "Not Applicable", "Watch and Act"]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_CATEGORIES, default=[]): vol.All(
            cv.ensure_list, [vol.In(VALID_CATEGORIES)]
        ),
        vol.Optional(CONF_LATITUDE): cv.latitude,
        vol.Optional(CONF_LONGITUDE): cv.longitude,
        vol.Optional(CONF_RADIUS, default=DEFAULT_RADIUS_IN_KM): vol.Coerce(float),
    }
)


async def async_setup_platform(
    opp: OpenPeerPowerType, config: ConfigType, async_add_entities, discovery_info=None
):
    """Set up the NSW Rural Fire Service Feed platform."""
    scan_interval = config.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL)
    coordinates = (
        config.get(CONF_LATITUDE, opp.config.latitude),
        config.get(CONF_LONGITUDE, opp.config.longitude),
    )
    radius_in_km = config[CONF_RADIUS]
    categories = config.get(CONF_CATEGORIES)
    # Initialize the entity manager.
    manager = NswRuralFireServiceFeedEntityManager(
        opp, async_add_entities, scan_interval, coordinates, radius_in_km, categories
    )

    async def start_feed_manager(event):
        """Start feed manager."""
        await manager.async_init()

    async def stop_feed_manager(event):
        """Stop feed manager."""
        await manager.async_stop()

    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_START, start_feed_manager)
    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, stop_feed_manager)
    opp.async_create_task(manager.async_update())


class NswRuralFireServiceFeedEntityManager:
    """Feed Entity Manager for NSW Rural Fire Service GeoJSON feed."""

    def __init__(
        self,
        opp,
        async_add_entities,
        scan_interval,
        coordinates,
        radius_in_km,
        categories,
    ):
        """Initialize the Feed Entity Manager."""
        self._opp = opp
        websession = aiohttp_client.async_get_clientsession(opp)
        self._feed_manager = NswRuralFireServiceIncidentsFeedManager(
            websession,
            self._generate_entity,
            self._update_entity,
            self._remove_entity,
            coordinates,
            filter_radius=radius_in_km,
            filter_categories=categories,
        )
        self._async_add_entities = async_add_entities
        self._scan_interval = scan_interval
        self._track_time_remove_callback = None

    async def async_init(self):
        """Schedule initial and regular updates based on configured time interval."""

        async def update(event_time):
            """Update."""
            await self.async_update()

        # Trigger updates at regular intervals.
        self._track_time_remove_callback = async_track_time_interval(
            self._opp, update, self._scan_interval
        )

        _LOGGER.debug("Feed entity manager initialized")

    async def async_update(self):
        """Refresh data."""
        await self._feed_manager.update()
        _LOGGER.debug("Feed entity manager updated")

    async def async_stop(self):
        """Stop this feed entity manager from refreshing."""
        if self._track_time_remove_callback:
            self._track_time_remove_callback()
        _LOGGER.debug("Feed entity manager stopped")

    def get_entry(self, external_id):
        """Get feed entry by external id."""
        return self._feed_manager.feed_entries.get(external_id)

    async def _generate_entity(self, external_id):
        """Generate new entity."""
        new_entity = NswRuralFireServiceLocationEvent(self, external_id)
        # Add new entities to HA.
        self._async_add_entities([new_entity], True)

    async def _update_entity(self, external_id):
        """Update entity."""
        async_dispatcher_send(self._opp, SIGNAL_UPDATE_ENTITY.format(external_id))

    async def _remove_entity(self, external_id):
        """Remove entity."""
        async_dispatcher_send(self._opp, SIGNAL_DELETE_ENTITY.format(external_id))


class NswRuralFireServiceLocationEvent(GeolocationEvent):
    """This represents an external event with NSW Rural Fire Service data."""

    def __init__(self, feed_manager, external_id):
        """Initialize entity with data from feed entry."""
        self._feed_manager = feed_manager
        self._external_id = external_id
        self._name = None
        self._distance = None
        self._latitude = None
        self._longitude = None
        self._attribution = None
        self._category = None
        self._publication_date = None
        self._location = None
        self._council_area = None
        self._status = None
        self._type = None
        self._fire = None
        self._size = None
        self._responsible_agency = None
        self._remove_signal_delete = None
        self._remove_signal_update = None

    async def async_added_to_opp(self):
        """Call when entity is added to opp."""
        self._remove_signal_delete = async_dispatcher_connect(
            self.opp,
            SIGNAL_DELETE_ENTITY.format(self._external_id),
            self._delete_callback,
        )
        self._remove_signal_update = async_dispatcher_connect(
            self.opp,
            SIGNAL_UPDATE_ENTITY.format(self._external_id),
            self._update_callback,
        )

    async def async_will_remove_from_opp(self) -> None:
        """Call when entity will be removed from opp."""
        self._remove_signal_delete()
        self._remove_signal_update()

    @callback
    def _delete_callback(self):
        """Remove this entity."""
        self.opp.async_create_task(self.async_remove(force_remove=True))

    @callback
    def _update_callback(self):
        """Call update method."""
        self.async_schedule_update_op_state(True)

    @property
    def should_poll(self):
        """No polling needed for NSW Rural Fire Service location events."""
        return False

    async def async_update(self):
        """Update this entity from the data held in the feed manager."""
        _LOGGER.debug("Updating %s", self._external_id)
        feed_entry = self._feed_manager.get_entry(self._external_id)
        if feed_entry:
            self._update_from_feed(feed_entry)

    def _update_from_feed(self, feed_entry):
        """Update the internal state from the provided feed entry."""
        self._name = feed_entry.title
        self._distance = feed_entry.distance_to_home
        self._latitude = feed_entry.coordinates[0]
        self._longitude = feed_entry.coordinates[1]
        self._attribution = feed_entry.attribution
        self._category = feed_entry.category
        self._publication_date = feed_entry.publication_date
        self._location = feed_entry.location
        self._council_area = feed_entry.council_area
        self._status = feed_entry.status
        self._type = feed_entry.type
        self._fire = feed_entry.fire
        self._size = feed_entry.size
        self._responsible_agency = feed_entry.responsible_agency

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        if self._fire:
            return "mdi:fire"
        return "mdi:alarm-light"

    @property
    def source(self) -> str:
        """Return source value of this external event."""
        return SOURCE

    @property
    def name(self) -> Optional[str]:
        """Return the name of the entity."""
        return self._name

    @property
    def distance(self) -> Optional[float]:
        """Return distance value of this external event."""
        return self._distance

    @property
    def latitude(self) -> Optional[float]:
        """Return latitude value of this external event."""
        return self._latitude

    @property
    def longitude(self) -> Optional[float]:
        """Return longitude value of this external event."""
        return self._longitude

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return LENGTH_KILOMETERS

    @property
    def device_state_attributes(self):
        """Return the device state attributes."""
        attributes = {}
        for key, value in (
            (ATTR_EXTERNAL_ID, self._external_id),
            (ATTR_CATEGORY, self._category),
            (ATTR_LOCATION, self._location),
            (ATTR_ATTRIBUTION, self._attribution),
            (ATTR_PUBLICATION_DATE, self._publication_date),
            (ATTR_COUNCIL_AREA, self._council_area),
            (ATTR_STATUS, self._status),
            (ATTR_TYPE, self._type),
            (ATTR_FIRE, self._fire),
            (ATTR_SIZE, self._size),
            (ATTR_RESPONSIBLE_AGENCY, self._responsible_agency),
        ):
            if value or isinstance(value, bool):
                attributes[key] = value
        return attributes
