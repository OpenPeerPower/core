"""Entity for Zigbee Home Automation."""

import asyncio
import functools
import logging
from typing import Any, Awaitable, Dict, List, Optional

from openpeerpower.core import CALLBACK_TYPE, Event, callback
from openpeerpower.helpers import entity
from openpeerpower.helpers.device_registry import CONNECTION_ZIGBEE
from openpeerpower.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from openpeerpower.helpers.event import async_track_state_change_event
from openpeerpower.helpers.restore_state import RestoreEntity

from .core.const import (
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_NAME,
    DATA_ZHA,
    DATA_ZOP_BRIDGE_ID,
    DOMAIN,
    SIGNAL_GROUP_ENTITY_REMOVED,
    SIGNAL_GROUP_MEMBERSHIP_CHANGE,
    SIGNAL_REMOVE,
)
from .core.helpers import LogMixin
from .core.typing import CALLABLE_T, ChannelType, ZhaDeviceType

_LOGGER = logging.getLogger(__name__)

ENTITY_SUFFIX = "entity_suffix"


class BaseZhaEntity(LogMixin, entity.Entity):
    """A base class for ZHA entities."""

    def __init__(self, unique_id: str, zha_device: ZhaDeviceType, **kwargs):
        """Init ZHA entity."""
        self._name: str = ""
        self._force_update: bool = False
        self._should_poll: bool = False
        self._unique_id: str = unique_id
        self._state: Any = None
        self._device_state_attributes: Dict[str, Any] = {}
        self._zha_device: ZhaDeviceType = zha_device
        self._unsubs: List[CALLABLE_T] = []
        self.remove_future: Awaitable[None] = None

    @property
    def name(self) -> str:
        """Return Entity's default name."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    @property
    def zha_device(self) -> ZhaDeviceType:
        """Return the zha device this entity is attached to."""
        return self._zha_device

    @property
    def device_state_attributes(self) -> Dict[str, Any]:
        """Return device specific state attributes."""
        return self._device_state_attributes

    @property
    def force_update(self) -> bool:
        """Force update this entity."""
        return self._force_update

    @property
    def should_poll(self) -> bool:
        """Poll state from device."""
        return self._should_poll

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return a device description for device registry."""
        zha_device_info = self._zha_device.device_info
        ieee = zha_device_info["ieee"]
        return {
            "connections": {(CONNECTION_ZIGBEE, ieee)},
            "identifiers": {(DOMAIN, ieee)},
            ATTR_MANUFACTURER: zha_device_info[ATTR_MANUFACTURER],
            ATTR_MODEL: zha_device_info[ATTR_MODEL],
            ATTR_NAME: zha_device_info[ATTR_NAME],
            "via_device": (DOMAIN, self.opp.data[DATA_ZHA][DATA_ZOP_BRIDGE_ID]),
        }

    @callback
    def async_state_changed(self) -> None:
        """Entity state changed."""
        self.async_write_op_state()

    @callback
    def async_update_state_attribute(self, key: str, value: Any) -> None:
        """Update a single device state attribute."""
        self._device_state_attributes.update({key: value})
        self.async_write_op_state()

    @callback
    def async_set_state(self, attr_id: int, attr_name: str, value: Any) -> None:
        """Set the entity state."""

    async def async_will_remove_from.opp(self) -> None:
        """Disconnect entity object when removed."""
        for unsub in self._unsubs[:]:
            unsub()
            self._unsubs.remove(unsub)

    @callback
    def async_accept_signal(
        self, channel: ChannelType, signal: str, func: CALLABLE_T, signal_override=False
    ):
        """Accept a signal from a channel."""
        unsub = None
        if signal_override:
            unsub = async_dispatcher_connect(self.opp, signal, func)
        else:
            unsub = async_dispatcher_connect(
                self.opp, f"{channel.unique_id}_{signal}", func
            )
        self._unsubs.append(unsub)

    def log(self, level: int, msg: str, *args):
        """Log a message."""
        msg = f"%s: {msg}"
        args = (self.entity_id,) + args
        _LOGGER.log(level, msg, *args)


