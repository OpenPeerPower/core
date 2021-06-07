"""Support for AVM Fritz!Box functions."""
import logging

from fritzconnection.core.exceptions import FritzConnectionException, FritzSecurityError

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    EVENT_OPENPEERPOWER_STOP,
)
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .common import FritzBoxTools, FritzData
from .const import DATA_FRITZ, DOMAIN, PLATFORMS
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up fritzboxtools from config entry."""
    _LOGGER.debug("Setting up FRITZ!Box Tools component")
    fritz_tools = FritzBoxTools(
        opp.opp,
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
    )

    try:
        await fritz_tools.async_setup()
        await fritz_tools.async_start(entry.options)
    except FritzSecurityError as ex:
        raise ConfigEntryAuthFailed from ex
    except FritzConnectionException as ex:
        raise ConfigEntryNotReady from ex

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = fritz_tools

    if DATA_FRITZ not in opp.data:
        opp.data[DATA_FRITZ] = FritzData()

    @callback
    def _async_unload(event):
        fritz_tools.async_unload()

    entry.async_on_unload(
        opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, _async_unload)
    )
    entry.async_on_unload(entry.add_update_listener(update_listener))

    # Load the other platforms like switch
    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    await async_setup_services(opp)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload FRITZ!Box Tools config entry."""
    fritzbox: FritzBoxTools = opp.data[DOMAIN][entry.entry_id]
    fritzbox.async_unload()

    fritz_data = opp.data[DATA_FRITZ]
    fritz_data.tracked.pop(fritzbox.unique_id)

    if not bool(fritz_data.tracked):
        opp.data.pop(DATA_FRITZ)

    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    await async_unload_services(opp)

    return unload_ok


async def update_listener(opp: OpenPeerPower, entry: ConfigEntry):
    """Update when config_entry options update."""
    if entry.options:
        await opp.config_entries.async_reload(entry.entry_id)
