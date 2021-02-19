"""Kuler Sky lights integration."""
import asyncio

from openpeerpower.config_entries import ConfigEntry
from openpeerpowerr.core import OpenPeerPower

from .const import DOMAIN

PLATFORMS = ["light"]


async def async_setup.opp: OpenPeerPower, config: dict):
    """Set up the Kuler Sky component."""
    return True


async def async_setup_entry.opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Kuler Sky from a config entry."""
    for component in PLATFORMS:
       .opp.async_create_task(
           .opp.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry.opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
               .opp.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
       .opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
