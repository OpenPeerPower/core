"""The forked_daapd component."""
from openpeerpower.components.media_player import DOMAIN as MP_DOMAIN

from .const import DOMAIN, OPP_DATA_REMOVE_LISTENERS_KEY, OPP_DATA_UPDATER_KEY


async def async_setup(opp, config):
    """Set up the forked-daapd component."""
    return True


async def async_setup_entry(opp, entry):
    """Set up forked-daapd from a config entry by forwarding to platform."""
    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(entry, MP_DOMAIN)
    )
    return True


async def async_unload_entry(opp, entry):
    """Remove forked-daapd component."""
    status = await opp.config_entries.async_forward_entry_unload(entry, MP_DOMAIN)
    if status and opp.data.get(DOMAIN) and opp.data[DOMAIN].get(entry.entry_id):
        opp.data[DOMAIN][entry.entry_id][
            OPP_DATA_UPDATER_KEY
        ].websocket_handler.cancel()
        for remove_listener in opp.data[DOMAIN][entry.entry_id][
            OPP_DATA_REMOVE_LISTENERS_KEY
        ]:
            remove_listener()
        del opp.data[DOMAIN][entry.entry_id]
        if not opp.data[DOMAIN]:
            del opp.data[DOMAIN]
    return status
