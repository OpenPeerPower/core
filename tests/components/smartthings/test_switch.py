"""
Test for the SmartThings switch platform.

The only mocking required is of the underlying SmartThings API object so
real HTTP calls are not initiated during testing.
"""
from pysmartthings import Attribute, Capability

from openpeerpower.components.smartthings.const import DOMAIN, SIGNAL_SMARTTHINGS_UPDATE
from openpeerpower.components.switch import (
    ATTR_CURRENT_POWER_W,
    ATTR_TODAY_ENERGY_KWH,
    DOMAIN as SWITCH_DOMAIN,
)
from openpeerpower.config_entries import ConfigEntryState
from openpeerpower.const import STATE_UNAVAILABLE
from openpeerpower.helpers import device_registry as dr, entity_registry as er
from openpeerpower.helpers.dispatcher import async_dispatcher_send

from .conftest import setup_platform


async def test_entity_and_device_attributes(opp, device_factory):
    """Test the attributes of the entity are correct."""
    # Arrange
    device = device_factory("Switch_1", [Capability.switch], {Attribute.switch: "on"})
    entity_registry = er.async_get(opp)
    device_registry = dr.async_get(opp)
    # Act
    await setup_platform(opp, SWITCH_DOMAIN, devices=[device])
    # Assert
    entry = entity_registry.async_get("switch.switch_1")
    assert entry
    assert entry.unique_id == device.device_id

    entry = device_registry.async_get_device({(DOMAIN, device.device_id)})
    assert entry
    assert entry.name == device.label
    assert entry.model == device.device_type_name
    assert entry.manufacturer == "Unavailable"


async def test_turn_off(opp, device_factory):
    """Test the switch turns of successfully."""
    # Arrange
    device = device_factory("Switch_1", [Capability.switch], {Attribute.switch: "on"})
    await setup_platform(opp, SWITCH_DOMAIN, devices=[device])
    # Act
    await opp.services.async_call(
        "switch", "turn_off", {"entity_id": "switch.switch_1"}, blocking=True
    )
    # Assert
    state = opp.states.get("switch.switch_1")
    assert state is not None
    assert state.state == "off"


async def test_turn_on(opp, device_factory):
    """Test the switch turns of successfully."""
    # Arrange
    device = device_factory(
        "Switch_1",
        [Capability.switch, Capability.power_meter, Capability.energy_meter],
        {Attribute.switch: "off", Attribute.power: 355, Attribute.energy: 11.422},
    )
    await setup_platform(opp, SWITCH_DOMAIN, devices=[device])
    # Act
    await opp.services.async_call(
        "switch", "turn_on", {"entity_id": "switch.switch_1"}, blocking=True
    )
    # Assert
    state = opp.states.get("switch.switch_1")
    assert state is not None
    assert state.state == "on"
    assert state.attributes[ATTR_CURRENT_POWER_W] == 355
    assert state.attributes[ATTR_TODAY_ENERGY_KWH] == 11.422


async def test_update_from_signal(opp, device_factory):
    """Test the switch updates when receiving a signal."""
    # Arrange
    device = device_factory("Switch_1", [Capability.switch], {Attribute.switch: "off"})
    await setup_platform(opp, SWITCH_DOMAIN, devices=[device])
    await device.switch_on(True)
    # Act
    async_dispatcher_send(opp, SIGNAL_SMARTTHINGS_UPDATE, [device.device_id])
    # Assert
    await opp.async_block_till_done()
    state = opp.states.get("switch.switch_1")
    assert state is not None
    assert state.state == "on"


async def test_unload_config_entry(opp, device_factory):
    """Test the switch is removed when the config entry is unloaded."""
    # Arrange
    device = device_factory("Switch 1", [Capability.switch], {Attribute.switch: "on"})
    config_entry = await setup_platform(opp, SWITCH_DOMAIN, devices=[device])
    config_entry.state = ConfigEntryState.LOADED
    # Act
    await opp.config_entries.async_forward_entry_unload(config_entry, "switch")
    # Assert
    assert opp.states.get("switch.switch_1").state == STATE_UNAVAILABLE
