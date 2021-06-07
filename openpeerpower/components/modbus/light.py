"""Support for Modbus lights."""
from __future__ import annotations

import logging

from openpeerpower.components.light import LightEntity
from openpeerpower.const import CONF_LIGHTS, CONF_NAME
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
    """Read configuration and create Modbus lights."""
    if discovery_info is None:  # pragma: no cover
        return

    lights = []
    for entry in discovery_info[CONF_LIGHTS]:
        hub: ModbusHub = opp.data[MODBUS_DOMAIN][discovery_info[CONF_NAME]]
        lights.append(ModbusLight(hub, entry))
    async_add_entities(lights)


class ModbusLight(BaseSwitch, LightEntity):
    """Class representing a Modbus light."""

    async def async_turn_on(self, **kwargs):
        """Set light on."""
        await self.async_turn(self.command_on)
