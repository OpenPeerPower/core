"""Support for Synology DSM sensors."""
from datetime import timedelta
from typing import Dict

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import (
    CONF_DISKS,
    DATA_MEGABYTES,
    DATA_RATE_KILOBYTES_PER_SECOND,
    DATA_TERABYTES,
    PRECISION_TENTHS,
    TEMP_CELSIUS,
)
from openpeerpower.helpers.temperature import display_temp
from openpeerpower.helpers.typing import OpenPeerPowerType
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator
from openpeerpower.util.dt import utcnow

from . import SynoApi, SynologyDSMBaseEntity, SynologyDSMDeviceEntity
from .const import (
    CONF_VOLUMES,
    COORDINATOR_CENTRAL,
    DOMAIN,
    ENTITY_UNIT_LOAD,
    INFORMATION_SENSORS,
    STORAGE_DISK_SENSORS,
    STORAGE_VOL_SENSORS,
    SYNO_API,
    TEMP_SENSORS_KEYS,
    UTILISATION_SENSORS,
)


async def async_setup_entry(
    opp: OpenPeerPowerType, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the Synology NAS Sensor."""

    data = opp.data[DOMAIN][entry.unique_id]
    api = data[SYNO_API]
    coordinator = data[COORDINATOR_CENTRAL]

    entities = [
        SynoDSMUtilSensor(
            api, sensor_type, UTILISATION_SENSORS[sensor_type], coordinator
        )
        for sensor_type in UTILISATION_SENSORS
    ]

    # Handle all volumes
    if api.storage.volumes_ids:
        for volume in entry.data.get(CONF_VOLUMES, api.storage.volumes_ids):
            entities += [
                SynoDSMStorageSensor(
                    api,
                    sensor_type,
                    STORAGE_VOL_SENSORS[sensor_type],
                    coordinator,
                    volume,
                )
                for sensor_type in STORAGE_VOL_SENSORS
            ]

    # Handle all disks
    if api.storage.disks_ids:
        for disk in entry.data.get(CONF_DISKS, api.storage.disks_ids):
            entities += [
                SynoDSMStorageSensor(
                    api,
                    sensor_type,
                    STORAGE_DISK_SENSORS[sensor_type],
                    coordinator,
                    disk,
                )
                for sensor_type in STORAGE_DISK_SENSORS
            ]

    entities += [
        SynoDSMInfoSensor(
            api, sensor_type, INFORMATION_SENSORS[sensor_type], coordinator
        )
        for sensor_type in INFORMATION_SENSORS
    ]

    async_add_entities(entities)


class SynoDSMUtilSensor(SynologyDSMBaseEntity):
    """Representation a Synology Utilisation sensor."""

    @property
    def state(self):
        """Return the state."""
        attr = getattr(self._api.utilisation, self.entity_type)
        if callable(attr):
            attr = attr()
        if attr is None:
            return None

        # Data (RAM)
        if self._unit == DATA_MEGABYTES:
            return round(attr / 1024.0 ** 2, 1)

        # Network
        if self._unit == DATA_RATE_KILOBYTES_PER_SECOND:
            return round(attr / 1024.0, 1)

        # CPU load average
        if self._unit == ENTITY_UNIT_LOAD:
            return round(attr / 100, 2)

        return attr

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return bool(self._api.utilisation)


class SynoDSMStorageSensor(SynologyDSMDeviceEntity):
    """Representation a Synology Storage sensor."""

    @property
    def state(self):
        """Return the state."""
        attr = getattr(self._api.storage, self.entity_type)(self._device_id)
        if attr is None:
            return None

        # Data (disk space)
        if self._unit == DATA_TERABYTES:
            return round(attr / 1024.0 ** 4, 2)

        # Temperature
        if self.entity_type in TEMP_SENSORS_KEYS:
            return display_temp(self.opp, attr, TEMP_CELSIUS, PRECISION_TENTHS)

        return attr


class SynoDSMInfoSensor(SynologyDSMBaseEntity):
    """Representation a Synology information sensor."""

    def __init__(
        self,
        api: SynoApi,
        entity_type: str,
        entity_info: Dict[str, str],
        coordinator: DataUpdateCoordinator,
    ):
        """Initialize the Synology SynoDSMInfoSensor entity."""
        super().__init__(api, entity_type, entity_info, coordinator)
        self._previous_uptime = None
        self._last_boot = None

    @property
    def state(self):
        """Return the state."""
        attr = getattr(self._api.information, self.entity_type)
        if attr is None:
            return None

        # Temperature
        if self.entity_type in TEMP_SENSORS_KEYS:
            return display_temp(self.opp, attr, TEMP_CELSIUS, PRECISION_TENTHS)

        if self.entity_type == "uptime":
            # reboot happened or entity creation
            if self._previous_uptime is None or self._previous_uptime > attr:
                last_boot = utcnow() - timedelta(seconds=attr)
                self._last_boot = last_boot.replace(microsecond=0).isoformat()

            self._previous_uptime = attr
            return self._last_boot
        return attr
