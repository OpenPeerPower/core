"""Support for MySensors binary sensors."""
from typing import Callable

from openpeerpower.components import mysensors
from openpeerpower.components.binary_sensor import (
    DEVICE_CLASS_MOISTURE,
    DEVICE_CLASS_MOTION,
    DEVICE_CLASS_SAFETY,
    DEVICE_CLASS_SOUND,
    DEVICE_CLASS_VIBRATION,
    DEVICE_CLASSES,
    DOMAIN,
    BinarySensorEntity,
)
from openpeerpower.components.mysensors import on_unload
from openpeerpower.components.mysensors.const import MYSENSORS_DISCOVERY
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import STATE_ON
from openpeerpower.core import callback
from openpeerpower.helpers.dispatcher import async_dispatcher_connect
from openpeerpower.helpers.typing import OpenPeerPowerType

SENSORS = {
    "S_DOOR": "door",
    "S_MOTION": DEVICE_CLASS_MOTION,
    "S_SMOKE": "smoke",
    "S_SPRINKLER": DEVICE_CLASS_SAFETY,
    "S_WATER_LEAK": DEVICE_CLASS_SAFETY,
    "S_SOUND": DEVICE_CLASS_SOUND,
    "S_VIBRATION": DEVICE_CLASS_VIBRATION,
    "S_MOISTURE": DEVICE_CLASS_MOISTURE,
}


async def async_setup_entry(
    opp: OpenPeerPowerType, config_entry: ConfigEntry, async_add_entities: Callable
):
    """Set up this platform for a specific ConfigEntry(==Gateway)."""

    @callback
    def async_discover(discovery_info):
        """Discover and add a MySensors binary_sensor."""
        mysensors.setup_mysensors_platform(
            opp,
            DOMAIN,
            discovery_info,
            MySensorsBinarySensor,
            async_add_entities=async_add_entities,
        )

    await on_unload(
        opp,
        config_entry,
        async_dispatcher_connect(
            opp,
            MYSENSORS_DISCOVERY.format(config_entry.entry_id, DOMAIN),
            async_discover,
        ),
    )


class MySensorsBinarySensor(mysensors.device.MySensorsEntity, BinarySensorEntity):
    """Representation of a MySensors Binary Sensor child node."""

    @property
    def is_on(self):
        """Return True if the binary sensor is on."""
        return self._values.get(self.value_type) == STATE_ON

    @property
    def device_class(self):
        """Return the class of this sensor, from DEVICE_CLASSES."""
        pres = self.gateway.const.Presentation
        device_class = SENSORS.get(pres(self.child_type).name)
        if device_class in DEVICE_CLASSES:
            return device_class
        return None
