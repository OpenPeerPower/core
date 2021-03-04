"""Support for Aqualink pool feature switches."""
from openpeerpower.components.switch import DOMAIN, SwitchEntity
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.helpers.typing import OpenPeerPowerType

from . import AqualinkEntity, refresh_system
from .const import DOMAIN as AQUALINK_DOMAIN

PARALLEL_UPDATES = 0


async def async_setup_entry(
    opp: OpenPeerPowerType, config_entry: ConfigEntry, async_add_entities
) -> None:
    """Set up discovered switches."""
    devs = []
    for dev in opp.data[AQUALINK_DOMAIN][DOMAIN]:
        devs.append(OppAqualinkSwitch(dev))
    async_add_entities(devs, True)


class OppAqualinkSwitch(AqualinkEntity, SwitchEntity):
    """Representation of a switch."""

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return self.dev.label

    @property
    def icon(self) -> str:
        """Return an icon based on the switch type."""
        if self.name == "Cleaner":
            return "mdi:robot-vacuum"
        if self.name == "Waterfall" or self.name.endswith("Dscnt"):
            return "mdi:fountain"
        if self.name.endswith("Pump") or self.name.endswith("Blower"):
            return "mdi:fan"
        if self.name.endswith("Heater"):
            return "mdi:radiator"

    @property
    def is_on(self) -> bool:
        """Return whether the switch is on or not."""
        return self.dev.is_on

    @refresh_system
    async def async_turn_on(self, **kwargs) -> None:
        """Turn on the switch."""
        await self.dev.turn_on()

    @refresh_system
    async def async_turn_off(self, **kwargs) -> None:
        """Turn off the switch."""
        await self.dev.turn_off()
