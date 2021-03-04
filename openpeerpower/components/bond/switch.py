"""Support for Bond generic devices."""
from typing import Any, Callable, List, Optional

from bond_api import Action, BPUPSubscriptions, DeviceType

from openpeerpower.components.switch import SwitchEntity
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.entity import Entity

from .const import BPUP_SUBS, DOMAIN, HUB
from .entity import BondEntity
from .utils import BondDevice, BondHub


async def async_setup_entry(
    opp: OpenPeerPower,
    entry: ConfigEntry,
    async_add_entities: Callable[[List[Entity], bool], None],
) -> None:
    """Set up Bond generic devices."""
    data = opp.data[DOMAIN][entry.entry_id]
    hub: BondHub = data[HUB]
    bpup_subs: BPUPSubscriptions = data[BPUP_SUBS]

    switches: List[Entity] = [
        BondSwitch(hub, device, bpup_subs)
        for device in hub.devices
        if DeviceType.is_generic(device.type)
    ]

    async_add_entities(switches, True)


class BondSwitch(BondEntity, SwitchEntity):
    """Representation of a Bond generic device."""

    def __init__(self, hub: BondHub, device: BondDevice, bpup_subs: BPUPSubscriptions):
        """Create OP entity representing Bond generic device (switch)."""
        super().__init__(hub, device, bpup_subs)

        self._power: Optional[bool] = None

    def _apply_state(self, state: dict) -> None:
        self._power = state.get("power")

    @property
    def is_on(self) -> bool:
        """Return True if power is on."""
        return self._power == 1

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        await self._hub.bond.action(self._device.device_id, Action.turn_on())

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        await self._hub.bond.action(self._device.device_id, Action.turn_off())
