"""
Test for the SmartThings binary_sensor platform.

The only mocking required is of the underlying SmartThings API object so
real HTTP calls are not initiated during testing.
"""
from pysmartthings import ATTRIBUTES, CAPABILITIES, Attribute, Capability

from openpeerpower.components.binary_sensor import (
    DEVICE_CLASSES,
    DOMAIN as BINARY_SENSOR_DOMAIN,
)
from openpeerpower.components.smartthings import binary_sensor
from openpeerpower.components.smartthings.const import DOMAIN, SIGNAL_SMARTTHINGS_UPDATE
from openpeerpower.config_entries import ConfigEntryState
from openpeerpower.const import ATTR_FRIENDLY_NAME, STATE_UNAVAILABLE
from openpeerpower.helpers import device_registry as dr, entity_registry as er
from openpeerpower.helpers.dispatcher import async_dispatcher_send

from .conftest import setup_platform


async def test_mapping_integrity():
    """Test ensures the map dicts have proper integrity."""
    # Ensure every CAPABILITY_TO_ATTRIB key is in CAPABILITIES
    # Ensure every CAPABILITY_TO_ATTRIB value is in ATTRIB_TO_CLASS keys
    for capability, attrib in binary_sensor.CAPABILITY_TO_ATTRIB.items():
        assert capability in CAPABILITIES, capability
        assert attrib in ATTRIBUTES, attrib
        assert attrib in binary_sensor.ATTRIB_TO_CLASS.keys(), attrib
    # Ensure every ATTRIB_TO_CLASS value is in DEVICE_CLASSES
    for attrib, device_class in binary_sensor.ATTRIB_TO_CLASS.items():
        assert attrib in ATTRIBUTES, attrib
        assert device_class in DEVICE_CLASSES, device_class


async def test_entity_state(opp, device_factory):
    """Tests the state attributes properly match the light types."""
    device = device_factory(
        "Motion Sensor 1", [Capability.motion_sensor], {Attribute.motion: "inactive"}
    )
    await setup_platform(opp, BINARY_SENSOR_DOMAIN, devices=[device])
    state = opp.states.get("binary_sensor.motion_sensor_1_motion")
    assert state.state == "off"
    assert state.attributes[ATTR_FRIENDLY_NAME] == f"{device.label} {Attribute.motion}"


async def test_entity_and_device_attributes(opp, device_factory):
    """Test the attributes of the entity are correct."""
    # Arrange
    device = device_factory(
        "Motion Sensor 1", [Capability.motion_sensor], {Attribute.motion: "inactive"}
    )
    entity_registry = er.async_get(opp)
    device_registry = dr.async_get(opp)
    # Act
    await setup_platform(opp, BINARY_SENSOR_DOMAIN, devices=[device])
    # Assert
    entry = entity_registry.async_get("binary_sensor.motion_sensor_1_motion")
    assert entry
    assert entry.unique_id == f"{device.device_id}.{Attribute.motion}"
    entry = device_registry.async_get_device({(DOMAIN, device.device_id)})
    assert entry
    assert entry.name == device.label
    assert entry.model == device.device_type_name
    assert entry.manufacturer == "Unavailable"


async def test_update_from_signal(opp, device_factory):
    """Test the binary_sensor updates when receiving a signal."""
    # Arrange
    device = device_factory(
        "Motion Sensor 1", [Capability.motion_sensor], {Attribute.motion: "inactive"}
    )
    await setup_platform(opp, BINARY_SENSOR_DOMAIN, devices=[device])
    device.status.apply_attribute_update(
        "main", Capability.motion_sensor, Attribute.motion, "active"
    )
    # Act
    async_dispatcher_send(opp, SIGNAL_SMARTTHINGS_UPDATE, [device.device_id])
    # Assert
    await opp.async_block_till_done()
    state = opp.states.get("binary_sensor.motion_sensor_1_motion")
    assert state is not None
    assert state.state == "on"


async def test_unload_config_entry(opp, device_factory):
    """Test the binary_sensor is removed when the config entry is unloaded."""
    # Arrange
    device = device_factory(
        "Motion Sensor 1", [Capability.motion_sensor], {Attribute.motion: "inactive"}
    )
    config_entry = await setup_platform(opp, BINARY_SENSOR_DOMAIN, devices=[device])
    config_entry.state = ConfigEntryState.LOADED
    # Act
    await opp.config_entries.async_forward_entry_unload(config_entry, "binary_sensor")
    # Assert
    assert (
        opp.states.get("binary_sensor.motion_sensor_1_motion").state
        == STATE_UNAVAILABLE
    )
