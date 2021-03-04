"""The epson integration."""
import asyncio
import logging

from epson_projector import Projector
from epson_projector.const import POWER, STATE_UNAVAILABLE as EPSON_STATE_UNAVAILABLE

from openpeerpower.components.media_player import DOMAIN as MEDIA_PLAYER_PLATFORM
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST, CONF_PORT
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .exceptions import CannotConnect

PLATFORMS = [MEDIA_PLAYER_PLATFORM]

_LOGGER = logging.getLogger(__name__)


async def validate_projector(opp: OpenPeerPower, host, port):
    """Validate the given host and port allows us to connect."""
    epson_proj = Projector(
        host=host,
        websession=async_get_clientsession(opp, verify_ssl=False),
        port=port,
    )
    _power = await epson_proj.get_property(POWER)
    if not _power or _power == EPSON_STATE_UNAVAILABLE:
        raise CannotConnect
    return epson_proj


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the epson component."""
    opp.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up epson from a config entry."""
    try:
        projector = await validate_projector(
            opp, entry.data[CONF_HOST], entry.data[CONF_PORT]
        )
    except CannotConnect:
        _LOGGER.warning("Cannot connect to projector %s", entry.data[CONF_HOST])
        return False
    opp.data[DOMAIN][entry.entry_id] = projector
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
