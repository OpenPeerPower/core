"""UK Environment Agency Flood Monitoring Integration."""

from .const import DOMAIN

PLATFORMS = ["sensor"]


async def async_setup_entry(opp, entry):
    """Set up flood monitoring sensors for this config entry."""
    opp.data.setdefault(DOMAIN, {})
    opp.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(opp, entry):
    """Unload flood monitoring sensors."""
    return await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
