"""Support for Epson Workforce Printer."""
from datetime import timedelta

from epsonprinter_pkg.epsonprinterapi import EpsonPrinterAPI
import voluptuous as vol

from openpeerpower.components.sensor import PLATFORM_SCHEMA
from openpeerpower.const import CONF_HOST, CONF_MONITORED_CONDITIONS, PERCENTAGE
from openpeerpower.exceptions import PlatformNotReady
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.entity import Entity

MONITORED_CONDITIONS = {
    "black": ["Ink level Black", PERCENTAGE, "mdi:water"],
    "photoblack": ["Ink level Photoblack", PERCENTAGE, "mdi:water"],
    "magenta": ["Ink level Magenta", PERCENTAGE, "mdi:water"],
    "cyan": ["Ink level Cyan", PERCENTAGE, "mdi:water"],
    "yellow": ["Ink level Yellow", PERCENTAGE, "mdi:water"],
    "clean": ["Cleaning level", PERCENTAGE, "mdi:water"],
}
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_MONITORED_CONDITIONS): vol.All(
            cv.ensure_list, [vol.In(MONITORED_CONDITIONS)]
        ),
    }
)
SCAN_INTERVAL = timedelta(minutes=60)


def setup_platform(opp, config, add_devices, discovery_info=None):
    """Set up the cartridge sensor."""
    host = config.get(CONF_HOST)

    api = EpsonPrinterAPI(host)
    if not api.available:
        raise PlatformNotReady()

    sensors = [
        EpsonPrinterCartridge(api, condition)
        for condition in config[CONF_MONITORED_CONDITIONS]
    ]

    add_devices(sensors, True)


class EpsonPrinterCartridge(Entity):
    """Representation of a cartridge sensor."""

    def __init__(self, api, cartridgeidx):
        """Initialize a cartridge sensor."""
        self._api = api

        self._id = cartridgeidx
        self._name = MONITORED_CONDITIONS[self._id][0]
        self._unit = MONITORED_CONDITIONS[self._id][1]
        self._icon = MONITORED_CONDITIONS[self._id][2]

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._unit

    @property
    def state(self):
        """Return the state of the device."""
        return self._api.getSensorValue(self._id)

    @property
    def available(self):
        """Could the device be accessed during the last update call."""
        return self._api.available

    def update(self):
        """Get the latest data from the Epson printer."""
        self._api.update()
