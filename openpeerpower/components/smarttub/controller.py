"""Interface to the SmartTub API."""

import asyncio
from datetime import timedelta
import logging

from aiohttp import client_exceptions
import async_timeout
from smarttub import APIError, LoginFailed, SmartTub
from smarttub.api import Account

from openpeerpower.const import CONF_EMAIL, CONF_PASSWORD
from openpeerpowerr.exceptions import ConfigEntryNotReady
from openpeerpowerr.helpers import device_registry as dr
from openpeerpowerr.helpers.aiohttp_client import async_get_clientsession
from openpeerpowerr.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, POLLING_TIMEOUT, SCAN_INTERVAL
from .helpers import get_spa_name

_LOGGER = logging.getLogger(__name__)


class SmartTubController:
    """Interface between Open Peer Power and the SmartTub API."""

    def __init__(self,.opp):
        """Initialize an interface to SmartTub."""
        self._opp =.opp
        self._account = None
        self.spas = set()
        self._spa_devices = {}

        self.coordinator = None

    async def async_setup_entry(self, entry):
        """Perform initial setup.

        Authenticate, query static state, set up polling, and otherwise make
        ready for normal operations .
        """

        try:
            self._account = await self.login(
                entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD]
            )
        except LoginFailed:
            # credentials were changed or invalidated, we need new ones

            return False
        except (
            asyncio.TimeoutError,
            client_exceptions.ClientOSError,
            client_exceptions.ServerDisconnectedError,
            client_exceptions.ContentTypeError,
        ) as err:
            raise ConfigEntryNotReady from err

        self.spas = await self._account.get_spas()

        self.coordinator = DataUpdateCoordinator(
            self._opp,
            _LOGGER,
            name=DOMAIN,
            update_method=self.async_update_data,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

        await self.coordinator.async_refresh()

        await self.async_register_devices(entry)

        return True

    async def async_update_data(self):
        """Query the API and return the new state."""

        data = {}
        try:
            async with async_timeout.timeout(POLLING_TIMEOUT):
                for spa in self.spas:
                    data[spa.id] = {"status": await spa.get_status()}
        except APIError as err:
            raise UpdateFailed(err) from err

        return data

    async def async_register_devices(self, entry):
        """Register devices with the device registry for all spas."""
        device_registry = await dr.async_get_registry(self._opp)
        for spa in self.spas:
            device = device_registry.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={(DOMAIN, spa.id)},
                manufacturer=spa.brand,
                name=get_spa_name(spa),
                model=spa.model,
            )
            self._spa_devices[spa.id] = device

    async def login(self, email, password) -> Account:
        """Retrieve the account corresponding to the specified email and password.

        Returns None if the credentials are invalid.
        """

        api = SmartTub(async_get_clientsession(self._opp))

        await api.login(email, password)
        return await api.get_account()
