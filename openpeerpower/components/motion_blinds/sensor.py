"""Support for Motion Blinds sensors."""
from motionblinds import BlindType

from openpeerpower.components.sensor import SensorEntity
from openpeerpower.const import (
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_SIGNAL_STRENGTH,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
)
from openpeerpower.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_AVAILABLE, DOMAIN, KEY_COORDINATOR, KEY_GATEWAY

ATTR_BATTERY_VOLTAGE = "battery_voltage"
TYPE_BLIND = "blind"
TYPE_GATEWAY = "gateway"


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Perform the setup for Motion Blinds."""
    entities = []
    motion_gateway = opp.data[DOMAIN][config_entry.entry_id][KEY_GATEWAY]
    coordinator = opp.data[DOMAIN][config_entry.entry_id][KEY_COORDINATOR]

    for blind in motion_gateway.device_list.values():
        entities.append(MotionSignalStrengthSensor(coordinator, blind, TYPE_BLIND))
        if blind.type == BlindType.TopDownBottomUp:
            entities.append(MotionTDBUBatterySensor(coordinator, blind, "Bottom"))
            entities.append(MotionTDBUBatterySensor(coordinator, blind, "Top"))
        elif blind.battery_voltage > 0:
            # Only add battery powered blinds
            entities.append(MotionBatterySensor(coordinator, blind))

    entities.append(
        MotionSignalStrengthSensor(coordinator, motion_gateway, TYPE_GATEWAY)
    )

    async_add_entities(entities)


class MotionBatterySensor(CoordinatorEntity, SensorEntity):
    """
    Representation of a Motion Battery Sensor.

    Updates are done by the cover platform.
    """

    def __init__(self, coordinator, blind):
        """Initialize the Motion Battery Sensor."""
        super().__init__(coordinator)

        self._blind = blind

    @property
    def unique_id(self):
        """Return the unique id of the blind."""
        return f"{self._blind.mac}-battery"

    @property
    def device_info(self):
        """Return the device info of the blind."""
        return {"identifiers": {(DOMAIN, self._blind.mac)}}

    @property
    def name(self):
        """Return the name of the blind battery sensor."""
        return f"{self._blind.blind_type}-battery-{self._blind.mac[12:]}"

    @property
    def available(self):
        """Return True if entity is available."""
        if self.coordinator.data is None:
            return False

        if not self.coordinator.data[KEY_GATEWAY][ATTR_AVAILABLE]:
            return False

        return self.coordinator.data[self._blind.mac][ATTR_AVAILABLE]

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return PERCENTAGE

    @property
    def device_class(self):
        """Return the device class of this entity."""
        return DEVICE_CLASS_BATTERY

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._blind.battery_level

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        return {ATTR_BATTERY_VOLTAGE: self._blind.battery_voltage}

    async def async_added_to_opp(self):
        """Subscribe to multicast pushes."""
        self._blind.Register_callback(self.unique_id, self.schedule_update_op_state)
        await super().async_added_to_opp()

    async def async_will_remove_from_opp(self):
        """Unsubscribe when removed."""
        self._blind.Remove_callback(self.unique_id)
        await super().async_will_remove_from_opp()


class MotionTDBUBatterySensor(MotionBatterySensor):
    """
    Representation of a Motion Battery Sensor for a Top Down Bottom Up blind.

    Updates are done by the cover platform.
    """

    def __init__(self, coordinator, blind, motor):
        """Initialize the Motion Battery Sensor."""
        super().__init__(coordinator, blind)

        self._motor = motor

    @property
    def unique_id(self):
        """Return the unique id of the blind."""
        return f"{self._blind.mac}-{self._motor}-battery"

    @property
    def name(self):
        """Return the name of the blind battery sensor."""
        return f"{self._blind.blind_type}-{self._motor}-battery-{self._blind.mac[12:]}"

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._blind.battery_level is None:
            return None
        return self._blind.battery_level[self._motor[0]]

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        attributes = {}
        if self._blind.battery_voltage is not None:
            attributes[ATTR_BATTERY_VOLTAGE] = self._blind.battery_voltage[
                self._motor[0]
            ]
        return attributes


class MotionSignalStrengthSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Motion Signal Strength Sensor."""

    def __init__(self, coordinator, device, device_type):
        """Initialize the Motion Signal Strength Sensor."""
        super().__init__(coordinator)

        self._device = device
        self._device_type = device_type

    @property
    def unique_id(self):
        """Return the unique id of the blind."""
        return f"{self._device.mac}-RSSI"

    @property
    def device_info(self):
        """Return the device info of the blind."""
        return {"identifiers": {(DOMAIN, self._device.mac)}}

    @property
    def name(self):
        """Return the name of the blind signal strength sensor."""
        if self._device_type == TYPE_GATEWAY:
            return "Motion gateway signal strength"
        return f"{self._device.blind_type} signal strength - {self._device.mac[12:]}"

    @property
    def available(self):
        """Return True if entity is available."""
        if self.coordinator.data is None:
            return False

        gateway_available = self.coordinator.data[KEY_GATEWAY][ATTR_AVAILABLE]
        if self._device_type == TYPE_GATEWAY:
            return gateway_available

        return (
            gateway_available
            and self.coordinator.data[self._device.mac][ATTR_AVAILABLE]
        )

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return SIGNAL_STRENGTH_DECIBELS_MILLIWATT

    @property
    def device_class(self):
        """Return the device class of this entity."""
        return DEVICE_CLASS_SIGNAL_STRENGTH

    @property
    def entity_registry_enabled_default(self):
        """Return if the entity should be enabled when first added to the entity registry."""
        return False

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._device.RSSI

    async def async_added_to_opp(self):
        """Subscribe to multicast pushes."""
        self._device.Register_callback(self.unique_id, self.schedule_update_op_state)
        await super().async_added_to_opp()

    async def async_will_remove_from_opp(self):
        """Unsubscribe when removed."""
        self._device.Remove_callback(self.unique_id)
        await super().async_will_remove_from_opp()
