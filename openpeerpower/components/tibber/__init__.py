"""Support for Tibber."""
import asyncio
import logging

import aiohttp
import tibber
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.const import CONF_ACCESS_TOKEN, CONF_NAME, EVENT_OPENPEERPOWER_STOP
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import discovery
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
import openpeerpower.helpers.config_validation as cv
from openpeerpower.util import dt as dt_util

from .const import DATA_OPP_CONFIG, DOMAIN

PLATFORMS = [
    "sensor",
]

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_ACCESS_TOKEN): cv.string})},
    extra=vol.ALLOW_EXTRA,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(opp, config):
    """Set up the Tibber component."""

    opp.data[DATA_OPP_CONFIG] = config

    if DOMAIN not in config:
        return True

    opp.async_create_task(
        opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=config[DOMAIN],
        )
    )

    return True


async def async_setup_entry(opp, entry):
    """Set up a config entry."""

    tibber_connection = tibber.Tibber(
        access_token=entry.data[CONF_ACCESS_TOKEN],
        websession=async_get_clientsession(opp),
        time_zone=dt_util.DEFAULT_TIME_ZONE,
    )
    opp.data[DOMAIN] = tibber_connection

    async def _close(event):
        await tibber_connection.rt_disconnect()

    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, _close)

    try:
        await tibber_connection.update_info()
    except asyncio.TimeoutError as err:
        raise ConfigEntryNotReady from err
    except aiohttp.ClientError as err:
        _LOGGER.error("Error connecting to Tibber: %s ", err)
        return False
    except tibber.InvalidLogin as exp:
        _LOGGER.error("Failed to login. %s", exp)
        return False

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    # set up notify platform, no entry support for notify component yet,
    # have to use discovery to load platform.
    opp.async_create_task(
        discovery.async_load_platform(
            opp, "notify", DOMAIN, {CONF_NAME: DOMAIN}, opp.data[DATA_OPP_CONFIG]
        )
    )
    return True


async def async_unload_entry(opp, config_entry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(config_entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    if unload_ok:
        tibber_connection = opp.data.get(DOMAIN)
        await tibber_connection.rt_disconnect()

    return unload_ok
