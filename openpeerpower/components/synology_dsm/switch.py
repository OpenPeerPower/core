"""Support for Synology DSM switch."""
from __future__ import annotations

import logging
from typing import Any

from synology_dsm.api.surveillance_station import SynoSurveillanceStation

from openpeerpower.components.switch import ToggleEntity
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.entity import DeviceInfo
from openpeerpower.helpers.entity_platform import AddEntitiesCallback
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator

from . import SynoApi, SynologyDSMBaseEntity
from .const import (
    COORDINATOR_SWITCHES,
    DOMAIN,
    SURVEILLANCE_SWITCH,
    SYNO_API,
    EntityInfo,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    opp: OpenPeerPower, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Synology NAS switch."""

    data = opp.data[DOMAIN][entry.unique_id]
    api: SynoApi = data[SYNO_API]

    entities = []

    if SynoSurveillanceStation.INFO_API_KEY in api.dsm.apis:
        info = await opp.async_add_executor_job(api.dsm.surveillance_station.get_info)
        version = info["data"]["CMSMinVersion"]

        # initial data fetch
        coordinator: DataUpdateCoordinator = data[COORDINATOR_SWITCHES]
        await coordinator.async_refresh()
        entities += [
            SynoDSMSurveillanceHomeModeToggle(
                api, sensor_type, SURVEILLANCE_SWITCH[sensor_type], version, coordinator
            )
            for sensor_type in SURVEILLANCE_SWITCH
        ]

    async_add_entities(entities, True)


class SynoDSMSurveillanceHomeModeToggle(SynologyDSMBaseEntity, ToggleEntity):
    """Representation a Synology Surveillance Station Home Mode toggle."""

    coordinator: DataUpdateCoordinator[dict[str, dict[str, bool]]]

    def __init__(
        self,
        api: SynoApi,
        entity_type: str,
        entity_info: EntityInfo,
        version: str,
        coordinator: DataUpdateCoordinator[dict[str, dict[str, bool]]],
    ) -> None:
        """Initialize a Synology Surveillance Station Home Mode."""
        super().__init__(
            api,
            entity_type,
            entity_info,
            coordinator,
        )
        self._version = version

    @property
    def is_on(self) -> bool:
        """Return the state."""
        return self.coordinator.data["switches"][self.entity_type]

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on Home mode."""
        _LOGGER.debug(
            "SynoDSMSurveillanceHomeModeToggle.turn_on(%s)",
            self._api.information.serial,
        )
        await self.opp.async_add_executor_job(
            self._api.dsm.surveillance_station.set_home_mode, True
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off Home mode."""
        _LOGGER.debug(
            "SynoDSMSurveillanceHomeModeToggle.turn_off(%s)",
            self._api.information.serial,
        )
        await self.opp.async_add_executor_job(
            self._api.dsm.surveillance_station.set_home_mode, False
        )
        await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return bool(self._api.surveillance_station)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information."""
        return {
            "identifiers": {
                (
                    DOMAIN,
                    f"{self._api.information.serial}_{SynoSurveillanceStation.INFO_API_KEY}",
                )
            },
            "name": "Surveillance Station",
            "manufacturer": "Synology",
            "model": self._api.information.model,
            "sw_version": self._version,
            "via_device": (DOMAIN, self._api.information.serial),
        }
