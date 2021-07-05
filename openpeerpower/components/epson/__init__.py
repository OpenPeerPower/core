"""The epson integration."""
import logging

from epson_projector import Projector
from epson_projector.const import (
    PWR_OFF_STATE,
    STATE_UNAVAILABLE as EPSON_STATE_UNAVAILABLE,
)

from openpeerpower.components.media_player import DOMAIN as MEDIA_PLAYER_PLATFORM
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, HTTP
from .exceptions import CannotConnect, PoweredOff

PLATFORMS = [MEDIA_PLAYER_PLATFORM]

_LOGGER = logging.getLogger(__name__)


async def validate_projector(
    opp: OpenPeerPower, host, check_power=True, check_powered_on=True
):
    """Validate the given projector host allows us to connect."""
    epson_proj = Projector(
        host=host,
        websession=async_get_clientsession(opp, verify_ssl=False),
        type=HTTP,
    )
    if check_power:
        _power = await epson_proj.get_power()
        if not _power or _power == EPSON_STATE_UNAVAILABLE:
            _LOGGER.debug("Cannot connect to projector")
            raise CannotConnect
        if _power == PWR_OFF_STATE and check_powered_on:
            _LOGGER.debug("Projector is off")
            raise PoweredOff
    return epson_proj


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up epson from a config entry."""
    projector = await validate_projector(
        opp=opp,
        host=entry.data[CONF_HOST],
        check_power=False,
        check_powered_on=False,
    )
    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = projector
    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
