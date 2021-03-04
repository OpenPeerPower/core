"""Support for WLED."""
import asyncio
from datetime import timedelta
import logging
from typing import Any, Dict

from wled import WLED, Device as WLEDDevice, WLEDConnectionError, WLEDError

from openpeerpower.components.light import DOMAIN as LIGHT_DOMAIN
from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.components.switch import DOMAIN as SWITCH_DOMAIN
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import ATTR_NAME, CONF_HOST
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.typing import ConfigType
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
    DOMAIN,
)

SCAN_INTERVAL = timedelta(seconds=5)
PLATFORMS = (LIGHT_DOMAIN, SENSOR_DOMAIN, SWITCH_DOMAIN)

_LOGGER = logging.getLogger(__name__)


async def async_setup(opp: OpenPeerPower, config: ConfigType) -> bool:
    """Set up the WLED components."""
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up WLED from a config entry."""

    # Create WLED instance for this entry
    coordinator = WLEDDataUpdateCoordinator(opp, host=entry.data[CONF_HOST])
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = coordinator

    # For backwards compat, set unique ID
    if entry.unique_id is None:
        opp.config_entries.async_update_entry(
            entry, unique_id=coordinator.data.info.mac_address
        )

    # Set up all platforms for this device/entry.
    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload WLED config entry."""

    # Unload entities for this entry/device.
    unload_ok = all(
        await asyncio.gather(
            *(
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            )
        )
    )

    if unload_ok:
        del opp.data[DOMAIN][entry.entry_id]

    if not opp.data[DOMAIN]:
        del opp.data[DOMAIN]

    return unload_ok


def wled_exception_handler(func):
    """Decorate WLED calls to handle WLED exceptions.

    A decorator that wraps the passed in function, catches WLED errors,
    and handles the availability of the device in the data coordinator.
    """

    async def handler(self, *args, **kwargs):
        try:
            await func(self, *args, **kwargs)
            self.coordinator.update_listeners()

        except WLEDConnectionError as error:
            _LOGGER.error("Error communicating with API: %s", error)
            self.coordinator.last_update_success = False
            self.coordinator.update_listeners()

        except WLEDError as error:
            _LOGGER.error("Invalid response from API: %s", error)

    return handler


class WLEDDataUpdateCoordinator(DataUpdateCoordinator[WLEDDevice]):
    """Class to manage fetching WLED data from single endpoint."""

    def __init__(
        self,
        opp: OpenPeerPower,
        *,
        host: str,
    ):
        """Initialize global WLED data updater."""
        self.wled = WLED(host, session=async_get_clientsession(opp))

        super().__init__(
            opp,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    def update_listeners(self) -> None:
        """Call update on all listeners."""
        for update_callback in self._listeners:
            update_callback()

    async def _async_update_data(self) -> WLEDDevice:
        """Fetch data from WLED."""
        try:
            return await self.wled.update(full_update=not self.last_update_success)
        except WLEDError as error:
            raise UpdateFailed(f"Invalid response from API: {error}") from error


class WLEDEntity(CoordinatorEntity):
    """Defines a base WLED entity."""

    def __init__(
        self,
        *,
        entry_id: str,
        coordinator: WLEDDataUpdateCoordinator,
        name: str,
        icon: str,
        enabled_default: bool = True,
    ) -> None:
        """Initialize the WLED entity."""
        super().__init__(coordinator)
        self._enabled_default = enabled_default
        self._entry_id = entry_id
        self._icon = icon
        self._name = name
        self._unsub_dispatcher = None

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


class WLEDDeviceEntity(WLEDEntity):
    """Defines a WLED device entity."""

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information about this WLED device."""
        return {
            ATTR_IDENTIFIERS: {(DOMAIN, self.coordinator.data.info.mac_address)},
            ATTR_NAME: self.coordinator.data.info.name,
            ATTR_MANUFACTURER: self.coordinator.data.info.brand,
            ATTR_MODEL: self.coordinator.data.info.product,
            ATTR_SOFTWARE_VERSION: self.coordinator.data.info.version,
        }
