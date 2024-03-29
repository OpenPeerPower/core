"""
Test for the SmartThings fan platform.

The only mocking required is of the underlying SmartThings API object so
real HTTP calls are not initiated during testing.
"""
from pysmartthings import Attribute, Capability

from openpeerpower.components.fan import (
    ATTR_SPEED,
    ATTR_SPEED_LIST,
    DOMAIN as FAN_DOMAIN,
    SPEED_HIGH,
    SPEED_LOW,
    SPEED_MEDIUM,
    SPEED_OFF,
    SUPPORT_SET_SPEED,
)
from openpeerpower.components.smartthings.const import DOMAIN, SIGNAL_SMARTTHINGS_UPDATE
from openpeerpower.config_entries import ConfigEntryState
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    STATE_UNAVAILABLE,
)
from openpeerpower.helpers import device_registry as dr, entity_registry as er
from openpeerpower.helpers.dispatcher import async_dispatcher_send

from .conftest import setup_platform


async def test_entity_state(opp, device_factory):
    """Tests the state attributes properly match the fan types."""
    device = device_factory(
        "Fan 1",
        capabilities=[Capability.switch, Capability.fan_speed],
        status={Attribute.switch: "on", Attribute.fan_speed: 2},
    )
    await setup_platform(opp, FAN_DOMAIN, devices=[device])

    # Dimmer 1
    state = opp.states.get("fan.fan_1")
    assert state.state == "on"
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == SUPPORT_SET_SPEED
    assert state.attributes[ATTR_SPEED] == SPEED_MEDIUM
    assert state.attributes[ATTR_SPEED_LIST] == [
        SPEED_OFF,
        SPEED_LOW,
        SPEED_MEDIUM,
        SPEED_HIGH,
    ]


async def test_entity_and_device_attributes(opp, device_factory):
    """Test the attributes of the entity are correct."""
    # Arrange
    device = device_factory(
        "Fan 1",
        capabilities=[Capability.switch, Capability.fan_speed],
        status={Attribute.switch: "on", Attribute.fan_speed: 2},
    )
    # Act
    await setup_platform(opp, FAN_DOMAIN, devices=[device])
    entity_registry = er.async_get(opp)
    device_registry = dr.async_get(opp)
    # Assert
    entry = entity_registry.async_get("fan.fan_1")
    assert entry
    assert entry.unique_id == device.device_id

    entry = device_registry.async_get_device({(DOMAIN, device.device_id)})
    assert entry
    assert entry.name == device.label
    assert entry.model == device.device_type_name
    assert entry.manufacturer == "Unavailable"


async def test_turn_off(opp, device_factory):
    """Test the fan turns of successfully."""
    # Arrange
    device = device_factory(
        "Fan 1",
        capabilities=[Capability.switch, Capability.fan_speed],
        status={Attribute.switch: "on", Attribute.fan_speed: 2},
    )
    await setup_platform(opp, FAN_DOMAIN, devices=[device])
    # Act
    await opp.services.async_call(
        "fan", "turn_off", {"entity_id": "fan.fan_1"}, blocking=True
    )
    # Assert
    state = opp.states.get("fan.fan_1")
    assert state is not None
    assert state.state == "off"


async def test_turn_on(opp, device_factory):
    """Test the fan turns of successfully."""
    # Arrange
    device = device_factory(
        "Fan 1",
        capabilities=[Capability.switch, Capability.fan_speed],
        status={Attribute.switch: "off", Attribute.fan_speed: 0},
    )
    await setup_platform(opp, FAN_DOMAIN, devices=[device])
    # Act
    await opp.services.async_call(
        "fan", "turn_on", {ATTR_ENTITY_ID: "fan.fan_1"}, blocking=True
    )
    # Assert
    state = opp.states.get("fan.fan_1")
    assert state is not None
    assert state.state == "on"


async def test_turn_on_with_speed(opp, device_factory):
    """Test the fan turns on to the specified speed."""
    # Arrange
    device = device_factory(
        "Fan 1",
        capabilities=[Capability.switch, Capability.fan_speed],
        status={Attribute.switch: "off", Attribute.fan_speed: 0},
    )
    await setup_platform(opp, FAN_DOMAIN, devices=[device])
    # Act
    await opp.services.async_call(
        "fan",
        "turn_on",
        {ATTR_ENTITY_ID: "fan.fan_1", ATTR_SPEED: SPEED_HIGH},
        blocking=True,
    )
    # Assert
    state = opp.states.get("fan.fan_1")
    assert state is not None
    assert state.state == "on"
    assert state.attributes[ATTR_SPEED] == SPEED_HIGH


async def test_set_speed(opp, device_factory):
    """Test setting to specific fan speed."""
    # Arrange
    device = device_factory(
        "Fan 1",
        capabilities=[Capability.switch, Capability.fan_speed],
        status={Attribute.switch: "off", Attribute.fan_speed: 0},
    )
    await setup_platform(opp, FAN_DOMAIN, devices=[device])
    # Act
    await opp.services.async_call(
        "fan",
        "set_speed",
        {ATTR_ENTITY_ID: "fan.fan_1", ATTR_SPEED: SPEED_HIGH},
        blocking=True,
    )
    # Assert
    state = opp.states.get("fan.fan_1")
    assert state is not None
    assert state.state == "on"
    assert state.attributes[ATTR_SPEED] == SPEED_HIGH


async def test_update_from_signal(opp, device_factory):
    """Test the fan updates when receiving a signal."""
    # Arrange
    device = device_factory(
        "Fan 1",
        capabilities=[Capability.switch, Capability.fan_speed],
        status={Attribute.switch: "off", Attribute.fan_speed: 0},
    )
    await setup_platform(opp, FAN_DOMAIN, devices=[device])
    await device.switch_on(True)
    # Act
    async_dispatcher_send(opp, SIGNAL_SMARTTHINGS_UPDATE, [device.device_id])
    # Assert
    await opp.async_block_till_done()
    state = opp.states.get("fan.fan_1")
    assert state is not None
    assert state.state == "on"


async def test_unload_config_entry(opp, device_factory):
    """Test the fan is removed when the config entry is unloaded."""
    # Arrange
    device = device_factory(
        "Fan 1",
        capabilities=[Capability.switch, Capability.fan_speed],
        status={Attribute.switch: "off", Attribute.fan_speed: 0},
    )
    config_entry = await setup_platform(opp, FAN_DOMAIN, devices=[device])
    config_entry.state = ConfigEntryState.LOADED
    # Act
    await opp.config_entries.async_forward_entry_unload(config_entry, "fan")
    # Assert
    assert opp.states.get("fan.fan_1").state == STATE_UNAVAILABLE
