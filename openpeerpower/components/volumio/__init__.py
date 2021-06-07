"""The Volumio integration."""

from pyvolumio import CannotConnectError, Volumio

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST, CONF_PORT
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession

from .const import DATA_INFO, DATA_VOLUMIO, DOMAIN

PLATFORMS = ["media_player"]


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up Volumio from a config entry."""

    volumio = Volumio(
        entry.data[CONF_HOST], entry.data[CONF_PORT], async_get_clientsession(opp)
    )
    try:
        info = await volumio.get_system_version()
    except CannotConnectError as error:
        raise ConfigEntryNotReady from error

    opp.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_VOLUMIO: volumio,
        DATA_INFO: info,
    }

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
