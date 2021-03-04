"""The Internet Printing Protocol (IPP) integration."""
import asyncio
from datetime import timedelta
import logging
from typing import Any, Dict

from pyipp import IPP, IPPError, Printer as IPPPrinter

from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import (
    ATTR_NAME,
    CONF_HOST,
    CONF_PORT,
    CONF_SSL,
    CONF_VERIFY_SSL,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_SOFTWARE_VERSION,
    CONF_BASE_PATH,
    DOMAIN,
)

PLATFORMS = [SENSOR_DOMAIN]
SCAN_INTERVAL = timedelta(seconds=60)

_LOGGER = logging.getLogger(__name__)


async def async_setup(opp: OpenPeerPower, config: Dict) -> bool:
    """Set up the IPP component."""
    opp.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up IPP from a config entry."""

    coordinator = opp.data[DOMAIN].get(entry.entry_id)
    if not coordinator:
        # Create IPP instance for this entry
        coordinator = IPPDataUpdateCoordinator(
            opp,
            host=entry.data[CONF_HOST],
            port=entry.data[CONF_PORT],
            base_path=entry.data[CONF_BASE_PATH],
            tls=entry.data[CONF_SSL],
            verify_ssl=entry.data[CONF_VERIFY_SSL],
        )
        opp.data[DOMAIN][entry.entry_id] = coordinator

    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
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


class IPPDataUpdateCoordinator(DataUpdateCoordinator[IPPPrinter]):
    """Class to manage fetching IPP data from single endpoint."""

    def __init__(
        self,
        opp: OpenPeerPower,
        *,
        host: str,
        port: int,
        base_path: str,
        tls: bool,
        verify_ssl: bool,
    ):
        """Initialize global IPP data updater."""
        self.ipp = IPP(
            host=host,
            port=port,
            base_path=base_path,
            tls=tls,
            verify_ssl=verify_ssl,
            session=async_get_clientsession(opp, verify_ssl),
        )

        super().__init__(
            opp,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> IPPPrinter:
        """Fetch data from IPP."""
        try:
            return await self.ipp.printer()
        except IPPError as error:
            raise UpdateFailed(f"Invalid response from API: {error}") from error


class IPPEntity(CoordinatorEntity):
    """Defines a base IPP entity."""

    def __init__(
        self,
        *,
        entry_id: str,
        device_id: str,
        coordinator: IPPDataUpdateCoordinator,
        name: str,
        icon: str,
        enabled_default: bool = True,
    ) -> None:
        """Initialize the IPP entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._enabled_default = enabled_default
        self._entry_id = entry_id
        self._icon = icon
        self._name = name

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def icon(self) -> str:
        """Return the mdi icon of the entity."""
        return self._icon

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return self._enabled_default

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information about this IPP device."""
        if self._device_id is None:
            return None

        return {
            ATTR_IDENTIFIERS: {(DOMAIN, self._device_id)},
            ATTR_NAME: self.coordinator.data.info.name,
            ATTR_MANUFACTURER: self.coordinator.data.info.manufacturer,
            ATTR_MODEL: self.coordinator.data.info.model,
            ATTR_SOFTWARE_VERSION: self.coordinator.data.info.version,
        }
