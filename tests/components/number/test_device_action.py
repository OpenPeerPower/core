"""The tests for Number device actions."""
import pytest
import voluptuous_serialize

import openpeerpower.components.automation as automation
from openpeerpower.components.number import DOMAIN, device_action
from openpeerpower.helpers import config_validation as cv, device_registry
from openpeerpower.setup import async_setup_component

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
    """Test we get the expected actions for an entity."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to.opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(DOMAIN, "test", "5678", device_id=device_entry.id)
    opp.states.async_set("number.test_5678", 0.5, {"min_value": 0.0, "max_value": 1.0})
    expected_actions = [
        {
            "domain": DOMAIN,
            "type": "set_value",
            "device_id": device_entry.id,
            "entity_id": "number.test_5678",
        },
    ]
    actions = await async_get_device_automations.opp, "action", device_entry.id)
    assert_lists_same(actions, expected_actions)


async def test_get_action_no_state.opp, device_reg, entity_reg):
    """Test we get the expected actions for an entity."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to.opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(DOMAIN, "test", "5678", device_id=device_entry.id)
    expected_actions = [
        {
            "domain": DOMAIN,
            "type": "set_value",
            "device_id": device_entry.id,
            "entity_id": "number.test_5678",
        },
    ]
    actions = await async_get_device_automations.opp, "action", device_entry.id)
    assert_lists_same(actions, expected_actions)


async def test_action.opp):
    """Test for actions."""
    opp.states.async_set("number.entity", 0.5, {"min_value": 0.0, "max_value": 1.0})

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_set_value",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "abcdefgh",
                        "entity_id": "number.entity",
                        "type": "set_value",
                        "value": 0.3,
                    },
                },
            ]
        },
    )

    calls = async_mock_service.opp, DOMAIN, "set_value")

    assert len(calls) == 0

    opp.bus.async_fire("test_event_set_value")
    await opp.async_block_till_done()

    assert len(calls) == 1


async def test_capabilities.opp):
    """Test getting capabilities."""
    capabilities = await device_action.async_get_action_capabilities(
        opp,
        {
            "domain": DOMAIN,
            "device_id": "abcdefgh",
            "entity_id": "number.entity",
            "type": "set_value",
        },
    )

    assert capabilities and "extra_fields" in capabilities

    assert voluptuous_serialize.convert(
        capabilities["extra_fields"], custom_serializer=cv.custom_serializer
    ) == [{"name": "value", "required": True, "type": "float"}]
