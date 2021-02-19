"""Support for fans through the SmartThings cloud API."""
import math
from typing import Optional, Sequence

from pysmartthings import Capability

from openpeerpower.components.fan import SUPPORT_SET_SPEED, FanEntity
from openpeerpower.util.percentage import (
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from . import SmartThingsEntity
from .const import DATA_BROKERS, DOMAIN

SPEED_RANGE = (1, 3)  # off is not included


async def async_setup_entry.opp, config_entry, async_add_entities):
    """Add fans for a config entry."""
    broker =.opp.data[DOMAIN][DATA_BROKERS][config_entry.entry_id]
    async_add_entities(
        [
            SmartThingsFan(device)
            for device in broker.devices.values()
            if broker.any_assigned(device.device_id, "fan")
        ]
    )


def get_capabilities(capabilities: Sequence[str]) -> Optional[Sequence[str]]:
    """Return all capabilities supported if minimum required are present."""
    supported = [Capability.switch, Capability.fan_speed]
    # Must have switch and fan_speed
    if all(capability in capabilities for capability in supported):
        return supported


class SmartThingsFan(SmartThingsEntity, FanEntity):
    """Define a SmartThings Fan."""

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        if percentage is None:
            await self._device.switch_on(set_status=True)
        elif percentage == 0:
            await self._device.switch_off(set_status=True)
        else:
            value = math.ceil(percentage_to_ranged_value(SPEED_RANGE, percentage))
            await self._device.set_fan_speed(value, set_status=True)
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_op.state()

    async def async_turn_on(
        self,
        speed: str = None,
        percentage: int = None,
        preset_mode: str = None,
        **kwargs,
    ) -> None:
        """Turn the fan on."""
        await self.async_set_percentage(percentage)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the fan off."""
        await self._device.switch_off(set_status=True)
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_op.state()

    @property
    def is_on(self) -> bool:
        """Return true if fan is on."""
        return self._device.status.switch

    @property
    def percentage(self) -> str:
        """Return the current speed percentage."""
        return ranged_value_to_percentage(SPEED_RANGE, self._device.status.fan_speed)

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return SUPPORT_SET_SPEED
