"""Support for Nest sensors that dispatches between API versions."""

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.helpers.typing import OpenPeerPowerType

from .const import DATA_SDM
from .legacy.sensor import async_setup_legacy_entry
from .sensor_sdm import async_setup_sdm_entry


async def async_setup_entry(
    opp: OpenPeerPowerType, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the sensors."""
    if DATA_SDM not in entry.data:
        await async_setup_legacy_entry(opp, entry, async_add_entities)
        return

    await async_setup_sdm_entry(opp, entry, async_add_entities)
