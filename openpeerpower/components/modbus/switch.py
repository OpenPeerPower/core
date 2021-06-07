"""Support for Modbus switches."""
from __future__ import annotations

import logging

from openpeerpower.components.switch import SwitchEntity
from openpeerpower.const import CONF_NAME, CONF_SWITCHES
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.typing import ConfigType

from .base_platform import BaseSwitch
from .const import MODBUS_DOMAIN
from .modbus import ModbusHub

PARALLEL_UPDATES = 1
_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    opp: OpenPeerPower, config: ConfigType, async_add_entities, discovery_info=None
):
    """Read configuration and create Modbus switches."""
    switches = []

    if discovery_info is None:  # pragma: no cover
        return

    for entry in discovery_info[CONF_SWITCHES]:
        hub: ModbusHub = opp.data[MODBUS_DOMAIN][discovery_info[CONF_NAME]]
        switches.append(ModbusSwitch(hub, entry))
    async_add_entities(switches)


class ModbusSwitch(BaseSwitch, SwitchEntity):
    """Base class representing a Modbus switch."""

    async def async_turn_on(self, **kwargs):
        """Set switch on."""
        await self.async_turn(self.command_on)
