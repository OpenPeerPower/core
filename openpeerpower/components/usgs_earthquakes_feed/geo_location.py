"""Support for U.S. Geological Survey Earthquake Hazards Program Feeds."""
from __future__ import annotations

from datetime import timedelta
import logging

from geojson_client.usgs_earthquake_hazards_program_feed import (
    UsgsEarthquakeHazardsProgramFeedManager,
)
import voluptuous as vol

from openpeerpower.components.geo_location import PLATFORM_SCHEMA, GeolocationEvent
from openpeerpower.const import (
    ATTR_ATTRIBUTION,
    ATTR_TIME,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_RADIUS,
    CONF_SCAN_INTERVAL,
    EVENT_OPENPEERPOWER_START,
    LENGTH_KILOMETERS,
)
from openpeerpower.core import callback
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.dispatcher import async_dispatcher_connect, dispatcher_send
from openpeerpower.helpers.event import track_time_interval

_LOGGER = logging.getLogger(__name__)

ATTR_ALERT = "alert"
ATTR_EXTERNAL_ID = "external_id"
ATTR_MAGNITUDE = "magnitude"
ATTR_PLACE = "place"
ATTR_STATUS = "status"
ATTR_TYPE = "type"
ATTR_UPDATED = "updated"

CONF_FEED_TYPE = "feed_type"
CONF_MINIMUM_MAGNITUDE = "minimum_magnitude"

DEFAULT_MINIMUM_MAGNITUDE = 0.0
DEFAULT_RADIUS_IN_KM = 50.0
DEFAULT_UNIT_OF_MEASUREMENT = LENGTH_KILOMETERS

SCAN_INTERVAL = timedelta(minutes=5)

SIGNAL_DELETE_ENTITY = "usgs_earthquakes_feed_delete_{}"
SIGNAL_UPDATE_ENTITY = "usgs_earthquakes_feed_update_{}"

SOURCE = "usgs_earthquakes_feed"

VALID_FEED_TYPES = [
    "past_hour_significant_earthquakes",
    "past_hour_m45_earthquakes",
    "past_hour_m25_earthquakes",
    "past_hour_m10_earthquakes",
    "past_hour_all_earthquakes",
    "past_day_significant_earthquakes",
    "past_day_m45_earthquakes",
    "past_day_m25_earthquakes",
    "past_day_m10_earthquakes",
    "past_day_all_earthquakes",
    "past_week_significant_earthquakes",
    "past_week_m45_earthquakes",
    "past_week_m25_earthquakes",
    "past_week_m10_earthquakes",
    "past_week_all_earthquakes",
    "past_month_significant_earthquakes",
    "past_month_m45_earthquakes",
    "past_month_m25_earthquakes",
    "past_month_m10_earthquakes",
    "past_month_all_earthquakes",
]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_FEED_TYPE): vol.In(VALID_FEED_TYPES),
        vol.Optional(CONF_LATITUDE): cv.latitude,
        vol.Optional(CONF_LONGITUDE): cv.longitude,
        vol.Optional(CONF_RADIUS, default=DEFAULT_RADIUS_IN_KM): vol.Coerce(float),
        vol.Optional(
            CONF_MINIMUM_MAGNITUDE, default=DEFAULT_MINIMUM_MAGNITUDE
        ): cv.positive_float,
    }
)


def setup_platform(opp, config, add_entities, discovery_info=None):
    """Set up the USGS Earthquake Hazards Program Feed platform."""
    scan_interval = config.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL)
    feed_type = config[CONF_FEED_TYPE]
    coordinates = (
        config.get(CONF_LATITUDE, opp.config.latitude),
        config.get(CONF_LONGITUDE, opp.config.longitude),
    )
    radius_in_km = config[CONF_RADIUS]
    minimum_magnitude = config[CONF_MINIMUM_MAGNITUDE]
    # Initialize the entity manager.
    feed = UsgsEarthquakesFeedEntityManager(
        opp,
        add_entities,
        scan_interval,
        coordinates,
        feed_type,
        radius_in_km,
        minimum_magnitude,
    )

    def start_feed_manager(event):
        """Start feed manager."""
        feed.startup()

    opp.bus.listen_once(EVENT_OPENPEERPOWER_START, start_feed_manager)


