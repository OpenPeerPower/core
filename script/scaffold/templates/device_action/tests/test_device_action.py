"""The tests for NEW_NAME device actions."""
import pytest

from openpeerpower.components import automation
from openpeerpower.components.NEW_DOMAIN import DOMAIN
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import device_registry, entity_registry
from openpeerpower.setup import async_setup_component

from tests.common import (
    MockConfigEntry,
    assert_lists_same,
    async_get_device_automations,
    async_mock_service,
    mock_device_registry,
    mock_registry,
)


@pytest.fixture
def device_reg(opp: OpenPeerPower) -> device_registry.DeviceRegistry:
    """Return an empty, loaded, registry."""
    return mock_device_registry(opp)


@pytest.fixture
def entity_reg(opp: OpenPeerPower) -> entity_registry.EntityRegistry:
    """Return an empty, loaded, registry."""
    return mock_registry(opp)


async def test_get_actions(
    opp: OpenPeerPower,
    device_reg: device_registry.DeviceRegistry,
    entity_reg: entity_registry.EntityRegistry,
) -> None:
    """Test we get the expected actions from a NEW_DOMAIN."""
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
            "entity_id": "NEW_DOMAIN.test_5678",
        },
        {
            "domain": DOMAIN,
            "type": "turn_off",
            "device_id": device_entry.id,
            "entity_id": "NEW_DOMAIN.test_5678",
        },
    ]
    actions = await async_get_device_automations(opp, "action", device_entry.id)
    assert_lists_same(actions, expected_actions)


async def test_action(opp: OpenPeerPower) -> None:
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
                        "entity_id": "NEW_DOMAIN.entity",
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
                        "entity_id": "NEW_DOMAIN.entity",
                        "type": "turn_on",
                    },
                },
            ]
        },
    )

    turn_off_calls = async_mock_service(opp, "NEW_DOMAIN", "turn_off")
    turn_on_calls = async_mock_service(opp, "NEW_DOMAIN", "turn_on")

    opp.bus.async_fire("test_event_turn_off")
    await opp.async_block_till_done()
    assert len(turn_off_calls) == 1
    assert len(turn_on_calls) == 0

    opp.bus.async_fire("test_event_turn_on")
    await opp.async_block_till_done()
    assert len(turn_off_calls) == 1
    assert len(turn_on_calls) == 1
