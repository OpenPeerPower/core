"""Binary sensors for the Elexa Guardian integration."""
from typing import Callable, Dict, Optional

from openpeerpower.components.binary_sensor import (
    DEVICE_CLASS_CONNECTIVITY,
    DEVICE_CLASS_MOISTURE,
    DEVICE_CLASS_MOVING,
    BinarySensorEntity,
)
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers.dispatcher import async_dispatcher_connect
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator

from . import PairedSensorEntity, ValveControllerEntity
from .const import (
    API_SENSOR_PAIRED_SENSOR_STATUS,
    API_SYSTEM_ONBOARD_SENSOR_STATUS,
    API_WIFI_STATUS,
    CONF_UID,
    DATA_COORDINATOR,
    DATA_UNSUB_DISPATCHER_CONNECT,
    DOMAIN,
    SIGNAL_PAIRED_SENSOR_COORDINATOR_ADDED,
)

ATTR_CONNECTED_CLIENTS = "connected_clients"

SENSOR_KIND_AP_INFO = "ap_enabled"
SENSOR_KIND_LEAK_DETECTED = "leak_detected"
SENSOR_KIND_MOVED = "moved"

SENSOR_ATTRS_MAP = {
    SENSOR_KIND_AP_INFO: ("Onboard AP Enabled", DEVICE_CLASS_CONNECTIVITY),
    SENSOR_KIND_LEAK_DETECTED: ("Leak Detected", DEVICE_CLASS_MOISTURE),
    SENSOR_KIND_MOVED: ("Recently Moved", DEVICE_CLASS_MOVING),
}

PAIRED_SENSOR_SENSORS = [SENSOR_KIND_LEAK_DETECTED, SENSOR_KIND_MOVED]
VALVE_CONTROLLER_SENSORS = [SENSOR_KIND_AP_INFO, SENSOR_KIND_LEAK_DETECTED]


async def async_setup_entry(
    opp: OpenPeerPower, entry: ConfigEntry, async_add_entities: Callable
) -> None:
    """Set up Guardian switches based on a config entry."""

    @callback
    def add_new_paired_sensor(uid: str) -> None:
        """Add a new paired sensor."""
        coordinator = opp.data[DOMAIN][DATA_COORDINATOR][entry.entry_id][
            API_SENSOR_PAIRED_SENSOR_STATUS
        ][uid]

        entities = []
        for kind in PAIRED_SENSOR_SENSORS:
            name, device_class = SENSOR_ATTRS_MAP[kind]
            entities.append(
                PairedSensorBinarySensor(
                    entry,
                    coordinator,
                    kind,
                    name,
                    device_class,
                    None,
                )
            )

        async_add_entities(entities)

    # Handle adding paired sensors after OPP startup:
    opp.data[DOMAIN][DATA_UNSUB_DISPATCHER_CONNECT][entry.entry_id].append(
        async_dispatcher_connect(
            opp,
            SIGNAL_PAIRED_SENSOR_COORDINATOR_ADDED.format(entry.data[CONF_UID]),
            add_new_paired_sensor,
        )
    )

    sensors = []

    # Add all valve controller-specific binary sensors:
    for kind in VALVE_CONTROLLER_SENSORS:
        name, device_class = SENSOR_ATTRS_MAP[kind]
        sensors.append(
            ValveControllerBinarySensor(
                entry,
                opp.data[DOMAIN][DATA_COORDINATOR][entry.entry_id],
                kind,
                name,
                device_class,
                None,
            )
        )

    # Add all paired sensor-specific binary sensors:
    for coordinator in opp.data[DOMAIN][DATA_COORDINATOR][entry.entry_id][
        API_SENSOR_PAIRED_SENSOR_STATUS
    ].values():
        for kind in PAIRED_SENSOR_SENSORS:
            name, device_class = SENSOR_ATTRS_MAP[kind]
            sensors.append(
                PairedSensorBinarySensor(
                    entry,
                    coordinator,
                    kind,
                    name,
                    device_class,
                    None,
                )
            )

    async_add_entities(sensors)


class PairedSensorBinarySensor(PairedSensorEntity, BinarySensorEntity):
    """Define a binary sensor related to a Guardian valve controller."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        kind: str,
        name: str,
        device_class: Optional[str],
        icon: Optional[str],
    ) -> None:
        """Initialize."""
        super().__init__(entry, coordinator, kind, name, device_class, icon)

        self._is_on = True

    @property
    def available(self) -> bool:
        """Return whether the entity is available."""
        return self.coordinator.last_update_success

    @property
    def is_on(self) -> bool:
        """Return True if the binary sensor is on."""
        return self._is_on

    @callback
    def _async_update_from_latest_data(self) -> None:
        """Update the entity."""
        if self._kind == SENSOR_KIND_LEAK_DETECTED:
            self._is_on = self.coordinator.data["wet"]
        elif self._kind == SENSOR_KIND_MOVED:
            self._is_on = self.coordinator.data["moved"]


class ValveControllerBinarySensor(ValveControllerEntity, BinarySensorEntity):
    """Define a binary sensor related to a Guardian valve controller."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinators: Dict[str, DataUpdateCoordinator],
        kind: str,
        name: str,
        device_class: Optional[str],
        icon: Optional[str],
    ) -> None:
        """Initialize."""
        super().__init__(entry, coordinators, kind, name, device_class, icon)

        self._is_on = True

    @property
    def available(self) -> bool:
        """Return whether the entity is available."""
        if self._kind == SENSOR_KIND_AP_INFO:
            return self.coordinators[API_WIFI_STATUS].last_update_success
        if self._kind == SENSOR_KIND_LEAK_DETECTED:
            return self.coordinators[
                API_SYSTEM_ONBOARD_SENSOR_STATUS
            ].last_update_success
        return False

    @property
    def is_on(self) -> bool:
        """Return True if the binary sensor is on."""
        return self._is_on

    async def _async_continue_entity_setup(self) -> None:
        """Add an API listener."""
        if self._kind == SENSOR_KIND_AP_INFO:
            self.async_add_coordinator_update_listener(API_WIFI_STATUS)
        elif self._kind == SENSOR_KIND_LEAK_DETECTED:
            self.async_add_coordinator_update_listener(API_SYSTEM_ONBOARD_SENSOR_STATUS)

    @callback
    def _async_update_from_latest_data(self) -> None:
        """Update the entity."""
        if self._kind == SENSOR_KIND_AP_INFO:
            self._is_on = self.coordinators[API_WIFI_STATUS].data["station_connected"]
            self._attrs.update(
                {
                    ATTR_CONNECTED_CLIENTS: self.coordinators[API_WIFI_STATUS].data.get(
                        "ap_clients"
                    )
                }
            )
        elif self._kind == SENSOR_KIND_LEAK_DETECTED:
            self._is_on = self.coordinators[API_SYSTEM_ONBOARD_SENSOR_STATUS].data[
                "wet"
            ]
