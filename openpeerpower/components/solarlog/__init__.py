"""Solar-Log integration."""
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.helpers.typing import OpenPeerPowerType


async def async_setup(opp, config):
    """Component setup, do nothing."""
    return True


async def async_setup_entry(opp: OpenPeerPowerType, entry: ConfigEntry):
    """Set up a config entry for solarlog."""
    opp.async_create_task(opp.config_entries.async_forward_entry_setup(entry, "sensor"))
    return True


async def async_unload_entry(opp, entry):
    """Unload a config entry."""
    return await opp.config_entries.async_forward_entry_unload(entry, "sensor")
