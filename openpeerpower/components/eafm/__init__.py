"""UK Environment Agency Flood Monitoring Integration."""

from .const import DOMAIN


async def async_setup(opp, config):
    """Set up devices."""
    opp.data[DOMAIN] = {}
    return True


async def async_setup_entry(opp, entry):
    """Set up flood monitoring sensors for this config entry."""
    opp.async_create_task(opp.config_entries.async_forward_entry_setup(entry, "sensor"))

    return True


async def async_unload_entry(opp, config_entry):
    """Unload flood monitoring sensors."""
    return await opp.config_entries.async_forward_entry_unload(config_entry, "sensor")
