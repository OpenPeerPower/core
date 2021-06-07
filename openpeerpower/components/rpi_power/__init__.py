"""The Raspberry Pi Power Supply Checker integration."""
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower

PLATFORMS = ["binary_sensor"]


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up Raspberry Pi Power Supply Checker from a config entry."""
    opp.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    return await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
