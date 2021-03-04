"""Zerproc lights integration."""
import asyncio

from openpeerpower.config_entries import SOURCE_IMPORT, ConfigEntry
from openpeerpower.core import OpenPeerPower

from .const import DOMAIN

PLATFORMS = ["light"]


async def async_setup(opp, config):
    """Set up the Zerproc platform."""
    opp.async_create_task(
        opp.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_IMPORT})
    )

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Zerproc from a config entry."""
    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    return all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
