"""The Mullvad VPN integration."""
import asyncio
from datetime import timedelta
import logging

import async_timeout
from mullvad_api import MullvadAPI

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import update_coordinator

from .const import DOMAIN

PLATFORMS = ["binary_sensor"]


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the Mullvad VPN integration."""
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: dict):
    """Set up Mullvad VPN integration."""

    async def async_get_mullvad_api_data():
        with async_timeout.timeout(10):
            api = await opp.async_add_executor_job(MullvadAPI)
            return api.data

    coordinator = update_coordinator.DataUpdateCoordinator(
        opp,
        logging.getLogger(__name__),
        name=DOMAIN,
        update_method=async_get_mullvad_api_data,
        update_interval=timedelta(minutes=1),
    )
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    opp.data[DOMAIN] = coordinator

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
        del opp.data[DOMAIN]

    return unload_ok
