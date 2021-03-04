"""The dsmr component."""
import asyncio
from asyncio import CancelledError

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower

from .const import DATA_LISTENER, DATA_TASK, DOMAIN, PLATFORMS


async def async_setup(opp, config: dict):
    """Set up the DSMR platform."""
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up DSMR from a config entry."""
    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = {}

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    listener = entry.add_update_listener(async_update_options)
    opp.data[DOMAIN][entry.entry_id][DATA_LISTENER] = listener

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    task = opp.data[DOMAIN][entry.entry_id][DATA_TASK]
    listener = opp.data[DOMAIN][entry.entry_id][DATA_LISTENER]

    # Cancel the reconnect task
    task.cancel()
    try:
        await task
    except CancelledError:
        pass

    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        listener()

        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_update_options(opp: OpenPeerPower, config_entry: ConfigEntry):
    """Update options."""
    await opp.config_entries.async_reload(config_entry.entry_id)
