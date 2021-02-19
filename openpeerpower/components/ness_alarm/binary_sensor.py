"""Support for Ness D8X/D16X zone states - represented as binary sensors."""
from openpeerpower.components.binary_sensor import BinarySensorEntity
from openpeerpower.core import callback
from openpeerpower.helpers.dispatcher import async_dispatcher_connect

from . import (
    CONF_ZONE_ID,
    CONF_ZONE_NAME,
    CONF_ZONE_TYPE,
    CONF_ZONES,
    SIGNAL_ZONE_CHANGED,
    ZoneChangedData,
)


async def async_setup_platform.opp, config, async_add_entities, discovery_info=None):
    """Set up the Ness Alarm binary sensor devices."""
    if not discovery_info:
        return

    configured_zones = discovery_info[CONF_ZONES]

    devices = []

    for zone_config in configured_zones:
        zone_type = zone_config[CONF_ZONE_TYPE]
        zone_name = zone_config[CONF_ZONE_NAME]
        zone_id = zone_config[CONF_ZONE_ID]
        device = NessZoneBinarySensor(
            zone_id=zone_id, name=zone_name, zone_type=zone_type
        )
        devices.append(device)

    async_add_entities(devices)


class NessZoneBinarySensor(BinarySensorEntity):
    """Representation of an Ness alarm zone as a binary sensor."""

    def __init__(self, zone_id, name, zone_type):
        """Initialize the binary_sensor."""
        self._zone_id = zone_id
        self._name = name
        self._type = zone_type
        self._state = 0

    async def async_added_to_opp(self):
        """Register callbacks."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.opp, SIGNAL_ZONE_CHANGED, self._op.dle_zone_change
            )
        )

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def is_on(self):
        """Return true if sensor is on."""
        return self._state == 1

    @property
    def device_class(self):
        """Return the class of this sensor, from DEVICE_CLASSES."""
        return self._type

    @callback
    def _op.dle_zone_change(self, data: ZoneChangedData):
        """Handle zone state update."""
        if self._zone_id == data.zone_id:
            self._state = data.state
            self.async_write_op.state()
