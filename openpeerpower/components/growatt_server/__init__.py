"""The Growatt server PV inverter sensor integration."""
from openpeerpower import config_entries
from openpeerpower.core import OpenPeerPower

from .const import PLATFORMS


async def async_setup_entry(
    opp: OpenPeerPower, entry: config_entries.ConfigEntry
) -> bool:
    """Load the saved entities."""

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(opp, entry):
    """Unload a config entry."""
    return await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
