"""Component for the Somfy MyLink device supporting the Synergy API."""
import asyncio
import logging

from somfy_mylink_synergy import SomfyMyLinkSynergy

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST, CONF_PORT
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import config_validation as cv

from .const import CONF_SYSTEM_ID, DATA_SOMFY_MYLINK, DOMAIN, MYLINK_STATUS, PLATFORMS

UNDO_UPDATE_LISTENER = "undo_update_listener"

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.deprecated(DOMAIN)


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up Somfy MyLink from a config entry."""
    opp.data.setdefault(DOMAIN, {})

    config = entry.data
    somfy_mylink = SomfyMyLinkSynergy(
        config[CONF_SYSTEM_ID], config[CONF_HOST], config[CONF_PORT]
    )

    try:
        mylink_status = await somfy_mylink.status_info()
    except asyncio.TimeoutError as ex:
        raise ConfigEntryNotReady(
            "Unable to connect to the Somfy MyLink device, please check your settings"
        ) from ex

    if not mylink_status or "error" in mylink_status:
        _LOGGER.error(
            "Somfy Mylink failed to setup because of an error: %s",
            mylink_status.get("error", {}).get(
                "message", "Empty response from mylink device"
            ),
        )
        return False

    if "result" not in mylink_status:
        raise ConfigEntryNotReady("The Somfy MyLink device returned an empty result")

    undo_listener = entry.add_update_listener(_async_update_listener)

    opp.data[DOMAIN][entry.entry_id] = {
        DATA_SOMFY_MYLINK: somfy_mylink,
        MYLINK_STATUS: mylink_status,
        UNDO_UPDATE_LISTENER: undo_listener,
    }

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def _async_update_listener(opp: OpenPeerPower, entry: ConfigEntry):
    """Handle options update."""
    await opp.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)

    opp.data[DOMAIN][entry.entry_id][UNDO_UPDATE_LISTENER]()

    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
