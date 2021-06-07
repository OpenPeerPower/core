"""The mill component."""

PLATFORMS = ["climate"]


async def async_setup_entry(opp, entry):
    """Set up the Mill heater."""
    opp.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(opp, entry):
    """Unload a config entry."""
    return await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
