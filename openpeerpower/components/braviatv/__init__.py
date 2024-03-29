"""The Bravia TV component."""

from bravia_tv import BraviaRC

from openpeerpower.const import CONF_HOST, CONF_MAC

from .const import BRAVIARC, DOMAIN, UNDO_UPDATE_LISTENER

PLATFORMS = ["media_player"]


async def async_setup_entry(opp, config_entry):
    """Set up a config entry."""
    host = config_entry.data[CONF_HOST]
    mac = config_entry.data[CONF_MAC]

    undo_listener = config_entry.add_update_listener(update_listener)

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][config_entry.entry_id] = {
        BRAVIARC: BraviaRC(host, mac),
        UNDO_UPDATE_LISTENER: undo_listener,
    }

    opp.config_entries.async_setup_platforms(config_entry, PLATFORMS)

    return True


async def async_unload_entry(opp, config_entry):
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(config_entry, PLATFORMS)

    opp.data[DOMAIN][config_entry.entry_id][UNDO_UPDATE_LISTENER]()

    if unload_ok:
        opp.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


async def update_listener(opp, config_entry):
    """Handle options update."""
    await opp.config_entries.async_reload(config_entry.entry_id)
