"""Support for Dynalite channels as lights."""
from typing import Callable

from openpeerpower.components.light import SUPPORT_BRIGHTNESS, LightEntity
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower

from .dynalitebase import DynaliteBase, async_setup_entry_base


async def async_setup_entry(
    opp: OpenPeerPower, config_entry: ConfigEntry, async_add_entities: Callable
) -> None:
    """Record the async_add_entities function to add them later when received from Dynalite."""
    async_setup_entry_base(
        opp, config_entry, async_add_entities, "light", DynaliteLight
    )


class DynaliteLight(DynaliteBase, LightEntity):
    """Representation of a Dynalite Channel as a Open Peer Power Light."""

    @property
    def brightness(self) -> int:
        """Return the brightness of this light between 0..255."""
        return self._device.brightness

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self._device.is_on

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the light on."""
        await self._device.async_turn_on(**kwargs)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the light off."""
        await self._device.async_turn_off(**kwargs)

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return SUPPORT_BRIGHTNESS
