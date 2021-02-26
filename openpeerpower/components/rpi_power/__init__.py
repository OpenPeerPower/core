"""The Raspberry Pi Power Supply Checker integration."""
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the Raspberry Pi Power Supply Checker component."""
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Raspberry Pi Power Supply Checker from a config entry."""
    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(entry, "binary_sensor")
    )
    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    return await opp.config_entries.async_forward_entry_unload(entry, "binary_sensor")
