"""The tests for Alarm control panel device conditions."""
import pytest

from openpeerpower.components.alarm_control_panel import DOMAIN
import openpeerpower.components.automation as automation
from openpeerpower.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_CUSTOM_BYPASS,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
    STATE_ALARM_TRIGGERED,
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


async def test_get_no_conditions(opp, device_reg, entity_reg):
    """Test we get the expected conditions from a alarm_control_panel."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp(opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(DOMAIN, "test", "5678", device_id=device_entry.id)
    conditions = await async_get_device_automations(opp, "condition", device_entry.id)
    assert_lists_same(conditions, [])


async def test_get_minimum_conditions(opp, device_reg, entity_reg):
    """Test we get the expected conditions from a alarm_control_panel."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp(opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(DOMAIN, "test", "5678", device_id=device_entry.id)
    opp.states.async_set(
        "alarm_control_panel.test_5678", "attributes", {"supported_features": 0}
    )
    expected_conditions = [
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_disarmed",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_triggered",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
    ]

    conditions = await async_get_device_automations(opp, "condition", device_entry.id)
    assert_lists_same(conditions, expected_conditions)


async def test_get_maximum_conditions(opp, device_reg, entity_reg):
    """Test we get the expected conditions from a alarm_control_panel."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp(opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(DOMAIN, "test", "5678", device_id=device_entry.id)
    opp.states.async_set(
        "alarm_control_panel.test_5678", "attributes", {"supported_features": 31}
    )
    expected_conditions = [
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_disarmed",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_triggered",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_armed_home",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_armed_away",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_armed_night",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_armed_custom_bypass",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
    ]

    conditions = await async_get_device_automations(opp, "condition", device_entry.id)
    assert_lists_same(conditions, expected_conditions)


async def test_if_state(opp, calls):
    """Test for all conditions."""
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
                            "entity_id": "alarm_control_panel.entity",
                            "type": "is_triggered",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_triggered - {{ trigger.platform }} - {{ trigger.event.event_type }}"
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
                            "entity_id": "alarm_control_panel.entity",
                            "type": "is_disarmed",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_disarmed - {{ trigger.platform }} - {{ trigger.event.event_type }}"
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
                            "entity_id": "alarm_control_panel.entity",
                            "type": "is_armed_home",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_armed_home - {{ trigger.platform }} - {{ trigger.event.event_type }}"
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
                            "entity_id": "alarm_control_panel.entity",
                            "type": "is_armed_away",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_armed_away - {{ trigger.platform }} - {{ trigger.event.event_type }}"
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
                            "entity_id": "alarm_control_panel.entity",
                            "type": "is_armed_night",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_armed_night - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                        },
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event6"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": "alarm_control_panel.entity",
                            "type": "is_armed_custom_bypass",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_armed_custom_bypass - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                        },
                    },
                },
            ]
        },
    )
    opp.states.async_set("alarm_control_panel.entity", STATE_ALARM_TRIGGERED)
    opp.bus.async_fire("test_event1")
    opp.bus.async_fire("test_event2")
    opp.bus.async_fire("test_event3")
    opp.bus.async_fire("test_event4")
    opp.bus.async_fire("test_event5")
    opp.bus.async_fire("test_event6")
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["some"] == "is_triggered - event - test_event1"

    opp.states.async_set("alarm_control_panel.entity", STATE_ALARM_DISARMED)
    opp.bus.async_fire("test_event1")
    opp.bus.async_fire("test_event2")
    opp.bus.async_fire("test_event3")
    opp.bus.async_fire("test_event4")
    opp.bus.async_fire("test_event5")
    opp.bus.async_fire("test_event6")
    await opp.async_block_till_done()
    assert len(calls) == 2
    assert calls[1].data["some"] == "is_disarmed - event - test_event2"

    opp.states.async_set("alarm_control_panel.entity", STATE_ALARM_ARMED_HOME)
    opp.bus.async_fire("test_event1")
    opp.bus.async_fire("test_event2")
    opp.bus.async_fire("test_event3")
    opp.bus.async_fire("test_event4")
    opp.bus.async_fire("test_event5")
    opp.bus.async_fire("test_event6")
    await opp.async_block_till_done()
    assert len(calls) == 3
    assert calls[2].data["some"] == "is_armed_home - event - test_event3"

    opp.states.async_set("alarm_control_panel.entity", STATE_ALARM_ARMED_AWAY)
    opp.bus.async_fire("test_event1")
    opp.bus.async_fire("test_event2")
    opp.bus.async_fire("test_event3")
    opp.bus.async_fire("test_event4")
    opp.bus.async_fire("test_event5")
    opp.bus.async_fire("test_event6")
    await opp.async_block_till_done()
    assert len(calls) == 4
    assert calls[3].data["some"] == "is_armed_away - event - test_event4"

    opp.states.async_set("alarm_control_panel.entity", STATE_ALARM_ARMED_NIGHT)
    opp.bus.async_fire("test_event1")
    opp.bus.async_fire("test_event2")
    opp.bus.async_fire("test_event3")
    opp.bus.async_fire("test_event4")
    opp.bus.async_fire("test_event5")
    opp.bus.async_fire("test_event6")
    await opp.async_block_till_done()
    assert len(calls) == 5
    assert calls[4].data["some"] == "is_armed_night - event - test_event5"

    opp.states.async_set("alarm_control_panel.entity", STATE_ALARM_ARMED_CUSTOM_BYPASS)
    opp.bus.async_fire("test_event1")
    opp.bus.async_fire("test_event2")
    opp.bus.async_fire("test_event3")
    opp.bus.async_fire("test_event4")
    opp.bus.async_fire("test_event5")
    opp.bus.async_fire("test_event6")
    await opp.async_block_till_done()
    assert len(calls) == 6
    assert calls[5].data["some"] == "is_armed_custom_bypass - event - test_event6"
