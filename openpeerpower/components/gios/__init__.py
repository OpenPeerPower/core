"""The GIOS component."""
from __future__ import annotations

import logging
from typing import Any, Dict, cast

from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientConnectorError
from async_timeout import timeout
from gios import ApiError, Gios, InvalidSensorsData, NoStationError

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.device_registry import async_get_registry
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_TIMEOUT, CONF_STATION_ID, DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["air_quality"]


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up GIOS as config entry."""
    station_id: int = entry.data[CONF_STATION_ID]
    _LOGGER.debug("Using station_id: %d", station_id)

    # We used to use int as config_entry unique_id, convert this to str.
    if isinstance(entry.unique_id, int):  # type: ignore[unreachable]
        opp.config_entries.async_update_entry(entry, unique_id=str(station_id))  # type: ignore[unreachable]

    # We used to use int in device_entry identifiers, convert this to str.
    device_registry = await async_get_registry(opp)
    old_ids = (DOMAIN, station_id)
    device_entry = device_registry.async_get_device({old_ids})  # type: ignore[arg-type]
    if device_entry and entry.entry_id in device_entry.config_entries:
        new_ids = (DOMAIN, str(station_id))
        device_registry.async_update_device(device_entry.id, new_identifiers={new_ids})

    websession = async_get_clientsession(opp)

    coordinator = GiosDataUpdateCoordinator(opp, websession, station_id)
    await coordinator.async_config_entry_first_refresh()

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = coordinator

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class GiosDataUpdateCoordinator(DataUpdateCoordinator):
    """Define an object to hold GIOS data."""

    def __init__(
        self, opp: OpenPeerPower, session: ClientSession, station_id: int
    ) -> None:
        """Class to manage fetching GIOS data API."""
        self.gios = Gios(station_id, session)

        super().__init__(opp, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            with timeout(API_TIMEOUT):
                return cast(Dict[str, Any], await self.gios.async_update())
        except (
            ApiError,
            NoStationError,
            ClientConnectorError,
            InvalidSensorsData,
        ) as error:
            raise UpdateFailed(error) from error
