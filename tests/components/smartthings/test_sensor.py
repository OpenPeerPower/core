"""
Test for the SmartThings sensors platform.

The only mocking required is of the underlying SmartThings API object so
real HTTP calls are not initiated during testing.
"""
from pysmartthings import ATTRIBUTES, CAPABILITIES, Attribute, Capability

from openpeerpower.components.sensor import DEVICE_CLASSES, DOMAIN as SENSOR_DOMAIN
from openpeerpower.components.smartthings import sensor
from openpeerpower.components.smartthings.const import DOMAIN, SIGNAL_SMARTTHINGS_UPDATE
from openpeerpower.const import (
    ATTR_FRIENDLY_NAME,
    ATTR_UNIT_OF_MEASUREMENT,
    PERCENTAGE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from openpeerpowerr.helpers.dispatcher import async_dispatcher_send

from .conftest import setup_platform


async def test_mapping_integrity():
    """Test ensures the map dicts have proper integrity."""
    for capability, maps in sensor.CAPABILITY_TO_SENSORS.items():
        assert capability in CAPABILITIES, capability
        for sensor_map in maps:
            assert sensor_map.attribute in ATTRIBUTES, sensor_map.attribute
            if sensor_map.device_class:
                assert (
                    sensor_map.device_class in DEVICE_CLASSES
                ), sensor_map.device_class


async def test_entity_state.opp, device_factory):
    """Tests the state attributes properly match the sensor types."""
    device = device_factory("Sensor 1", [Capability.battery], {Attribute.battery: 100})
    await setup_platform.opp, SENSOR_DOMAIN, devices=[device])
    state = opp.states.get("sensor.sensor_1_battery")
    assert state.state == "100"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == PERCENTAGE
    assert state.attributes[ATTR_FRIENDLY_NAME] == f"{device.label} Battery"


async def test_entity_three_axis_state.opp, device_factory):
    """Tests the state attributes properly match the three axis types."""
    device = device_factory(
        "Three Axis", [Capability.three_axis], {Attribute.three_axis: [100, 75, 25]}
    )
    await setup_platform.opp, SENSOR_DOMAIN, devices=[device])
    state = opp.states.get("sensor.three_axis_x_coordinate")
    assert state.state == "100"
    assert state.attributes[ATTR_FRIENDLY_NAME] == f"{device.label} X Coordinate"
    state = opp.states.get("sensor.three_axis_y_coordinate")
    assert state.state == "75"
    assert state.attributes[ATTR_FRIENDLY_NAME] == f"{device.label} Y Coordinate"
    state = opp.states.get("sensor.three_axis_z_coordinate")
    assert state.state == "25"
    assert state.attributes[ATTR_FRIENDLY_NAME] == f"{device.label} Z Coordinate"


async def test_entity_three_axis_invalid_state.opp, device_factory):
    """Tests the state attributes properly match the three axis types."""
    device = device_factory(
        "Three Axis", [Capability.three_axis], {Attribute.three_axis: []}
    )
    await setup_platform.opp, SENSOR_DOMAIN, devices=[device])
    state = opp.states.get("sensor.three_axis_x_coordinate")
    assert state.state == STATE_UNKNOWN
    state = opp.states.get("sensor.three_axis_y_coordinate")
    assert state.state == STATE_UNKNOWN
    state = opp.states.get("sensor.three_axis_z_coordinate")
    assert state.state == STATE_UNKNOWN


async def test_entity_and_device_attributes.opp, device_factory):
    """Test the attributes of the entity are correct."""
    # Arrange
    device = device_factory("Sensor 1", [Capability.battery], {Attribute.battery: 100})
    entity_registry = await opp..helpers.entity_registry.async_get_registry()
    device_registry = await opp..helpers.device_registry.async_get_registry()
    # Act
    await setup_platform.opp, SENSOR_DOMAIN, devices=[device])
    # Assert
    entry = entity_registry.async_get("sensor.sensor_1_battery")
    assert entry
    assert entry.unique_id == f"{device.device_id}.{Attribute.battery}"
    entry = device_registry.async_get_device({(DOMAIN, device.device_id)})
    assert entry
    assert entry.name == device.label
    assert entry.model == device.device_type_name
    assert entry.manufacturer == "Unavailable"


async def test_update_from_signal.opp, device_factory):
    """Test the binary_sensor updates when receiving a signal."""
    # Arrange
    device = device_factory("Sensor 1", [Capability.battery], {Attribute.battery: 100})
    await setup_platform.opp, SENSOR_DOMAIN, devices=[device])
    device.status.apply_attribute_update(
        "main", Capability.battery, Attribute.battery, 75
    )
    # Act
    async_dispatcher_send.opp, SIGNAL_SMARTTHINGS_UPDATE, [device.device_id])
    # Assert
    await opp..async_block_till_done()
    state = opp.states.get("sensor.sensor_1_battery")
    assert state is not None
    assert state.state == "75"


async def test_unload_config_entry.opp, device_factory):
    """Test the binary_sensor is removed when the config entry is unloaded."""
    # Arrange
    device = device_factory("Sensor 1", [Capability.battery], {Attribute.battery: 100})
    config_entry = await setup_platform.opp, SENSOR_DOMAIN, devices=[device])
    # Act
    await opp..config_entries.async_forward_entry_unload(config_entry, "sensor")
    # Assert
    assert.opp.states.get("sensor.sensor_1_battery").state == STATE_UNAVAILABLE
