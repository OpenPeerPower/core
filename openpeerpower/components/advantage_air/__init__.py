"""Advantage Air climate integration."""

import asyncio
from datetime import timedelta
import logging

from advantage_air import ApiError, advantage_air

from openpeerpower.const import CONF_IP_ADDRESS, CONF_PORT
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import ADVANTAGE_AIR_RETRY, DOMAIN

ADVANTAGE_AIR_SYNC_INTERVAL = 15
PLATFORMS = ["climate", "cover", "binary_sensor", "sensor", "switch"]

_LOGGER = logging.getLogger(__name__)


async def async_setup(opp, config):
    """Set up Advantage Air integration."""
    opp.data[DOMAIN] = {}
    return True


async def async_setup_entry(opp, entry):
    """Set up Advantage Air config."""
    ip_address = entry.data[CONF_IP_ADDRESS]
    port = entry.data[CONF_PORT]
    api = advantage_air(
        ip_address,
        port=port,
        session=async_get_clientsession(opp),
        retry=ADVANTAGE_AIR_RETRY,
    )

    async def async_get():
        try:
            return await api.async_get()
        except ApiError as err:
            raise UpdateFailed(err) from err

    coordinator = DataUpdateCoordinator(
        opp,
        _LOGGER,
        name="Advantage Air",
        update_method=async_get,
        update_interval=timedelta(seconds=ADVANTAGE_AIR_SYNC_INTERVAL),
    )

    async def async_change(change):
        try:
            if await api.async_change(change):
                await coordinator.async_refresh()
        except ApiError as err:
            _LOGGER.warning(err)

    await coordinator.async_refresh()

    if not coordinator.data:
        raise ConfigEntryNotReady

    opp.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "async_change": async_change,
    }

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(opp, entry):
    """Unload Advantage Air Config."""
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
