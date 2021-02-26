"""Plugwise platform for Open Peer Power Core."""

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST
from openpeerpower.core import OpenPeerPower

from .gateway import async_setup_entry_gw, async_unload_entry_gw


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the Plugwise platform."""
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up Plugwise components from a config entry."""
    if entry.data.get(CONF_HOST):
        return await async_setup_entry_gw(opp, entry)
    # PLACEHOLDER USB entry setup
    return False


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload the Plugwise components."""
    if entry.data.get(CONF_HOST):
        return await async_unload_entry_gw(opp, entry)
    # PLACEHOLDER USB entry setup
    return False
