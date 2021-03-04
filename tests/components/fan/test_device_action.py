"""The tests for Fan device actions."""
import pytest

import openpeerpower.components.automation as automation
from openpeerpower.components.fan import DOMAIN
from openpeerpower.helpers import device_registry
from openpeerpower.setup import async_setup_component

from tests.common import (
    MockConfigEntry,
    assert_lists_same,
    async_get_device_automations,
    async_mock_service,
    mock_device_registry,
    mock_registry,
)
from tests.components.blueprint.conftest import stub_blueprint_populate  # noqa: F401


@pytest.fixture
def device_reg(opp):
    """Return an empty, loaded, registry."""
    return mock_device_registry(opp)


@pytest.fixture
def entity_reg(opp):
    """Return an empty, loaded, registry."""
    return mock_registry(opp)


async def test_get_actions(opp, device_reg, entity_reg):
    """Test we get the expected actions from a fan."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp(opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(DOMAIN, "test", "5678", device_id=device_entry.id)
    expected_actions = [
        {
            "domain": DOMAIN,
            "type": "turn_on",
            "device_id": device_entry.id,
            "entity_id": "fan.test_5678",
        },
        {
            "domain": DOMAIN,
            "type": "turn_off",
            "device_id": device_entry.id,
            "entity_id": "fan.test_5678",
        },
    ]
    actions = await async_get_device_automations(opp, "action", device_entry.id)
    assert_lists_same(actions, expected_actions)


async def test_action(opp):
    """Test for turn_on and turn_off actions."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_turn_off",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "abcdefgh",
                        "entity_id": "fan.entity",
                        "type": "turn_off",
                    },
                },
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_turn_on",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "abcdefgh",
                        "entity_id": "fan.entity",
                        "type": "turn_on",
                    },
                },
            ]
        },
    )

    turn_off_calls = async_mock_service(opp, "fan", "turn_off")
    turn_on_calls = async_mock_service(opp, "fan", "turn_on")

    opp.bus.async_fire("test_event_turn_off")
    await opp.async_block_till_done()
    assert len(turn_off_calls) == 1
    assert len(turn_on_calls) == 0

    opp.bus.async_fire("test_event_turn_on")
    await opp.async_block_till_done()
    assert len(turn_off_calls) == 1
    assert len(turn_on_calls) == 1
