"""Support for Nest cameras that dispatches between API versions."""

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.helpers.typing import OpenPeerPowerType

from .camera_sdm import async_setup_sdm_entry
from .const import DATA_SDM
from .legacy.camera import async_setup_legacy_entry


async def async_setup_entry(
    opp: OpenPeerPowerType, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the cameras."""
    if DATA_SDM not in entry.data:
        await async_setup_legacy_entry(opp, entry, async_add_entities)
        return
    await async_setup_sdm_entry(opp, entry, async_add_entities)
