"""The Logitech Squeezebox integration."""

import logging

from openpeerpower.components.media_player import DOMAIN as MP_DOMAIN
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower

from .const import DISCOVERY_TASK, DOMAIN, PLAYER_DISCOVERY_UNSUB

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [MP_DOMAIN]


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up Logitech Squeezebox from a config entry."""
    opp.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(opp, entry):
    """Unload a config entry."""
    # Stop player discovery task for this config entry.
    opp.data[DOMAIN][entry.entry_id][PLAYER_DISCOVERY_UNSUB]()

    # Remove stored data for this config entry
    opp.data[DOMAIN].pop(entry.entry_id)

    # Stop server discovery task if this is the last config entry.
    current_entries = opp.config_entries.async_entries(DOMAIN)
    if len(current_entries) == 1 and current_entries[0] == entry:
        _LOGGER.debug("Stopping server discovery task")
        opp.data[DOMAIN][DISCOVERY_TASK].cancel()
        opp.data[DOMAIN].pop(DISCOVERY_TASK)

    return await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
