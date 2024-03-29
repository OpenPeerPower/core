"""The MyQ integration."""
from datetime import timedelta
import logging

import pymyq
from pymyq.errors import InvalidCredentialsError, MyQError

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from openpeerpower.helpers import aiohttp_client
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, MYQ_COORDINATOR, MYQ_GATEWAY, PLATFORMS, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up MyQ from a config entry."""

    opp.data.setdefault(DOMAIN, {})
    websession = aiohttp_client.async_get_clientsession(opp)
    conf = entry.data

    try:
        myq = await pymyq.login(conf[CONF_USERNAME], conf[CONF_PASSWORD], websession)
    except InvalidCredentialsError as err:
        raise ConfigEntryAuthFailed from err
    except MyQError as err:
        raise ConfigEntryNotReady from err

    # Called by DataUpdateCoordinator, allows to capture any MyQError exceptions and to throw an OPP UpdateFailed
    # exception instead, preventing traceback in OPP logs.
    async def async_update_data():
        try:
            return await myq.update_device_info()
        except InvalidCredentialsError as err:
            raise ConfigEntryAuthFailed from err
        except MyQError as err:
            raise UpdateFailed(str(err)) from err

    coordinator = DataUpdateCoordinator(
        opp,
        _LOGGER,
        name="myq devices",
        update_method=async_update_data,
        update_interval=timedelta(seconds=UPDATE_INTERVAL),
    )

    opp.data[DOMAIN][entry.entry_id] = {MYQ_GATEWAY: myq, MYQ_COORDINATOR: coordinator}

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
