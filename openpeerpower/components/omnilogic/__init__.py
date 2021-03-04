"""The Omnilogic integration."""
import asyncio
import logging

from omnilogic import LoginException, OmniLogic, OmniLogicException

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import aiohttp_client

from .common import OmniLogicUpdateCoordinator
from .const import CONF_SCAN_INTERVAL, COORDINATOR, DOMAIN, OMNI_API

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the Omnilogic component."""
    opp.data.setdefault(DOMAIN, {})

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Omnilogic from a config entry."""

    conf = entry.data
    username = conf[CONF_USERNAME]
    password = conf[CONF_PASSWORD]

    polling_interval = 6
    if CONF_SCAN_INTERVAL in conf:
        polling_interval = conf[CONF_SCAN_INTERVAL]

    session = aiohttp_client.async_get_clientsession(opp)

    api = OmniLogic(username, password, session)

    try:
        await api.connect()
        await api.get_telemetry_data()
    except LoginException as error:
        _LOGGER.error("Login Failed: %s", error)
        return False
    except OmniLogicException as error:
        _LOGGER.debug("OmniLogic API error: %s", error)
        raise ConfigEntryNotReady from error

    coordinator = OmniLogicUpdateCoordinator(
        opp=opp,
        api=api,
        name="Omnilogic",
        polling_interval=polling_interval,
    )
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    opp.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: coordinator,
        OMNI_API: api,
    }

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
