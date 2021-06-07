"""Support for Nest binary sensors that dispatches between API versions."""

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower

from .const import DATA_SDM
from .legacy.binary_sensor import async_setup_legacy_entry


async def async_setup_entry(
    opp: OpenPeerPower, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the binary sensors."""
    assert DATA_SDM not in entry.data
    await async_setup_legacy_entry(opp, entry, async_add_entities)
