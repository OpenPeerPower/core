"""Support for Somfy Thermostat Battery."""

from pymfy.api.devices.category import Category
from pymfy.api.devices.thermostat import Thermostat

from openpeerpower.components.sensor import SensorEntity
from openpeerpower.const import DEVICE_CLASS_BATTERY, PERCENTAGE

from . import SomfyEntity
from .const import API, COORDINATOR, DOMAIN

SUPPORTED_CATEGORIES = {Category.HVAC.value}


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up the Somfy sensor platform."""
    domain_data = opp.data[DOMAIN]
    coordinator = domain_data[COORDINATOR]
    api = domain_data[API]

    sensors = [
        SomfyThermostatBatterySensor(coordinator, device_id, api)
        for device_id, device in coordinator.data.items()
        if SUPPORTED_CATEGORIES & set(device.categories)
    ]

    async_add_entities(sensors)


class SomfyThermostatBatterySensor(SomfyEntity, SensorEntity):
    """Representation of a Somfy thermostat battery."""

    _attr_device_class = DEVICE_CLASS_BATTERY
    _attr_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, device_id, api):
        """Initialize the Somfy device."""
        super().__init__(coordinator, device_id, api)
        self._climate = None
        self._create_device()

    def _create_device(self):
        """Update the device with the latest data."""
        self._climate = Thermostat(self.device, self.api)

    @property
    def state(self) -> int:
        """Return the state of the sensor."""
        return self._climate.get_battery()
