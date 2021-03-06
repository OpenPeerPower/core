"""Interfaces with Egardia/Woonveilig alarm control panel."""
from openpeerpower.components.binary_sensor import (
    DEVICE_CLASS_MOTION,
    DEVICE_CLASS_OPENING,
    BinarySensorEntity,
)
from openpeerpower.const import STATE_OFF, STATE_ON

from . import ATTR_DISCOVER_DEVICES, EGARDIA_DEVICE

EGARDIA_TYPE_TO_DEVICE_CLASS = {
    "IR Sensor": DEVICE_CLASS_MOTION,
    "Door Contact": DEVICE_CLASS_OPENING,
    "IR": DEVICE_CLASS_MOTION,
}


async def async_setup_platform(opp, config, async_add_entities, discovery_info=None):
    """Initialize the platform."""
    if discovery_info is None or discovery_info[ATTR_DISCOVER_DEVICES] is None:
        return

    disc_info = discovery_info[ATTR_DISCOVER_DEVICES]

    async_add_entities(
        (
            EgardiaBinarySensor(
                sensor_id=disc_info[sensor]["id"],
                name=disc_info[sensor]["name"],
                egardia_system=opp.data[EGARDIA_DEVICE],
                device_class=EGARDIA_TYPE_TO_DEVICE_CLASS.get(
                    disc_info[sensor]["type"], None
                ),
            )
            for sensor in disc_info
        ),
        True,
    )


class EgardiaBinarySensor(BinarySensorEntity):
    """Represents a sensor based on an Egardia sensor (IR, Door Contact)."""

    def __init__(self, sensor_id, name, egardia_system, device_class):
        """Initialize the sensor device."""
        self._id = sensor_id
        self._name = name
        self._state = None
        self._device_class = device_class
        self._egardia_system = egardia_system

    def update(self):
        """Update the status."""
        egardia_input = self._egardia_system.getsensorstate(self._id)
        self._state = STATE_ON if egardia_input else STATE_OFF

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def is_on(self):
        """Whether the device is switched on."""
        return self._state == STATE_ON

    @property
    def device_class(self):
        """Return the device class."""
        return self._device_class
