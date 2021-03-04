"""The 1-Wire component."""
import asyncio

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.typing import OpenPeerPowerType

from .const import DOMAIN, PLATFORMS
from .onewirehub import CannotConnect, OneWireHub


async def async_setup(opp, config):
    """Set up 1-Wire integrations."""
    return True


async def async_setup_entry(opp: OpenPeerPowerType, config_entry: ConfigEntry):
    """Set up a 1-Wire proxy for a config entry."""
    opp.data.setdefault(DOMAIN, {})

    onewirehub = OneWireHub(opp)
    try:
        await onewirehub.initialize(config_entry)
    except CannotConnect as exc:
        raise ConfigEntryNotReady() from exc

    opp.data[DOMAIN][config_entry.unique_id] = onewirehub

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(config_entry, platform)
        )
    return True


async def async_unload_entry(opp: OpenPeerPowerType, config_entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(config_entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        opp.data[DOMAIN].pop(config_entry.unique_id)
    return unload_ok
