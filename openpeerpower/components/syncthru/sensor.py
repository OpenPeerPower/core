"""Support for Samsung Printers with SyncThru web interface."""

import logging

from pysyncthru import SYNCTHRU_STATE_HUMAN, SyncThru
import voluptuous as vol

from openpeerpower.components.sensor import PLATFORM_SCHEMA
from openpeerpower.config_entries import SOURCE_IMPORT
from openpeerpower.const import CONF_NAME, CONF_RESOURCE, CONF_URL, PERCENTAGE
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.entity import Entity

from . import device_identifiers
from .const import DEFAULT_MODEL, DEFAULT_NAME_TEMPLATE, DOMAIN

_LOGGER = logging.getLogger(__name__)

COLORS = ["black", "cyan", "magenta", "yellow"]
DRUM_COLORS = COLORS
TONER_COLORS = COLORS
TRAYS = range(1, 6)
OUTPUT_TRAYS = range(0, 6)
DEFAULT_MONITORED_CONDITIONS = []
DEFAULT_MONITORED_CONDITIONS.extend([f"toner_{key}" for key in TONER_COLORS])
DEFAULT_MONITORED_CONDITIONS.extend([f"drum_{key}" for key in DRUM_COLORS])
DEFAULT_MONITORED_CONDITIONS.extend([f"tray_{key}" for key in TRAYS])
DEFAULT_MONITORED_CONDITIONS.extend([f"output_tray_{key}" for key in OUTPUT_TRAYS])

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_RESOURCE): cv.url,
        vol.Optional(
            CONF_NAME, default=DEFAULT_NAME_TEMPLATE.format(DEFAULT_MODEL)
        ): cv.string,
    }
)


async def async_setup_platform(opp, config, async_add_entities, discovery_info=None):
    """Set up the SyncThru component."""
    _LOGGER.warning(
        "Loading syncthru via platform config is deprecated and no longer "
        "necessary as of 0.113. Please remove it from your configuration YAML."
    )
    opp.async_create_task(
        opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data={
                CONF_URL: config.get(CONF_RESOURCE),
                CONF_NAME: config.get(CONF_NAME),
            },
        )
    )
    return True


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up from config entry."""

    printer = opp.data[DOMAIN][config_entry.entry_id]

    supp_toner = printer.toner_status(filter_supported=True)
    supp_drum = printer.drum_status(filter_supported=True)
    supp_tray = printer.input_tray_status(filter_supported=True)
    supp_output_tray = printer.output_tray_status()

    name = config_entry.data[CONF_NAME]
    devices = [SyncThruMainSensor(printer, name)]

    for key in supp_toner:
        devices.append(SyncThruTonerSensor(printer, name, key))
    for key in supp_drum:
        devices.append(SyncThruDrumSensor(printer, name, key))
    for key in supp_tray:
        devices.append(SyncThruInputTraySensor(printer, name, key))
    for key in supp_output_tray:
        devices.append(SyncThruOutputTraySensor(printer, name, key))

    async_add_entities(devices, True)


class SyncThruSensor(Entity):
    """Implementation of an abstract Samsung Printer sensor platform."""

    def __init__(self, syncthru, name):
        """Initialize the sensor."""
        self.syncthru: SyncThru = syncthru
        self._attributes = {}
        self._state = None
        self._name = name
        self._icon = "mdi:printer"
        self._unit_of_measurement = None
        self._id_suffix = ""

    @property
    def unique_id(self):
        """Return unique ID for the sensor."""
        serial = self.syncthru.serial_number()
        return serial + self._id_suffix if serial else super().unique_id

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def icon(self):
        """Return the icon of the device."""
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the unit of measuremnt."""
        return self._unit_of_measurement

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        return self._attributes

    @property
    def device_info(self):
        """Return device information."""
        return {"identifiers": device_identifiers(self.syncthru)}


class SyncThruMainSensor(SyncThruSensor):
    """Implementation of the main sensor, conducting the actual polling."""

    def __init__(self, syncthru, name):
        """Initialize the sensor."""
        super().__init__(syncthru, name)
        self._id_suffix = "_main"
        self._active = True

    async def async_update(self):
        """Get the latest data from SyncThru and update the state."""
        if not self._active:
            return
        try:
            await self.syncthru.update()
        except ValueError:
            # if an exception is thrown, printer does not support syncthru
            _LOGGER.warning(
                "Configured printer at %s does not support SyncThru. "
                "Consider changing your configuration",
                self.syncthru.url,
            )
            self._active = False
        self._state = SYNCTHRU_STATE_HUMAN[self.syncthru.device_status()]
        self._attributes = {"display_text": self.syncthru.device_status_details()}


class SyncThruTonerSensor(SyncThruSensor):
    """Implementation of a Samsung Printer toner sensor platform."""

    def __init__(self, syncthru, name, color):
        """Initialize the sensor."""
        super().__init__(syncthru, name)
        self._name = f"{name} Toner {color}"
        self._color = color
        self._unit_of_measurement = PERCENTAGE
        self._id_suffix = f"_toner_{color}"

    def update(self):
        """Get the latest data from SyncThru and update the state."""
        # Data fetching is taken care of through the Main sensor

        if self.syncthru.is_online():
            self._attributes = self.syncthru.toner_status().get(self._color, {})
            self._state = self._attributes.get("remaining")


class SyncThruDrumSensor(SyncThruSensor):
    """Implementation of a Samsung Printer toner sensor platform."""

    def __init__(self, syncthru, name, color):
        """Initialize the sensor."""
        super().__init__(syncthru, name)
        self._name = f"{name} Drum {color}"
        self._color = color
        self._unit_of_measurement = PERCENTAGE
        self._id_suffix = f"_drum_{color}"

    def update(self):
        """Get the latest data from SyncThru and update the state."""
        # Data fetching is taken care of through the Main sensor

        if self.syncthru.is_online():
            self._attributes = self.syncthru.drum_status().get(self._color, {})
            self._state = self._attributes.get("remaining")


class SyncThruInputTraySensor(SyncThruSensor):
    """Implementation of a Samsung Printer input tray sensor platform."""

    def __init__(self, syncthru, name, number):
        """Initialize the sensor."""
        super().__init__(syncthru, name)
        self._name = f"{name} Tray {number}"
        self._number = number
        self._id_suffix = f"_tray_{number}"

    def update(self):
        """Get the latest data from SyncThru and update the state."""
        # Data fetching is taken care of through the Main sensor

        if self.syncthru.is_online():
            self._attributes = self.syncthru.input_tray_status().get(self._number, {})
            self._state = self._attributes.get("newError")
            if self._state == "":
                self._state = "Ready"


class SyncThruOutputTraySensor(SyncThruSensor):
    """Implementation of a Samsung Printer input tray sensor platform."""

    def __init__(self, syncthru, name, number):
        """Initialize the sensor."""
        super().__init__(syncthru, name)
        self._name = f"{name} Output Tray {number}"
        self._number = number
        self._id_suffix = f"_output_tray_{number}"

    def update(self):
        """Get the latest data from SyncThru and update the state."""
        # Data fetching is taken care of through the Main sensor

        if self.syncthru.is_online():
            self._attributes = self.syncthru.output_tray_status().get(self._number, {})
            self._state = self._attributes.get("status")
            if self._state == "":
                self._state = "Ready"
