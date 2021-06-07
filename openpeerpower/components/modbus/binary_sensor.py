"""Support for Modbus Coil and Discrete Input sensors."""
from __future__ import annotations

import logging

from openpeerpower.components.binary_sensor import BinarySensorEntity
from openpeerpower.const import CONF_BINARY_SENSORS, CONF_NAME, STATE_ON
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.restore_state import RestoreEntity
from openpeerpower.helpers.typing import ConfigType, DiscoveryInfoType

from .base_platform import BasePlatform
from .const import MODBUS_DOMAIN

PARALLEL_UPDATES = 1
_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    opp: OpenPeerPower,
    config: ConfigType,
    async_add_entities,
    discovery_info: DiscoveryInfoType | None = None,
):
    """Set up the Modbus binary sensors."""
    sensors = []

    if discovery_info is None:  # pragma: no cover
        return

    for entry in discovery_info[CONF_BINARY_SENSORS]:
        hub = opp.data[MODBUS_DOMAIN][discovery_info[CONF_NAME]]
        sensors.append(ModbusBinarySensor(hub, entry))

    async_add_entities(sensors)


class ModbusBinarySensor(BasePlatform, RestoreEntity, BinarySensorEntity):
    """Modbus binary sensor."""

    async def async_added_to_opp(self):
        """Handle entity which will be added."""
        await self.async_base_added_to_opp()
        state = await self.async_get_last_state()
        if state:
            self._value = state.state == STATE_ON
        else:
            self._value = None

    @property
    def is_on(self):
        """Return the state of the sensor."""
        return self._value

    async def async_update(self, now=None):
        """Update the state of the sensor."""
        result = await self._hub.async_pymodbus_call(
            self._slave, self._address, 1, self._input_type
        )
        if result is None:
            self._available = False
            self.async_write_op_state()
            return

        self._value = result.bits[0] & 1
        self._available = True
        self.async_write_op_state()
