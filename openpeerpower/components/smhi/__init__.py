"""Support for the Swedish weather institute weather service."""
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower

PLATFORMS = ["weather"]


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up SMHI forecast as config entry."""
    opp.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
