"""The dsmr component."""
from asyncio import CancelledError
from contextlib import suppress

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower

from .const import DATA_LISTENER, DATA_TASK, DOMAIN, PLATFORMS


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up DSMR from a config entry."""
    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = {}

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    listener = entry.add_update_listener(async_update_options)
    opp.data[DOMAIN][entry.entry_id][DATA_LISTENER] = listener

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    task = opp.data[DOMAIN][entry.entry_id][DATA_TASK]
    listener = opp.data[DOMAIN][entry.entry_id][DATA_LISTENER]

    # Cancel the reconnect task
    task.cancel()
    with suppress(CancelledError):
        await task

    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        listener()

        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_update_options(opp: OpenPeerPower, config_entry: ConfigEntry):
    """Update options."""
    await opp.config_entries.async_reload(config_entry.entry_id)