class UsgsEarthquakesFeedEntityManager:
    """Feed Entity Manager for USGS Earthquake Hazards Program feed."""

    def __init__(
        self,
        opp,
        add_entities,
        scan_interval,
        coordinates,
        feed_type,
        radius_in_km,
        minimum_magnitude,
    ):
        """Initialize the Feed Entity Manager."""

        self._opp = opp
        self._feed_manager = UsgsEarthquakeHazardsProgramFeedManager(
            self._generate_entity,
            self._update_entity,
            self._remove_entity,
            coordinates,
            feed_type,
            filter_radius=radius_in_km,
            filter_minimum_magnitude=minimum_magnitude,
        )
        self._add_entities = add_entities
        self._scan_interval = scan_interval

    def startup(self):
        """Start up this manager."""
        self._feed_manager.update()
        self._init_regular_updates()

    def _init_regular_updates(self):
        """Schedule regular updates at the specified interval."""
        track_time_interval(
            self._opp, lambda now: self._feed_manager.update(), self._scan_interval
        )

    def get_entry(self, external_id):
        """Get feed entry by external id."""
        return self._feed_manager.feed_entries.get(external_id)

    def _generate_entity(self, external_id):
        """Generate new entity."""
        new_entity = UsgsEarthquakesEvent(self, external_id)
        # Add new entities to HA.
        self._add_entities([new_entity], True)

    def _update_entity(self, external_id):
        """Update entity."""
        dispatcher_send(self._opp, SIGNAL_UPDATE_ENTITY.format(external_id))

    def _remove_entity(self, external_id):
        """Remove entity."""
        dispatcher_send(self._opp, SIGNAL_DELETE_ENTITY.format(external_id))


class UsgsEarthquakesEvent(GeolocationEvent):
    """This represents an external event with USGS Earthquake data."""

    def __init__(self, feed_manager, external_id):
        """Initialize entity with data from feed entry."""
        self._feed_manager = feed_manager
        self._external_id = external_id
        self._name = None
        self._distance = None
        self._latitude = None
        self._longitude = None
        self._attribution = None
        self._place = None
        self._magnitude = None
        self._time = None
        self._updated = None
        self._status = None
        self._type = None
        self._alert = None
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

    @callback
    def _delete_callback(self):
        """Remove this entity."""
        self._remove_signal_delete()
        self._remove_signal_update()
        self.opp.async_create_task(self.async_remove(force_remove=True))

    @callback
    def _update_callback(self):
        """Call update method."""
        self.async_schedule_update_op_state(True)

    @property
    def should_poll(self):
        """No polling needed for USGS Earthquake events."""
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
        self._place = feed_entry.place
        self._magnitude = feed_entry.magnitude
        self._time = feed_entry.time
        self._updated = feed_entry.updated
        self._status = feed_entry.status
        self._type = feed_entry.type
        self._alert = feed_entry.alert

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return "mdi:pulse"

    @property
    def source(self) -> str:
        """Return source value of this external event."""
        return SOURCE

    @property
    def name(self) -> str | None:
        """Return the name of the entity."""
        return self._name

    @property
    def distance(self) -> float | None:
        """Return distance value of this external event."""
        return self._distance

    @property
    def latitude(self) -> float | None:
        """Return latitude value of this external event."""
        return self._latitude

    @property
    def longitude(self) -> float | None:
        """Return longitude value of this external event."""
        return self._longitude

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return DEFAULT_UNIT_OF_MEASUREMENT

    @property
    def extra_state_attributes(self):
        """Return the device state attributes."""
        attributes = {}
        for key, value in (
            (ATTR_EXTERNAL_ID, self._external_id),
            (ATTR_PLACE, self._place),
            (ATTR_MAGNITUDE, self._magnitude),
            (ATTR_TIME, self._time),
            (ATTR_UPDATED, self._updated),
            (ATTR_STATUS, self._status),
            (ATTR_TYPE, self._type),
            (ATTR_ALERT, self._alert),
            (ATTR_ATTRIBUTION, self._attribution),
        ):
            if value or isinstance(value, bool):
                attributes[key] = value
        return attributes
