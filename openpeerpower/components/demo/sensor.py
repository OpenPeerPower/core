"""Demo platform that has a couple of fake sensors."""
from openpeerpower.components.sensor import STATE_CLASS_MEASUREMENT, SensorEntity
from openpeerpower.const import (
    ATTR_BATTERY_LEVEL,
    CONCENTRATION_PARTS_PER_MILLION,
    DEVICE_CLASS_CO,
    DEVICE_CLASS_CO2,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_TEMPERATURE,
    PERCENTAGE,
    TEMP_CELSIUS,
)

from . import DOMAIN


async def async_setup_platform(opp, config, async_add_entities, discovery_info=None):
    """Set up the Demo sensors."""
    async_add_entities(
        [
            DemoSensor(
                "sensor_1",
                "Outside Temperature",
                15.6,
                DEVICE_CLASS_TEMPERATURE,
                STATE_CLASS_MEASUREMENT,
                TEMP_CELSIUS,
                12,
            ),
            DemoSensor(
                "sensor_2",
                "Outside Humidity",
                54,
                DEVICE_CLASS_HUMIDITY,
                STATE_CLASS_MEASUREMENT,
                PERCENTAGE,
                None,
            ),
            DemoSensor(
                "sensor_3",
                "Carbon monoxide",
                54,
                DEVICE_CLASS_CO,
                STATE_CLASS_MEASUREMENT,
                CONCENTRATION_PARTS_PER_MILLION,
                None,
            ),
            DemoSensor(
                "sensor_4",
                "Carbon dioxide",
                54,
                DEVICE_CLASS_CO2,
                STATE_CLASS_MEASUREMENT,
                CONCENTRATION_PARTS_PER_MILLION,
                14,
            ),
        ]
    )


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up the Demo config entry."""
    await async_setup_platform(opp, {}, async_add_entities)


class DemoSensor(SensorEntity):
    """Representation of a Demo sensor."""

    def __init__(
        self,
        unique_id,
        name,
        state,
        device_class,
        state_class,
        unit_of_measurement,
        battery,
    ):
        """Initialize the sensor."""
        self._battery = battery
        self._device_class = device_class
        self._name = name
        self._state = state
        self._state_class = state_class
        self._unique_id = unique_id
        self._unit_of_measurement = unit_of_measurement

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.unique_id)
            },
            "name": self.name,
        }

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._unique_id

    @property
    def should_poll(self):
        """No polling needed for a demo sensor."""
        return False

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._device_class

    @property
    def state_class(self):
        """Return the state class of the sensor."""
        return self._state_class

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        return self._unit_of_measurement

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if self._battery:
            return {ATTR_BATTERY_LEVEL: self._battery}
