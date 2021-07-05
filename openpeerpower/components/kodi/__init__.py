"""The kodi component."""

import logging

from pykodi import CannotConnectError, InvalidAuthError, Kodi, get_kodi_connection

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    EVENT_OPENPEERPOWER_STOP,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_WS_PORT,
    DATA_CONNECTION,
    DATA_KODI,
    DATA_REMOVE_LISTENER,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["media_player"]


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Kodi from a config entry."""
    conn = get_kodi_connection(
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_WS_PORT],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        entry.data[CONF_SSL],
        session=async_get_clientsession(opp),
    )

    kodi = Kodi(conn)

    try:
        await conn.connect()
    except CannotConnectError:
        pass
    except InvalidAuthError as error:
        _LOGGER.error(
            "Login to %s failed: [%s]",
            entry.data[CONF_HOST],
            error,
        )
        return False

    async def _close(event):
        await conn.close()

    remove_stop_listener = opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, _close)

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: conn,
        DATA_KODI: kodi,
        DATA_REMOVE_LISTENER: remove_stop_listener,
    }

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = opp.data[DOMAIN].pop(entry.entry_id)
        await data[DATA_CONNECTION].close()
        data[DATA_REMOVE_LISTENER]()

    return unload_ok
