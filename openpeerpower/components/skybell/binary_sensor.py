"""Binary sensor support for the Skybell HD Doorbell."""
from datetime import timedelta

import voluptuous as vol

from openpeerpower.components.binary_sensor import (
    DEVICE_CLASS_MOTION,
    DEVICE_CLASS_OCCUPANCY,
    PLATFORM_SCHEMA,
    BinarySensorEntity,
)
from openpeerpower.const import CONF_ENTITY_NAMESPACE, CONF_MONITORED_CONDITIONS
import openpeerpower.helpers.config_validation as cv

from . import DEFAULT_ENTITY_NAMESPACE, DOMAIN as SKYBELL_DOMAIN, SkybellDevice

SCAN_INTERVAL = timedelta(seconds=10)

# Sensor types: Name, device_class, event
SENSOR_TYPES = {
    "button": ["Button", DEVICE_CLASS_OCCUPANCY, "device:sensor:button"],
    "motion": ["Motion", DEVICE_CLASS_MOTION, "device:sensor:motion"],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(
            CONF_ENTITY_NAMESPACE, default=DEFAULT_ENTITY_NAMESPACE
        ): cv.string,
        vol.Required(CONF_MONITORED_CONDITIONS, default=[]): vol.All(
            cv.ensure_list, [vol.In(SENSOR_TYPES)]
        ),
    }
)


def setup_platform(opp, config, add_entities, discovery_info=None):
    """Set up the platform for a Skybell device."""
    skybell = opp.data.get(SKYBELL_DOMAIN)

    sensors = []
    for sensor_type in config.get(CONF_MONITORED_CONDITIONS):
        for device in skybell.get_devices():
            sensors.append(SkybellBinarySensor(device, sensor_type))

    add_entities(sensors, True)


class SkybellBinarySensor(SkybellDevice, BinarySensorEntity):
    """A binary sensor implementation for Skybell devices."""

    def __init__(self, device, sensor_type):
        """Initialize a binary sensor for a Skybell device."""
        super().__init__(device)
        self._sensor_type = sensor_type
        self._name = "{} {}".format(
            self._device.name, SENSOR_TYPES[self._sensor_type][0]
        )
        self._device_class = SENSOR_TYPES[self._sensor_type][1]
        self._event = {}
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return True if the binary sensor is on."""
        return self._state

    @property
    def device_class(self):
        """Return the class of the binary sensor."""
        return self._device_class

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        attrs = super().device_state_attributes

        attrs["event_date"] = self._event.get("createdAt")

        return attrs

    def update(self):
        """Get the latest data and updates the state."""
        super().update()

        event = self._device.latest(SENSOR_TYPES[self._sensor_type][2])

        self._state = bool(event and event.get("id") != self._event.get("id"))

        self._event = event or {}
