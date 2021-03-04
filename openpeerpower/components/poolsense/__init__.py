"""The PoolSense integration."""
import asyncio
from datetime import timedelta
import logging

import async_timeout
from poolsense import PoolSense
from poolsense.exceptions import PoolSenseError

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_EMAIL, CONF_PASSWORD
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import aiohttp_client
from openpeerpower.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN

PLATFORMS = ["sensor", "binary_sensor"]


_LOGGER = logging.getLogger(__name__)


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the PoolSense component."""
    # Make sure coordinator is initialized.
    opp.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up PoolSense from a config entry."""

    poolsense = PoolSense(
        aiohttp_client.async_get_clientsession(opp),
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
    )
    auth_valid = await poolsense.test_poolsense_credentials()

    if not auth_valid:
        _LOGGER.error("Invalid authentication")
        return False

    coordinator = PoolSenseDataUpdateCoordinator(opp, entry)

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


class PoolSenseEntity(CoordinatorEntity):
    """Implements a common class elements representing the PoolSense component."""

    def __init__(self, coordinator, email, info_type):
        """Initialize poolsense sensor."""
        super().__init__(coordinator)
        self._unique_id = f"{email}-{info_type}"
        self.info_type = info_type

    @property
    def unique_id(self):
        """Return a unique id."""
        return self._unique_id


class PoolSenseDataUpdateCoordinator(DataUpdateCoordinator):
    """Define an object to hold PoolSense data."""

    def __init__(self, opp, entry):
        """Initialize."""
        self.poolsense = PoolSense(
            aiohttp_client.async_get_clientsession(opp),
            entry.data[CONF_EMAIL],
            entry.data[CONF_PASSWORD],
        )
        self.opp = opp
        self.entry = entry

        super().__init__(opp, _LOGGER, name=DOMAIN, update_interval=timedelta(hours=1))

    async def _async_update_data(self):
        """Update data via library."""
        data = {}
        with async_timeout.timeout(10):
            try:
                data = await self.poolsense.get_poolsense_data()
            except (PoolSenseError) as error:
                _LOGGER.error("PoolSense query did not complete.")
                raise UpdateFailed(error) from error

        return data
