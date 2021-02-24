"""Sensor for Spot Crime."""

from collections import defaultdict
from datetime import timedelta

import spotcrime
import voluptuous as vol

from openpeerpower.components.sensor import PLATFORM_SCHEMA
from openpeerpower.const import (
    ATTR_ATTRIBUTION,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    CONF_API_KEY,
    CONF_EXCLUDE,
    CONF_INCLUDE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    CONF_RADIUS,
)
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.entity import Entity
from openpeerpower.util import slugify

CONF_DAYS = "days"
DEFAULT_DAYS = 1
NAME = "spotcrime"

EVENT_INCIDENT = f"{NAME}_incident"

SCAN_INTERVAL = timedelta(minutes=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_RADIUS): vol.Coerce(float),
        vol.Required(CONF_API_KEY): cv.string,
        vol.Inclusive(CONF_LATITUDE, "coordinates"): cv.latitude,
        vol.Inclusive(CONF_LONGITUDE, "coordinates"): cv.longitude,
        vol.Optional(CONF_DAYS, default=DEFAULT_DAYS): cv.positive_int,
        vol.Optional(CONF_INCLUDE): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_EXCLUDE): vol.All(cv.ensure_list, [cv.string]),
    }
)


def setup_platform(opp, config, add_entities, discovery_info=None):
    """Set up the Crime Reports platform."""
    latitude = config.get(CONF_LATITUDE, opp.config.latitude)
    longitude = config.get(CONF_LONGITUDE, opp.config.longitude)
    name = config[CONF_NAME]
    radius = config[CONF_RADIUS]
    api_key = config[CONF_API_KEY]
    days = config.get(CONF_DAYS)
    include = config.get(CONF_INCLUDE)
    exclude = config.get(CONF_EXCLUDE)

    add_entities(
        [
            SpotCrimeSensor(
                name, latitude, longitude, radius, include, exclude, api_key, days
            )
        ],
        True,
    )


class SpotCrimeSensor(Entity):
    """Representation of a Spot Crime Sensor."""

    def __init__(
        self, name, latitude, longitude, radius, include, exclude, api_key, days
    ):
        """Initialize the Spot Crime sensor."""

        self._name = name
        self._include = include
        self._exclude = exclude
        self.api_key = api_key
        self.days = days
        self._spotcrime = spotcrime.SpotCrime(
            (latitude, longitude),
            radius,
            self._include,
            self._exclude,
            self.api_key,
            self.days,
        )
        self._attributes = None
        self._state = None
        self._previous_incidents = set()
        self._attributes = {ATTR_ATTRIBUTION: spotcrime.ATTRIBUTION}

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    def _incident_event(self, incident):
        data = {
            "type": incident.get("type"),
            "timestamp": incident.get("timestamp"),
            "address": incident.get("location"),
        }
        if incident.get("coordinates"):
            data.update(
                {
                    ATTR_LATITUDE: incident.get("lat"),
                    ATTR_LONGITUDE: incident.get("lon"),
                }
            )
        self.opp.bus.fire(EVENT_INCIDENT, data)

    def update(self):
        """Update device state."""
        incident_counts = defaultdict(int)
        incidents = self._spotcrime.get_incidents()
        if len(incidents) < len(self._previous_incidents):
            self._previous_incidents = set()
        for incident in incidents:
            incident_type = slugify(incident.get("type"))
            incident_counts[incident_type] += 1
            if (
                self._previous_incidents
                and incident.get("id") not in self._previous_incidents
            ):
                self._incident_event(incident)
            self._previous_incidents.add(incident.get("id"))
        self._attributes.update(incident_counts)
        self._state = len(incidents)
