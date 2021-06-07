"""Solar-Log integration."""
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower

PLATFORMS = ["sensor"]


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up a config entry for solarlog."""
    opp.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(opp, entry):
    """Unload a config entry."""
    return await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
