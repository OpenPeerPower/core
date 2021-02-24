"""Xbox friends binary sensors."""
from functools import partial
from typing import Dict, List

from openpeerpower.core import callback
from openpeerpower.helpers.entity_registry import (
    async_get_registry as async_get_entity_registry,
)
from openpeerpower.helpers.typing import OpenPeerPowerType

from . import XboxUpdateCoordinator
from .base_sensor import XboxBaseSensorEntity
from .const import DOMAIN

SENSOR_ATTRIBUTES = ["status", "gamer_score", "account_tier", "gold_tenure"]


async def async_setup_entry(opp: OpenPeerPowerType, config_entry, async_add_entities):
    """Set up Xbox Live friends."""
    coordinator: XboxUpdateCoordinator = opp.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    update_friends = partial(async_update_friends, coordinator, {}, async_add_entities)

    unsub = coordinator.async_add_listener(update_friends)
    opp.data[DOMAIN][config_entry.entry_id]["sensor_unsub"] = unsub
    update_friends()


class XboxSensorEntity(XboxBaseSensorEntity):
    """Representation of a Xbox presence state."""

    @property
    def state(self):
        """Return the state of the requested attribute."""
        if not self.coordinator.last_update_success:
            return None

        return getattr(self.data, self.attribute, None)


@callback
def async_update_friends(
    coordinator: XboxUpdateCoordinator,
    current: Dict[str, List[XboxSensorEntity]],
    async_add_entities,
) -> None:
    """Update friends."""
    new_ids = set(coordinator.data.presence)
    current_ids = set(current)

    # Process new favorites, add them to Open Peer Power
    new_entities = []
    for xuid in new_ids - current_ids:
        current[xuid] = [
            XboxSensorEntity(coordinator, xuid, attribute)
            for attribute in SENSOR_ATTRIBUTES
        ]
        new_entities = new_entities + current[xuid]

    if new_entities:
        async_add_entities(new_entities)

    # Process deleted favorites, remove them from Open Peer Power
    for xuid in current_ids - new_ids:
        coordinator.opp.async_create_task(
            async_remove_entities(xuid, coordinator, current)
        )


async def async_remove_entities(
    xuid: str,
    coordinator: XboxUpdateCoordinator,
    current: Dict[str, XboxSensorEntity],
) -> None:
    """Remove friend sensors from Open Peer Power."""
    registry = await async_get_entity_registry(coordinator.opp)
    entities = current[xuid]
    for entity in entities:
        if entity.entity_id in registry.entities:
            registry.async_remove(entity.entity_id)
    del current[xuid]
