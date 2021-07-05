"""Support for Modbus fans."""
from __future__ import annotations

import logging

from openpeerpower.components.fan import FanEntity
from openpeerpower.const import CONF_NAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.typing import ConfigType

from .base_platform import BaseSwitch
from .const import CONF_FANS, MODBUS_DOMAIN
from .modbus import ModbusHub

PARALLEL_UPDATES = 1
_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    opp: OpenPeerPower, config: ConfigType, async_add_entities, discovery_info=None
):
    """Read configuration and create Modbus fans."""
    if discovery_info is None:
        return
    fans = []

    for entry in discovery_info[CONF_FANS]:
        hub: ModbusHub = opp.data[MODBUS_DOMAIN][discovery_info[CONF_NAME]]
        fans.append(ModbusFan(hub, entry))
    async_add_entities(fans)


class ModbusFan(BaseSwitch, FanEntity):
    """Class representing a Modbus fan."""

    async def async_turn_on(
        self,
        speed: str | None = None,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs,
    ) -> None:
        """Set fan on."""
        await self.async_turn(self.command_on)
