"""Support for the Brother service."""
from __future__ import annotations

from typing import Any

from openpeerpower.components.sensor import SensorEntity
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import ATTR_ICON, DEVICE_CLASS_TIMESTAMP
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.entity import DeviceInfo
from openpeerpower.helpers.entity_platform import AddEntitiesCallback
from openpeerpower.helpers.update_coordinator import CoordinatorEntity

from . import BrotherDataUpdateCoordinator
from .const import (
    ATTR_COUNTER,
    ATTR_ENABLED,
    ATTR_LABEL,
    ATTR_MANUFACTURER,
    ATTR_REMAINING_PAGES,
    ATTR_UNIT,
    ATTR_UPTIME,
    ATTRS_MAP,
    DATA_CONFIG_ENTRY,
    DOMAIN,
    SENSOR_TYPES,
)


async def async_setup_entry(
    opp: OpenPeerPower, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add Brother entities from a config_entry."""
    coordinator = opp.data[DOMAIN][DATA_CONFIG_ENTRY][entry.entry_id]

    sensors = []

    device_info: DeviceInfo = {
        "identifiers": {(DOMAIN, coordinator.data.serial)},
        "name": coordinator.data.model,
        "manufacturer": ATTR_MANUFACTURER,
        "model": coordinator.data.model,
        "sw_version": getattr(coordinator.data, "firmware", None),
    }

    for sensor in SENSOR_TYPES:
        if sensor in coordinator.data:
            sensors.append(BrotherPrinterSensor(coordinator, sensor, device_info))
    async_add_entities(sensors, False)


class BrotherPrinterSensor(CoordinatorEntity, SensorEntity):
    """Define an Brother Printer sensor."""

    def __init__(
        self,
        coordinator: BrotherDataUpdateCoordinator,
        kind: str,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._description = SENSOR_TYPES[kind]
        self._name = f"{coordinator.data.model} {self._description[ATTR_LABEL]}"
        self._unique_id = f"{coordinator.data.serial.lower()}_{kind}"
        self._device_info = device_info
        self.kind = kind
        self._attrs: dict[str, Any] = {}

    @property
    def name(self) -> str:
        """Return the name."""
        return self._name

    @property
    def state(self) -> Any:
        """Return the state."""
        if self.kind == ATTR_UPTIME:
            return getattr(self.coordinator.data, self.kind).isoformat()
        return getattr(self.coordinator.data, self.kind)

    @property
    def device_class(self) -> str | None:
        """Return the class of this sensor."""
        if self.kind == ATTR_UPTIME:
            return DEVICE_CLASS_TIMESTAMP
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        remaining_pages, drum_counter = ATTRS_MAP.get(self.kind, (None, None))
        if remaining_pages and drum_counter:
            self._attrs[ATTR_REMAINING_PAGES] = getattr(
                self.coordinator.data, remaining_pages
            )
            self._attrs[ATTR_COUNTER] = getattr(self.coordinator.data, drum_counter)
        return self._attrs

    @property
    def icon(self) -> str | None:
        """Return the icon."""
        return self._description[ATTR_ICON]

    @property
    def unique_id(self) -> str:
        """Return a unique_id for this entity."""
        return self._unique_id

    @property
    def unit_of_measurement(self) -> str | None:
        """Return the unit the value is expressed in."""
        return self._description[ATTR_UNIT]

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return self._device_info

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return self._description[ATTR_ENABLED]
