"""Sensor for checking the status of London Underground tube lines."""
from datetime import timedelta

from london_tube_status import TubeData
import voluptuous as vol

from openpeerpower.components.sensor import PLATFORM_SCHEMA
from openpeerpower.const import ATTR_ATTRIBUTION
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.entity import Entity

ATTRIBUTION = "Powered by TfL Open Data"

CONF_LINE = "line"

ICON = "mdi:subway"

SCAN_INTERVAL = timedelta(seconds=30)

TUBE_LINES = [
    "Bakerloo",
    "Central",
    "Circle",
    "District",
    "DLR",
    "Hammersmith & City",
    "Jubilee",
    "London Overground",
    "Metropolitan",
    "Northern",
    "Piccadilly",
    "TfL Rail",
    "Victoria",
    "Waterloo & City",
]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_LINE): vol.All(cv.ensure_list, [vol.In(list(TUBE_LINES))])}
)


def setup_platform(opp, config, add_entities, discovery_info=None):
    """Set up the Tube sensor."""

    data = TubeData()
    data.update()
    sensors = []
    for line in config.get(CONF_LINE):
        sensors.append(LondonTubeSensor(line, data))

    add_entities(sensors, True)


class LondonTubeSensor(Entity):
    """Sensor that reads the status of a line from Tube Data."""

    def __init__(self, name, data):
        """Initialize the London Underground sensor."""
        self._data = data
        self._description = None
        self._name = name
        self._state = None
        self.attrs = {ATTR_ATTRIBUTION: ATTRIBUTION}

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return ICON

    @property
    def device_state_attributes(self):
        """Return other details about the sensor state."""
        self.attrs["Description"] = self._description
        return self.attrs

    def update(self):
        """Update the sensor."""
        self._data.update()
        self._state = self._data.data[self.name]["State"]
        self._description = self._data.data[self.name]["Description"]
