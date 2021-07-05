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


async def async_setup_entry(opp: OpenPeerPower, config_entry: ConfigEntry):
    """Set up Google Maps Travel Time from a config entry."""
    if config_entry.unique_id is not None:
        opp.config_entries.async_update_entry(config_entry, unique_id=None)

        ent_reg = async_get(opp)
        for entity in async_entries_for_config_entry(ent_reg, config_entry.entry_id):
            ent_reg.async_update_entity(
                entity.entity_id, new_unique_id=config_entry.entry_id
            )

    opp.config_entries.async_setup_platforms(config_entry, PLATFORMS)
    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    return await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
