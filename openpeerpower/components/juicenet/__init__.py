"""The JuiceNet integration."""
import asyncio
from datetime import timedelta
import logging

import aiohttp
from pyjuicenet import Api, TokenError
import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT, ConfigEntry
from openpeerpower.const import CONF_ACCESS_TOKEN
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, JUICENET_API, JUICENET_COORDINATOR
from .device import JuiceNetApi

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "switch"]

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_ACCESS_TOKEN): cv.string})},
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the JuiceNet component."""
    conf = config.get(DOMAIN)
    opp.data.setdefault(DOMAIN, {})

    if not conf:
        return True

    opp.async_create_task(
        opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=conf
        )
    )
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up JuiceNet from a config entry."""

    config = entry.data

    session = async_get_clientsession(opp)

    access_token = config[CONF_ACCESS_TOKEN]
    api = Api(access_token, session)

    juicenet = JuiceNetApi(api)

    try:
        await juicenet.setup()
    except TokenError as error:
        _LOGGER.error("JuiceNet Error %s", error)
        return False
    except aiohttp.ClientError as error:
        _LOGGER.error("Could not reach the JuiceNet API %s", error)
        raise ConfigEntryNotReady from error

    if not juicenet.devices:
        _LOGGER.error("No JuiceNet devices found for this account")
        return False
    _LOGGER.info("%d JuiceNet device(s) found", len(juicenet.devices))

    async def async_update_data():
        """Update all device states from the JuiceNet API."""
        for device in juicenet.devices:
            await device.update_state(True)
        return True

    coordinator = DataUpdateCoordinator(
        opp,
        _LOGGER,
        name="JuiceNet",
        update_method=async_update_data,
        update_interval=timedelta(seconds=30),
    )

    opp.data[DOMAIN][entry.entry_id] = {
        JUICENET_API: juicenet,
        JUICENET_COORDINATOR: coordinator,
    }

    await coordinator.async_refresh()

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
