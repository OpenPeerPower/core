"""The ATAG Integration."""
from datetime import timedelta
import logging

import async_timeout
from pyatag import AtagException, AtagOne

from openpeerpower.components.climate import DOMAIN as CLIMATE
from openpeerpower.components.sensor import DOMAIN as SENSOR
from openpeerpower.components.water_heater import DOMAIN as WATER_HEATER
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower, asyncio
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "atag"
PLATFORMS = [CLIMATE, WATER_HEATER, SENSOR]


async def async_setup(opp: OpenPeerPower, config):
    """Set up the Atag component."""
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Atag integration from a config entry."""
    session = async_get_clientsession(opp)

    coordinator = AtagDataUpdateCoordinator(opp, session, entry)
    await coordinator.async_refresh()
    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = coordinator
    if entry.unique_id is None:
        opp.config_entries.async_update_entry(entry, unique_id=coordinator.atag.id)

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


class AtagDataUpdateCoordinator(DataUpdateCoordinator):
    """Define an object to hold Atag data."""

    def __init__(self, opp, session, entry):
        """Initialize."""
        self.atag = AtagOne(session=session, **entry.data)

        super().__init__(
            opp, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=30)
        )

    async def _async_update_data(self):
        """Update data via library."""
        with async_timeout.timeout(20):
            try:
                if not await self.atag.update():
                    raise UpdateFailed("No data received")
            except AtagException as error:
                raise UpdateFailed(error) from error
        return self.atag.report


async def async_unload_entry(opp, entry):
    """Unload Atag config entry."""
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


class AtagEntity(CoordinatorEntity):
    """Defines a base Atag entity."""

    def __init__(self, coordinator: AtagDataUpdateCoordinator, atag_id: str) -> None:
        """Initialize the Atag entity."""
        super().__init__(coordinator)

        self._id = atag_id
        self._name = DOMAIN.title()

    @property
    def device_info(self) -> dict:
        """Return info for device registry."""
        device = self.coordinator.atag.id
        version = self.coordinator.atag.apiversion
        return {
            "identifiers": {(DOMAIN, device)},
            "name": "Atag Thermostat",
            "model": "Atag One",
            "sw_version": version,
            "manufacturer": "Atag",
        }

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{self.coordinator.atag.id}-{self._id}"
