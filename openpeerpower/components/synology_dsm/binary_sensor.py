"""Support for Synology DSM binary sensors."""
from __future__ import annotations

from openpeerpower.components.binary_sensor import BinarySensorEntity
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_DISKS
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.entity_platform import AddEntitiesCallback

from . import SynoApi, SynologyDSMBaseEntity, SynologyDSMDeviceEntity
from .const import (
    COORDINATOR_CENTRAL,
    DOMAIN,
    SECURITY_BINARY_SENSORS,
    STORAGE_DISK_BINARY_SENSORS,
    SYNO_API,
    UPGRADE_BINARY_SENSORS,
)


async def async_setup_entry(
    opp: OpenPeerPower, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Synology NAS binary sensor."""

    data = opp.data[DOMAIN][entry.unique_id]
    api: SynoApi = data[SYNO_API]
    coordinator = data[COORDINATOR_CENTRAL]

    entities: list[
        SynoDSMSecurityBinarySensor
        | SynoDSMUpgradeBinarySensor
        | SynoDSMStorageBinarySensor
    ] = [
        SynoDSMSecurityBinarySensor(
            api, sensor_type, SECURITY_BINARY_SENSORS[sensor_type], coordinator
        )
        for sensor_type in SECURITY_BINARY_SENSORS
    ]

    entities += [
        SynoDSMUpgradeBinarySensor(
            api, sensor_type, UPGRADE_BINARY_SENSORS[sensor_type], coordinator
        )
        for sensor_type in UPGRADE_BINARY_SENSORS
    ]

    # Handle all disks
    if api.storage.disks_ids:
        for disk in entry.data.get(CONF_DISKS, api.storage.disks_ids):
            entities += [
                SynoDSMStorageBinarySensor(
                    api,
                    sensor_type,
                    STORAGE_DISK_BINARY_SENSORS[sensor_type],
                    coordinator,
                    disk,
                )
                for sensor_type in STORAGE_DISK_BINARY_SENSORS
            ]

    async_add_entities(entities)


class SynoDSMSecurityBinarySensor(SynologyDSMBaseEntity, BinarySensorEntity):
    """Representation a Synology Security binary sensor."""

    @property
    def is_on(self) -> bool:
        """Return the state."""
        return getattr(self._api.security, self.entity_type) != "safe"  # type: ignore[no-any-return]

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return bool(self._api.security)

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return security checks details."""
        return self._api.security.status_by_check  # type: ignore[no-any-return]


class SynoDSMStorageBinarySensor(SynologyDSMDeviceEntity, BinarySensorEntity):
    """Representation a Synology Storage binary sensor."""

    @property
    def is_on(self) -> bool:
        """Return the state."""
        return bool(getattr(self._api.storage, self.entity_type)(self._device_id))


class SynoDSMUpgradeBinarySensor(SynologyDSMBaseEntity, BinarySensorEntity):
    """Representation a Synology Upgrade binary sensor."""

    @property
    def is_on(self) -> bool:
        """Return the state."""
        return bool(getattr(self._api.upgrade, self.entity_type))

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return bool(self._api.upgrade)
