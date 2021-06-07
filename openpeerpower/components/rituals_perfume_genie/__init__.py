"""The Rituals Perfume Genie integration."""
from datetime import timedelta
import logging

import aiohttp
from pyrituals import Account, Diffuser

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator

from .const import ACCOUNT_HASH, COORDINATORS, DEVICES, DOMAIN, HUBLOT

PLATFORMS = ["binary_sensor", "sensor", "switch"]

EMPTY_CREDENTIALS = ""

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up Rituals Perfume Genie from a config entry."""
    session = async_get_clientsession(opp)
    account = Account(EMPTY_CREDENTIALS, EMPTY_CREDENTIALS, session)
    account.data = {ACCOUNT_HASH: entry.data.get(ACCOUNT_HASH)}

    try:
        account_devices = await account.get_devices()
    except aiohttp.ClientError as err:
        raise ConfigEntryNotReady from err

    opp.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        COORDINATORS: {},
        DEVICES: {},
    }

    for device in account_devices:
        hublot = device.hub_data[HUBLOT]

        coordinator = RitualsDataUpdateCoordinator(opp, device)
        await coordinator.async_refresh()

        opp.data[DOMAIN][entry.entry_id][DEVICES][hublot] = device
        opp.data[DOMAIN][entry.entry_id][COORDINATORS][hublot] = coordinator

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class RitualsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Rituals Perufme Genie device data from single endpoint."""

    def __init__(self, opp: OpenPeerPower, device: Diffuser) -> None:
        """Initialize global Rituals Perufme Genie data updater."""
        self._device = device
        super().__init__(
            opp,
            _LOGGER,
            name=f"{DOMAIN}-{device.hub_data[HUBLOT]}",
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> None:
        """Fetch data from Rituals."""
        await self._device.update_data()
