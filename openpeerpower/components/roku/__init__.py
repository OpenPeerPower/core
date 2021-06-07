"""Support for Roku."""
from __future__ import annotations

from datetime import timedelta
import logging

from rokuecp import Roku, RokuConnectionError, RokuError
from rokuecp.models import Device

from openpeerpower.components.media_player import DOMAIN as MEDIA_PLAYER_DOMAIN
from openpeerpower.components.remote import DOMAIN as REMOTE_DOMAIN
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import ATTR_NAME, CONF_HOST
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.entity import DeviceInfo
from openpeerpower.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from openpeerpower.util.dt import utcnow

from .const import (
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_SOFTWARE_VERSION,
    ATTR_SUGGESTED_AREA,
    DOMAIN,
)

CONFIG_SCHEMA = cv.deprecated(DOMAIN)

PLATFORMS = [MEDIA_PLAYER_DOMAIN, REMOTE_DOMAIN]
SCAN_INTERVAL = timedelta(seconds=15)
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up Roku from a config entry."""
    opp.data.setdefault(DOMAIN, {})
    coordinator = opp.data[DOMAIN].get(entry.entry_id)
    if not coordinator:
        coordinator = RokuDataUpdateCoordinator(opp, host=entry.data[CONF_HOST])
        opp.data[DOMAIN][entry.entry_id] = coordinator

    await coordinator.async_config_entry_first_refresh()

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


def roku_exception_handler(func):
    """Decorate Roku calls to handle Roku exceptions."""

    async def handler(self, *args, **kwargs):
        try:
            await func(self, *args, **kwargs)
        except RokuConnectionError as error:
            if self.available:
                _LOGGER.error("Error communicating with API: %s", error)
        except RokuError as error:
            if self.available:
                _LOGGER.error("Invalid response from API: %s", error)

    return handler


class RokuDataUpdateCoordinator(DataUpdateCoordinator[Device]):
    """Class to manage fetching Roku data."""

    def __init__(
        self,
        opp: OpenPeerPower,
        *,
        host: str,
    ) -> None:
        """Initialize global Roku data updater."""
        self.roku = Roku(host=host, session=async_get_clientsession(opp))

        self.full_update_interval = timedelta(minutes=15)
        self.last_full_update = None

        super().__init__(
            opp,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> Device:
        """Fetch data from Roku."""
        full_update = self.last_full_update is None or utcnow() >= (
            self.last_full_update + self.full_update_interval
        )

        try:
            data = await self.roku.update(full_update=full_update)

            if full_update:
                self.last_full_update = utcnow()

            return data
        except RokuError as error:
            raise UpdateFailed(f"Invalid response from API: {error}") from error


class RokuEntity(CoordinatorEntity):
    """Defines a base Roku entity."""

    def __init__(
        self, *, device_id: str, name: str, coordinator: RokuDataUpdateCoordinator
    ) -> None:
        """Initialize the Roku entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._name = name

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Roku device."""
        if self._device_id is None:
            return None

        return {
            ATTR_IDENTIFIERS: {(DOMAIN, self._device_id)},
            ATTR_NAME: self.name,
            ATTR_MANUFACTURER: self.coordinator.data.info.brand,
            ATTR_MODEL: self.coordinator.data.info.model_name,
            ATTR_SOFTWARE_VERSION: self.coordinator.data.info.version,
            ATTR_SUGGESTED_AREA: self.coordinator.data.info.device_location,
        }
