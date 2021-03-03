"""Support for the Dynalite devices as entities."""
from typing import Any, Callable, Dict

from openpeerpower.components.dynalite.bridge import DynaliteBridge
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers.dispatcher import async_dispatcher_connect
from openpeerpower.helpers.entity import Entity

from .const import DOMAIN, LOGGER


def async_setup_entry_base(
    opp: OpenPeerPower,
    config_entry: ConfigEntry,
    async_add_entities: Callable,
    platform: str,
    entity_from_device: Callable,
) -> None:
    """Record the async_add_entities function to add them later when received from Dynalite."""
    LOGGER.debug("Setting up %s entry = %s", platform, config_entry.data)
    bridge = opp.data[DOMAIN][config_entry.entry_id]

    @callback
    def async_add_entities_platform(devices):
        # assumes it is called with a single platform
        added_entities = []
        for device in devices:
            added_entities.append(entity_from_device(device, bridge))
        if added_entities:
            async_add_entities(added_entities)

    bridge.register_add_devices(platform, async_add_entities_platform)


class DynaliteBase(Entity):
    """Base class for the Dynalite entities."""

    def __init__(self, device: Any, bridge: DynaliteBridge) -> None:
        """Initialize the base class."""
        self._device = device
        self._bridge = bridge
        self._unsub_dispatchers = []

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._device.name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the entity."""
        return self._device.unique_id

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._device.available

    @property
    def device_info(self) -> Dict[str, Any]:
        """Device info for this entity."""
        return {
            "identifiers": {(DOMAIN, self._device.unique_id)},
            "name": self.name,
            "manufacturer": "Dynalite",
        }

    async def async_added_to_opp(self) -> None:
        """Added to opp so need to register to dispatch."""
        # register for device specific update
        self._unsub_dispatchers.append(
            async_dispatcher_connect(
                self.opp,
                self._bridge.update_signal(self._device),
                self.async_schedule_update_op_state,
            )
        )
        # register for wide update
        self._unsub_dispatchers.append(
            async_dispatcher_connect(
                self.opp,
                self._bridge.update_signal(),
                self.async_schedule_update_op_state,
            )
        )

    async def async_will_remove_from_opp(self) -> None:
        """Unregister signal dispatch listeners when being removed."""
        for unsub in self._unsub_dispatchers:
            unsub()
        self._unsub_dispatchers = []