class ZhaEntity(BaseZhaEntity, RestoreEntity):
    """A base class for non group ZHA entities."""

    def __init__(
        self,
        unique_id: str,
        zha_device: ZhaDeviceType,
        channels: List[ChannelType],
        **kwargs,
    ):
        """Init ZHA entity."""
        super().__init__(unique_id, zha_device, **kwargs)
        ieeetail = "".join([f"{o:02x}" for o in zha_device.ieee[:4]])
        ch_names = [ch.cluster.ep_attribute for ch in channels]
        ch_names = ", ".join(sorted(ch_names))
        self._name: str = f"{zha_device.name} {ieeetail} {ch_names}"
        self.cluster_channels: Dict[str, ChannelType] = {}
        for channel in channels:
            self.cluster_channels[channel.name] = channel

    @property
    def available(self) -> bool:
        """Return entity availability."""
        return self._zha_device.available

    async def async_added_to.opp(self) -> None:
        """Run when about to be added to.opp."""
        self.remove_future = asyncio.Future()
        self.async_accept_signal(
            None,
            f"{SIGNAL_REMOVE}_{self.zha_device.ieee}",
            functools.partial(self.async_remove, force_remove=True),
            signal_override=True,
        )

        if not self.zha_device.is_mains_powered:
            # mains powered devices will get real time state
            last_state = await self.async_get_last_state()
            if last_state:
                self.async_restore_last_state(last_state)

        self.async_accept_signal(
            None,
            f"{self.zha_device.available_signal}_entity",
            self.async_state_changed,
            signal_override=True,
        )
        self._zha_device.gateway.register_entity_reference(
            self._zha_device.ieee,
            self.entity_id,
            self._zha_device,
            self.cluster_channels,
            self.device_info,
            self.remove_future,
        )

    async def async_will_remove_from.opp(self) -> None:
        """Disconnect entity object when removed."""
        await super().async_will_remove_from.opp()
        self.zha_device.gateway.remove_entity_reference(self)
        self.remove_future.set_result(True)

    @callback
    def async_restore_last_state(self, last_state) -> None:
        """Restore previous state."""

    async def async_update(self) -> None:
        """Retrieve latest state."""
        tasks = [
            channel.async_update()
            for channel in self.cluster_channels.values()
            if hasattr(channel, "async_update")
        ]
        if tasks:
            await asyncio.gather(*tasks)


class ZhaGroupEntity(BaseZhaEntity):
    """A base class for ZHA group entities."""

    def __init__(
        self, entity_ids: List[str], unique_id: str, group_id: int, zha_device, **kwargs
    ) -> None:
        """Initialize a light group."""
        super().__init__(unique_id, zha_device, **kwargs)
        self._available = False
        self._group = zha_device.gateway.groups.get(group_id)
        self._name = f"{self._group.name}_zha_group_0x{group_id:04x}"
        self._group_id: int = group_id
        self._entity_ids: List[str] = entity_ids
        self._async_unsub_state_changed: Optional[CALLBACK_TYPE] = None
        self._handled_group_membership = False

    @property
    def available(self) -> bool:
        """Return entity availability."""
        return self._available

    async def _handle_group_membership_changed(self):
        """Handle group membership changed."""
        # Make sure we don't call remove twice as members are removed
        if self._handled_group_membership:
            return

        self._handled_group_membership = True
        await self.async_remove(force_remove=True)

    async def async_added_to.opp(self) -> None:
        """Register callbacks."""
        await super().async_added_to.opp()

        self.async_accept_signal(
            None,
            f"{SIGNAL_GROUP_MEMBERSHIP_CHANGE}_0x{self._group_id:04x}",
            self._handle_group_membership_changed,
            signal_override=True,
        )

        self._async_unsub_state_changed = async_track_state_change_event(
            self.opp, self._entity_ids, self.async_state_changed_listener
        )

        def send_removed_signal():
            async_dispatcher_send(
                self.opp, SIGNAL_GROUP_ENTITY_REMOVED, self._group_id
            )

        self.async_on_remove(send_removed_signal)

    @callback
    def async_state_changed_listener(self, event: Event):
        """Handle child updates."""
        self.async_schedule_update_op_state(True)

    async def async_will_remove_from.opp(self) -> None:
        """Handle removal from Open Peer Power."""
        await super().async_will_remove_from.opp()
        if self._async_unsub_state_changed is not None:
            self._async_unsub_state_changed()
            self._async_unsub_state_changed = None

    async def async_update(self) -> None:
        """Update the state of the group entity."""
