"""Support for OVO Energy."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging

import aiohttp
import async_timeout
from ovoenergy import OVODailyUsage
from ovoenergy.ovoenergy import OVOEnergy

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from openpeerpower.helpers.entity import DeviceInfo
from openpeerpower.helpers.typing import ConfigType
from openpeerpower.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DATA_CLIENT, DATA_COORDINATOR, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up OVO Energy from a config entry."""

    client = OVOEnergy()

    try:
        authenticated = await client.authenticate(
            entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD]
        )
    except aiohttp.ClientError as exception:
        _LOGGER.warning(exception)
        raise ConfigEntryNotReady from exception

    if not authenticated:
        raise ConfigEntryAuthFailed

    async def async_update_data() -> OVODailyUsage:
        """Fetch data from OVO Energy."""
        async with async_timeout.timeout(10):
            try:
                authenticated = await client.authenticate(
                    entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD]
                )
            except aiohttp.ClientError as exception:
                raise UpdateFailed(exception) from exception
            if not authenticated:
                raise ConfigEntryAuthFailed("Not authenticated with OVO Energy")
            return await client.get_daily_usage(datetime.utcnow().strftime("%Y-%m"))

    coordinator = DataUpdateCoordinator(
        opp,
        _LOGGER,
        # Name of the data. For logging purposes.
        name="sensor",
        update_method=async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=timedelta(seconds=3600),
    )

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = {
        DATA_CLIENT: client,
        DATA_COORDINATOR: coordinator,
    }

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    # Setup components
    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigType) -> bool:
    """Unload OVO Energy config entry."""
    # Unload sensors
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)

    del opp.data[DOMAIN][entry.entry_id]

    return unload_ok


class OVOEnergyEntity(CoordinatorEntity):
    """Defines a base OVO Energy entity."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        client: OVOEnergy,
        key: str,
        name: str,
        icon: str,
    ) -> None:
        """Initialize the OVO Energy entity."""
        super().__init__(coordinator)
        self._client = client
        self._key = key
        self._name = name
        self._icon = icon
        self._available = True

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this sensor."""
        return self._key

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def icon(self) -> str:
        """Return the mdi icon of the entity."""
        return self._icon

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success and self._available


class OVOEnergyDeviceEntity(OVOEnergyEntity):
    """Defines a OVO Energy device entity."""

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this OVO Energy instance."""
        return {
            "identifiers": {(DOMAIN, self._client.account_id)},
            "manufacturer": "OVO Energy",
            "name": self._client.username,
            "entry_type": "service",
        }
