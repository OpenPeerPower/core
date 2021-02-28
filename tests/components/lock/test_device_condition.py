"""The tests for Lock device conditions."""
import pytest

import openpeerpower.components.automation as automation
from openpeerpower.components.lock import DOMAIN
from openpeerpower.const import STATE_LOCKED, STATE_UNLOCKED
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
from tests.components.blueprint.conftest import stub_blueprint_populate  # noqa


@pytest.fixture
def device_reg(opp):
    """Return an empty, loaded, registry."""
    return mock_device_registry(opp)


@pytest.fixture
def entity_reg(opp):
    """Return an empty, loaded, registry."""
    return mock_registry(opp)


@pytest.fixture
def calls.opp):
    """Track calls to a mock service."""
    return async_mock_service(opp, "test", "automation")


async def test_get_conditions(opp, device_reg, entity_reg):
    """Test we get the expected conditions from a lock."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp(opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(DOMAIN, "test", "5678", device_id=device_entry.id)
    expected_conditions = [
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_locked",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_unlocked",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
    ]
    conditions = await async_get_device_automations(opp, "condition", device_entry.id)
    assert_lists_same(conditions, expected_conditions)


async def test_if_state(opp, calls):
    """Test for turn_on and turn_off conditions."""
    opp.states.async_set("lock.entity", STATE_LOCKED)

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"platform": "event", "event_type": "test_event1"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": "lock.entity",
                            "type": "is_locked",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_locked - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                        },
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event2"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": "lock.entity",
                            "type": "is_unlocked",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_unlocked - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                        },
                    },
                },
            ]
        },
    )
    opp.bus.async_fire("test_event1")
    opp.bus.async_fire("test_event2")
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["some"] == "is_locked - event - test_event1"

    opp.states.async_set("lock.entity", STATE_UNLOCKED)
    opp.bus.async_fire("test_event1")
    opp.bus.async_fire("test_event2")
    await opp.async_block_till_done()
    assert len(calls) == 2
    assert calls[1].data["some"] == "is_unlocked - event - test_event2"
