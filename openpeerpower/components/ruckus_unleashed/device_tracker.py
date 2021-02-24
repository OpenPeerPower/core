"""Support for Ruckus Unleashed devices."""
from typing import Optional

from openpeerpower.components.device_tracker import SOURCE_TYPE_ROUTER
from openpeerpower.components.device_tracker.config_entry import ScannerEntity
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import callback
from openpeerpower.helpers import entity_registry
from openpeerpower.helpers.device_registry import CONNECTION_NETWORK_MAC
from openpeerpower.helpers.typing import OpenPeerPowerType
from openpeerpower.helpers.update_coordinator import CoordinatorEntity

from .const import (
    API_ACCESS_POINT,
    API_CLIENTS,
    API_NAME,
    COORDINATOR,
    DOMAIN,
    MANUFACTURER,
    UNDO_UPDATE_LISTENERS,
)


async def async_setup_entry(
    opp: OpenPeerPowerType, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up device tracker for Ruckus Unleashed component."""
    coordinator = opp.data[DOMAIN][entry.entry_id][COORDINATOR]

    tracked = set()

    @callback
    def router_update():
        """Update the values of the router."""
        add_new_entities(coordinator, async_add_entities, tracked)

    router_update()

    opp.data[DOMAIN][entry.entry_id][UNDO_UPDATE_LISTENERS].append(
        coordinator.async_add_listener(router_update)
    )

    registry = await entity_registry.async_get_registry(opp)
    restore_entities(registry, coordinator, entry, async_add_entities, tracked)


@callback
def add_new_entities(coordinator, async_add_entities, tracked):
    """Add new tracker entities from the router."""
    new_tracked = []

    for mac in coordinator.data[API_CLIENTS]:
        if mac in tracked:
            continue

        device = coordinator.data[API_CLIENTS][mac]
        new_tracked.append(RuckusUnleashedDevice(coordinator, mac, device[API_NAME]))
        tracked.add(mac)

    if new_tracked:
        async_add_entities(new_tracked)


@callback
def restore_entities(registry, coordinator, entry, async_add_entities, tracked):
    """Restore clients that are not a part of active clients list."""
    missing = []

    for entity in registry.entities.values():
        if entity.config_entry_id == entry.entry_id and entity.platform == DOMAIN:
            if entity.unique_id not in coordinator.data[API_CLIENTS]:
                missing.append(
                    RuckusUnleashedDevice(
                        coordinator, entity.unique_id, entity.original_name
                    )
                )
                tracked.add(entity.unique_id)

    if missing:
        async_add_entities(missing)


class RuckusUnleashedDevice(CoordinatorEntity, ScannerEntity):
    """Representation of a Ruckus Unleashed client."""

    def __init__(self, coordinator, mac, name) -> None:
        """Initialize a Ruckus Unleashed client."""
        super().__init__(coordinator)
        self._mac = mac
        self._name = name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._mac

    @property
    def name(self) -> str:
        """Return the name."""
        if self.is_connected:
            return (
                self.coordinator.data[API_CLIENTS][self._mac][API_NAME]
                or f"{MANUFACTURER} {self._mac}"
            )
        return self._name

    @property
    def is_connected(self) -> bool:
        """Return true if the device is connected to the network."""
        return self._mac in self.coordinator.data[API_CLIENTS]

    @property
    def source_type(self) -> str:
        """Return the source type."""
        return SOURCE_TYPE_ROUTER

    @property
    def device_info(self) -> Optional[dict]:
        """Return the device information."""
        if self.is_connected:
            return {
                "name": self.name,
                "connections": {(CONNECTION_NETWORK_MAC, self._mac)},
                "via_device": (
                    CONNECTION_NETWORK_MAC,
                    self.coordinator.data[API_CLIENTS][self._mac][API_ACCESS_POINT],
                ),
            }
        return None
