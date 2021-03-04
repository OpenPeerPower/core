"""The Nightscout integration."""
import asyncio
from asyncio import TimeoutError as AsyncIOTimeoutError

from aiohttp import ClientError
from py_nightscout import Api as NightscoutAPI

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_API_KEY, CONF_URL
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import device_registry as dr
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.entity import SLOW_UPDATE_WARNING

from .const import DOMAIN

PLATFORMS = ["sensor"]
_API_TIMEOUT = SLOW_UPDATE_WARNING - 1


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the Nightscout component."""
    opp.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Nightscout from a config entry."""
    server_url = entry.data[CONF_URL]
    api_key = entry.data.get(CONF_API_KEY)
    session = async_get_clientsession(opp)
    api = NightscoutAPI(server_url, session=session, api_secret=api_key)
    try:
        status = await api.get_server_status()
    except (ClientError, AsyncIOTimeoutError, OSError) as error:
        raise ConfigEntryNotReady from error

    opp.data[DOMAIN][entry.entry_id] = api

    device_registry = await dr.async_get_registry(opp)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, server_url)},
        manufacturer="Nightscout Foundation",
        name=status.name,
        sw_version=status.version,
        entry_type="service",
    )

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
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
