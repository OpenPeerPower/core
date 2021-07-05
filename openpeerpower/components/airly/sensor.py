"""Support for the Airly sensor service."""
from __future__ import annotations

from typing import Any, cast

from openpeerpower.components.sensor import SensorEntity
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import (
    ATTR_ATTRIBUTION,
    ATTR_DEVICE_CLASS,
    ATTR_ICON,
    CONF_NAME,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.entity import DeviceInfo
from openpeerpower.helpers.entity_platform import AddEntitiesCallback
from openpeerpower.helpers.typing import StateType
from openpeerpower.helpers.update_coordinator import CoordinatorEntity

from . import AirlyDataUpdateCoordinator
from .const import (
    ATTR_API_PM1,
    ATTR_API_PRESSURE,
    ATTR_LABEL,
    ATTR_UNIT,
    ATTRIBUTION,
    DEFAULT_NAME,
    DOMAIN,
    MANUFACTURER,
    SENSOR_TYPES,
)

PARALLEL_UPDATES = 1


async def async_setup_entry(
    opp: OpenPeerPower, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Airly sensor entities based on a config entry."""
    name = entry.data[CONF_NAME]

    coordinator = opp.data[DOMAIN][entry.entry_id]

    sensors = []
    for sensor in SENSOR_TYPES:
        # When we use the nearest method, we are not sure which sensors are available
        if coordinator.data.get(sensor):
            sensors.append(AirlySensor(coordinator, name, sensor))

    async_add_entities(sensors, False)


class AirlySensor(CoordinatorEntity, SensorEntity):
    """Define an Airly sensor."""

    coordinator: AirlyDataUpdateCoordinator

    def __init__(
        self, coordinator: AirlyDataUpdateCoordinator, name: str, kind: str
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._name = name
        self._description = SENSOR_TYPES[kind]
        self.kind = kind
        self._state = None
        self._unit_of_measurement = None
        self._attrs = {ATTR_ATTRIBUTION: ATTRIBUTION}

    @property
    def name(self) -> str:
        """Return the name."""
        return f"{self._name} {self._description[ATTR_LABEL]}"

    @property
    def state(self) -> StateType:
        """Return the state."""
        self._state = self.coordinator.data[self.kind]
        if self.kind in [ATTR_API_PM1, ATTR_API_PRESSURE]:
            return round(cast(float, self._state))
        return round(cast(float, self._state), 1)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return self._attrs

    @property
    def icon(self) -> str | None:
        """Return the icon."""
        return self._description[ATTR_ICON]

    @property
    def device_class(self) -> str | None:
        """Return the device_class."""
        return self._description[ATTR_DEVICE_CLASS]

    @property
    def unique_id(self) -> str:
        """Return a unique_id for this entity."""
        return f"{self.coordinator.latitude}-{self.coordinator.longitude}-{self.kind.lower()}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return {
            "identifiers": {
                (
                    DOMAIN,
                    f"{self.coordinator.latitude}-{self.coordinator.longitude}",
                )
            },
            "name": DEFAULT_NAME,
            "manufacturer": MANUFACTURER,
            "entry_type": "service",
        }

    @property
    def unit_of_measurement(self) -> str | None:
        """Return the unit the value is expressed in."""
        return self._description[ATTR_UNIT]
