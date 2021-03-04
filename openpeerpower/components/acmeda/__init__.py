"""The Rollease Acmeda Automate integration."""
import asyncio

from openpeerpower import config_entries, core

from .const import DOMAIN
from .hub import PulseHub

CONF_HUBS = "hubs"

PLATFORMS = ["cover", "sensor"]


async def async_setup(opp: core.OpenPeerPower, config: dict):
    """Set up the Rollease Acmeda Automate component."""
    return True


async def async_setup_entry(
    opp: core.OpenPeerPower, config_entry: config_entries.ConfigEntry
):
    """Set up Rollease Acmeda Automate hub from a config entry."""
    hub = PulseHub(opp, config_entry)

    if not await hub.async_setup():
        return False

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][config_entry.entry_id] = hub

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    return True


async def async_unload_entry(
    opp: core.OpenPeerPower, config_entry: config_entries.ConfigEntry
):
    """Unload a config entry."""
    hub = opp.data[DOMAIN][config_entry.entry_id]

    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(config_entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if not await hub.async_reset():
        return False

    if unload_ok:
        opp.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok
