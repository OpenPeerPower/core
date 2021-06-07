"""The kmtronic integration."""
from datetime import timedelta
import logging

import aiohttp
import async_timeout
from pykmtronic.auth import Auth
from pykmtronic.hub import KMTronicHubAPI

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import aiohttp_client
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DATA_COORDINATOR, DATA_HUB, DOMAIN, MANUFACTURER, UPDATE_LISTENER

PLATFORMS = ["switch"]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up kmtronic from a config entry."""
    session = aiohttp_client.async_get_clientsession(opp)
    auth = Auth(
        session,
        f"http://{entry.data[CONF_HOST]}",
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )
    hub = KMTronicHubAPI(auth)

    async def async_update_data():
        try:
            async with async_timeout.timeout(10):
                await hub.async_update_relays()
        except aiohttp.client_exceptions.ClientResponseError as err:
            raise UpdateFailed(f"Wrong credentials: {err}") from err
        except aiohttp.client_exceptions.ClientConnectorError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    coordinator = DataUpdateCoordinator(
        opp,
        _LOGGER,
        name=f"{MANUFACTURER} {hub.name}",
        update_method=async_update_data,
        update_interval=timedelta(seconds=30),
    )
    await coordinator.async_config_entry_first_refresh()

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = {
        DATA_HUB: hub,
        DATA_COORDINATOR: coordinator,
    }

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    update_listener = entry.add_update_listener(async_update_options)
    opp.data[DOMAIN][entry.entry_id][UPDATE_LISTENER] = update_listener

    return True


async def async_update_options(opp: OpenPeerPower, config_entry: ConfigEntry) -> None:
    """Update options."""
    await opp.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        update_listener = opp.data[DOMAIN][entry.entry_id][UPDATE_LISTENER]
        update_listener()
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
