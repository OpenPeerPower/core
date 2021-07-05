"""The ATAG Integration."""
from datetime import timedelta
import logging

import async_timeout
from pyatag import AtagException, AtagOne

from openpeerpower.components.climate import DOMAIN as CLIMATE
from openpeerpower.components.sensor import DOMAIN as SENSOR
from openpeerpower.components.water_heater import DOMAIN as WATER_HEATER
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.entity import DeviceInfo
from openpeerpower.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "atag"
PLATFORMS = [CLIMATE, WATER_HEATER, SENSOR]


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Atag integration from a config entry."""

    async def _async_update_data():
        """Update data via library."""
        with async_timeout.timeout(20):
            try:
                await atag.update()
            except AtagException as err:
                raise UpdateFailed(err) from err
        return atag

    atag = AtagOne(
        session=async_get_clientsession(opp), **entry.data, device=entry.unique_id
    )
    coordinator = DataUpdateCoordinator(
        opp,
        _LOGGER,
        name=DOMAIN.title(),
        update_method=_async_update_data,
        update_interval=timedelta(seconds=60),
    )

    await coordinator.async_config_entry_first_refresh()

    opp.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    if entry.unique_id is None:
        opp.config_entries.async_update_entry(entry, unique_id=atag.id)

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp, entry):
    """Unload Atag config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class AtagEntity(CoordinatorEntity):
    """Defines a base Atag entity."""

    def __init__(self, coordinator: DataUpdateCoordinator, atag_id: str) -> None:
        """Initialize the Atag entity."""
        super().__init__(coordinator)

        self._id = atag_id
        self._name = DOMAIN.title()

    @property
    def device_info(self) -> DeviceInfo:
        """Return info for device registry."""
        device = self.coordinator.data.id
        version = self.coordinator.data.apiversion
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
        return f"{self.coordinator.data.id}-{self._id}"
