"""The tests for Media player device conditions."""
import pytest

import openpeerpower.components.automation as automation
from openpeerpower.components.media_player import DOMAIN
from openpeerpower.const import (
    STATE_IDLE,
    STATE_OFF,
    STATE_ON,
    STATE_PAUSED,
    STATE_PLAYING,
)
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


@pytest.fixture
def calls(opp):
    """Track calls to a mock service."""
    return async_mock_service(opp, "test", "automation")


async def test_get_conditions(opp, device_reg, entity_reg):
    """Test we get the expected conditions from a media_player."""
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
            "type": "is_off",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_on",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_idle",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_paused",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_playing",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
    ]
    conditions = await async_get_device_automations(opp, "condition", device_entry.id)
    assert_lists_same(conditions, expected_conditions)


async def test_if_state(opp, calls):
    """Test for turn_on and turn_off conditions."""
    opp.states.async_set("media_player.entity", STATE_ON)

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
                            "entity_id": "media_player.entity",
                            "type": "is_on",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_on - {{ trigger.platform }} - {{ trigger.event.event_type }}"
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
                            "entity_id": "media_player.entity",
                            "type": "is_off",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_off - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                        },
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event3"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": "media_player.entity",
                            "type": "is_idle",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_idle - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                        },
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event4"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": "media_player.entity",
                            "type": "is_paused",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_paused - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                        },
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event5"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": "media_player.entity",
                            "type": "is_playing",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_playing - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                        },
                    },
                },
            ]
        },
    )
    opp.bus.async_fire("test_event1")
    opp.bus.async_fire("test_event2")
    opp.bus.async_fire("test_event3")
    opp.bus.async_fire("test_event4")
    opp.bus.async_fire("test_event5")
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["some"] == "is_on - event - test_event1"

    opp.states.async_set("media_player.entity", STATE_OFF)
    opp.bus.async_fire("test_event1")
    opp.bus.async_fire("test_event2")
    opp.bus.async_fire("test_event3")
    opp.bus.async_fire("test_event4")
    opp.bus.async_fire("test_event5")
    await opp.async_block_till_done()
    assert len(calls) == 2
    assert calls[1].data["some"] == "is_off - event - test_event2"

    opp.states.async_set("media_player.entity", STATE_IDLE)
    opp.bus.async_fire("test_event1")
    opp.bus.async_fire("test_event2")
    opp.bus.async_fire("test_event3")
    opp.bus.async_fire("test_event4")
    opp.bus.async_fire("test_event5")
    await opp.async_block_till_done()
    assert len(calls) == 3
    assert calls[2].data["some"] == "is_idle - event - test_event3"

    opp.states.async_set("media_player.entity", STATE_PAUSED)
    opp.bus.async_fire("test_event1")
    opp.bus.async_fire("test_event2")
    opp.bus.async_fire("test_event3")
    opp.bus.async_fire("test_event4")
    opp.bus.async_fire("test_event5")
    await opp.async_block_till_done()
    assert len(calls) == 4
    assert calls[3].data["some"] == "is_paused - event - test_event4"

    opp.states.async_set("media_player.entity", STATE_PLAYING)
    opp.bus.async_fire("test_event1")
    opp.bus.async_fire("test_event2")
    opp.bus.async_fire("test_event3")
    opp.bus.async_fire("test_event4")
    opp.bus.async_fire("test_event5")
    await opp.async_block_till_done()
    assert len(calls) == 5
    assert calls[4].data["some"] == "is_playing - event - test_event5"
