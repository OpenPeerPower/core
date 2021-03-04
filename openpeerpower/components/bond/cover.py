"""Support for Bond covers."""
from typing import Any, Callable, List, Optional

from bond_api import Action, BPUPSubscriptions, DeviceType

from openpeerpower.components.cover import DEVICE_CLASS_SHADE, CoverEntity
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
    """Set up Bond cover devices."""
    data = opp.data[DOMAIN][entry.entry_id]
    hub: BondHub = data[HUB]
    bpup_subs: BPUPSubscriptions = data[BPUP_SUBS]

    covers: List[Entity] = [
        BondCover(hub, device, bpup_subs)
        for device in hub.devices
        if device.type == DeviceType.MOTORIZED_SHADES
    ]

    async_add_entities(covers, True)


class BondCover(BondEntity, CoverEntity):
    """Representation of a Bond cover."""

    def __init__(
        self, hub: BondHub, device: BondDevice, bpup_subs: BPUPSubscriptions
    ) -> None:
        """Create OP entity representing Bond cover."""
        super().__init__(hub, device, bpup_subs)

        self._closed: Optional[bool] = None

    def _apply_state(self, state: dict) -> None:
        cover_open = state.get("open")
        self._closed = True if cover_open == 0 else False if cover_open == 1 else None

    @property
    def device_class(self) -> Optional[str]:
        """Get device class."""
        return DEVICE_CLASS_SHADE

    @property
    def is_closed(self) -> Optional[bool]:
        """Return if the cover is closed or not."""
        return self._closed

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self._hub.bond.action(self._device.device_id, Action.open())

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close cover."""
        await self._hub.bond.action(self._device.device_id, Action.close())

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Hold cover."""
        await self._hub.bond.action(self._device.device_id, Action.hold())
