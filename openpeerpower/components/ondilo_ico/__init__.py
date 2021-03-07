"""The Ondilo ICO integration."""
import asyncio

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import config_entry_oauth2_flow

from . import api, config_flow
from .const import DOMAIN
from .oauth_impl import OndiloOauth2Implementation

PLATFORMS = ["sensor"]


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the Ondilo ICO component."""
    opp.data.setdefault(DOMAIN, {})

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up Ondilo ICO from a config entry."""

    config_flow.OAuth2FlowHandler.async_register_implementation(
        opp,
        OndiloOauth2Implementation(opp),
    )

    implementation = (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(opp, entry)
    )

    opp.data[DOMAIN][entry.entry_id] = api.OndiloClient(opp, entry, implementation)

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
