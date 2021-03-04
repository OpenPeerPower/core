"""Support for Spider Smart devices."""
import asyncio
import logging

from spiderpy.spiderapi import SpiderApi, SpiderApiException, UnauthorizedException
import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT
from openpeerpower.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from openpeerpower.exceptions import ConfigEntryNotReady
import openpeerpower.helpers.config_validation as cv

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_USERNAME): cv.string,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): cv.time_period,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Set up a config entry."""
    opp.data[DOMAIN] = {}
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]

    if not opp.config_entries.async_entries(DOMAIN):
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=conf
            )
        )

    return True


async def async_setup_entry(opp, entry):
    """Set up Spider via config entry."""
    try:
        api = await opp.async_add_executor_job(
            SpiderApi,
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
            entry.data[CONF_SCAN_INTERVAL],
        )
    except UnauthorizedException:
        _LOGGER.error("Authorization failed")
        return False
    except SpiderApiException as err:
        _LOGGER.error("Can't connect to the Spider API: %s", err)
        raise ConfigEntryNotReady from err

    opp.data[DOMAIN][entry.entry_id] = api

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(opp, entry):
    """Unload Spider entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    if not unload_ok:
        return False

    opp.data[DOMAIN].pop(entry.entry_id)

    return True
