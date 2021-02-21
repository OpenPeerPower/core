"""The tests for Climate device actions."""
import pytest
import voluptuous_serialize

import openpeerpower.components.automation as automation
from openpeerpower.components.climate import DOMAIN, const, device_action
from openpeerpowerr.helpers import config_validation as cv, device_registry
from openpeerpowerr.setup import async_setup_component

from tests.common import (
    MockConfigEntry,
    assert_lists_same,
    async_get_device_automations,
    async_mock_service,
    mock_device_registry,
    mock_registry,
)
from tests.components.blueprint.conftest import stub_blueprint_populate  # noqa


@pytest.fixture
def device_reg.opp):
    """Return an empty, loaded, registry."""
    return mock_device_registry.opp)


@pytest.fixture
def entity_reg.opp):
    """Return an empty, loaded, registry."""
    return mock_registry.opp)


async def test_get_actions.opp, device_reg, entity_reg):
    """Test we get the expected actions from a climate."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(DOMAIN, "test", "5678", device_id=device_entry.id)
   .opp.states.async_set("climate.test_5678", const.HVAC_MODE_COOL, {})
   .opp.states.async_set("climate.test_5678", "attributes", {"supported_features": 17})
    expected_actions = [
        {
            "domain": DOMAIN,
            "type": "set_hvac_mode",
            "device_id": device_entry.id,
            "entity_id": "climate.test_5678",
        },
        {
            "domain": DOMAIN,
            "type": "set_preset_mode",
            "device_id": device_entry.id,
            "entity_id": "climate.test_5678",
        },
    ]
    actions = await async_get_device_automations.opp, "action", device_entry.id)
    assert_lists_same(actions, expected_actions)


async def test_get_action_hvac_only.opp, device_reg, entity_reg):
    """Test we get the expected actions from a climate."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(DOMAIN, "test", "5678", device_id=device_entry.id)
   .opp.states.async_set("climate.test_5678", const.HVAC_MODE_COOL, {})
   .opp.states.async_set("climate.test_5678", "attributes", {"supported_features": 1})
    expected_actions = [
        {
            "domain": DOMAIN,
            "type": "set_hvac_mode",
            "device_id": device_entry.id,
            "entity_id": "climate.test_5678",
        },
    ]
    actions = await async_get_device_automations.opp, "action", device_entry.id)
    assert_lists_same(actions, expected_actions)


async def test_action.opp):
    """Test for actions."""
   .opp.states.async_set(
        "climate.entity",
        const.HVAC_MODE_COOL,
        {
            const.ATTR_HVAC_MODES: [const.HVAC_MODE_COOL, const.HVAC_MODE_OFF],
            const.ATTR_PRESET_MODES: [const.PRESET_HOME, const.PRESET_AWAY],
        },
    )

    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_set_hvac_mode",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "abcdefgh",
                        "entity_id": "climate.entity",
                        "type": "set_hvac_mode",
                        "hvac_mode": const.HVAC_MODE_OFF,
                    },
                },
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_set_preset_mode",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "abcdefgh",
                        "entity_id": "climate.entity",
                        "type": "set_preset_mode",
                        "preset_mode": const.PRESET_AWAY,
                    },
                },
            ]
        },
    )

    set_hvac_mode_calls = async_mock_service.opp, "climate", "set_hvac_mode")
    set_preset_mode_calls = async_mock_service.opp, "climate", "set_preset_mode")

   .opp.bus.async_fire("test_event_set_hvac_mode")
    await opp..async_block_till_done()
    assert len(set_hvac_mode_calls) == 1
    assert len(set_preset_mode_calls) == 0

   .opp.bus.async_fire("test_event_set_preset_mode")
    await opp..async_block_till_done()
    assert len(set_hvac_mode_calls) == 1
    assert len(set_preset_mode_calls) == 1


async def test_capabilities.opp):
    """Test getting capabilities."""
   .opp.states.async_set(
        "climate.entity",
        const.HVAC_MODE_COOL,
        {
            const.ATTR_HVAC_MODES: [const.HVAC_MODE_COOL, const.HVAC_MODE_OFF],
            const.ATTR_PRESET_MODES: [const.PRESET_HOME, const.PRESET_AWAY],
        },
    )

    # Set HVAC mode
    capabilities = await device_action.async_get_action_capabilities(
       .opp,
        {
            "domain": DOMAIN,
            "device_id": "abcdefgh",
            "entity_id": "climate.entity",
            "type": "set_hvac_mode",
        },
    )

    assert capabilities and "extra_fields" in capabilities

    assert voluptuous_serialize.convert(
        capabilities["extra_fields"], custom_serializer=cv.custom_serializer
    ) == [
        {
            "name": "hvac_mode",
            "options": [("cool", "cool"), ("off", "off")],
            "required": True,
            "type": "select",
        }
    ]

    # Set preset mode
    capabilities = await device_action.async_get_action_capabilities(
       .opp,
        {
            "domain": DOMAIN,
            "device_id": "abcdefgh",
            "entity_id": "climate.entity",
            "type": "set_preset_mode",
        },
    )

    assert capabilities and "extra_fields" in capabilities

    assert voluptuous_serialize.convert(
        capabilities["extra_fields"], custom_serializer=cv.custom_serializer
    ) == [
        {
            "name": "preset_mode",
            "options": [("home", "home"), ("away", "away")],
            "required": True,
            "type": "select",
        }
    ]
