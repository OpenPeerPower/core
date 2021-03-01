"""Support for the Dynalite channels and presets as switches."""
from typing import Callable

from openpeerpower.components.switch import SwitchEntity
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower

from .dynalitebase import DynaliteBase, async_setup_entry_base


async def async_setup_entry(
    opp: OpenPeerPower, config_entry: ConfigEntry, async_add_entities: Callable
) -> None:
    """Record the async_add_entities function to add them later when received from Dynalite."""
    async_setup_entry_base(
        opp, config_entry, async_add_entities, "switch", DynaliteSwitch
    )


class DynaliteSwitch(DynaliteBase, SwitchEntity):
    """Representation of a Dynalite Channel as a Open Peer Power Switch."""

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._device.is_on

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        await self._device.async_turn_on()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        await self._device.async_turn_off()
