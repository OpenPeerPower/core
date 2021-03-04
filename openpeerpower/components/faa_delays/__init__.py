"""The FAA Delays integration."""
import asyncio
from datetime import timedelta
import logging

from aiohttp import ClientConnectionError
from async_timeout import timeout
from faadelays import Airport

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_ID
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import aiohttp_client
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["binary_sensor"]


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the FAA Delays component."""
    opp.data[DOMAIN] = {}
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up FAA Delays from a config entry."""
    code = entry.data[CONF_ID]

    coordinator = FAADataUpdateCoordinator(opp, code)
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    opp.data[DOMAIN][entry.entry_id] = coordinator

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


class FAADataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching FAA API data from a single endpoint."""

    def __init__(self, opp, code):
        """Initialize the coordinator."""
        super().__init__(
            opp, _LOGGER, name=DOMAIN, update_interval=timedelta(minutes=1)
        )
        self.session = aiohttp_client.async_get_clientsession(opp)
        self.data = Airport(code, self.session)
        self.code = code

    async def _async_update_data(self):
        try:
            with timeout(10):
                await self.data.update()
        except ClientConnectionError as err:
            raise UpdateFailed(err) from err
        return self.data
