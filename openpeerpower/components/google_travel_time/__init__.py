"""The google_travel_time component."""
import logging

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.entity_registry import (
    async_entries_for_config_entry,
    async_get,
)

PLATFORMS = ["sensor"]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up Google Maps Travel Time from a config entry."""
    if entry.unique_id is not None:
        opp.config_entries.async_update_entry(entry, unique_id=None)

        ent_reg = async_get(opp)
        for entity in async_entries_for_config_entry(ent_reg, entry.entry_id):
            ent_reg.async_update_entity(entity.entity_id, new_unique_id=entry.entry_id)

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    return await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
