"""The Rituals Perfume Genie integration."""
import asyncio
import logging

from aiohttp.client_exceptions import ClientConnectorError
from pyrituals import Account

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession

from .const import ACCOUNT_HASH, DOMAIN

_LOGGER = logging.getLogger(__name__)

EMPTY_CREDENTIALS = ""

PLATFORMS = ["switch"]


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the Rituals Perfume Genie component."""
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Rituals Perfume Genie from a config entry."""
    session = async_get_clientsession(opp)
    account = Account(EMPTY_CREDENTIALS, EMPTY_CREDENTIALS, session)
    account.data = {ACCOUNT_HASH: entry.data.get(ACCOUNT_HASH)}

    try:
        await account.get_devices()
    except ClientConnectorError as ex:
        raise ConfigEntryNotReady from ex

    opp.data.setdefault(DOMAIN, {})[entry.entry_id] = account

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
