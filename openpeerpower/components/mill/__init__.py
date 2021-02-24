"""The mill component."""


async def async_setup(opp, config):
    """Set up the Mill platform."""
    return True


async def async_setup_entry(opp, entry):
    """Set up the Mill heater."""
    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(entry, "climate")
    )
    return True


async def async_unload_entry(opp, config_entry):
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_forward_entry_unload(
        config_entry, "climate"
    )
    return unload_ok
