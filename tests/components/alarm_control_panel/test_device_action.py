"""The tests for Alarm control panel device actions."""
import pytest

from openpeerpower.components.alarm_control_panel import DOMAIN
import openpeerpower.components.automation as automation
from openpeerpower.const import (
    CONF_PLATFORM,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
    STATE_ALARM_TRIGGERED,
    STATE_UNKNOWN,
)
from openpeerpowerr.helpers import device_registry
from openpeerpowerr.setup import async_setup_component

from tests.common import (
    MockConfigEntry,
    assert_lists_same,
    async_get_device_automation_capabilities,
    async_get_device_automations,
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
    """Test we get the expected actions from a alarm_control_panel."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(DOMAIN, "test", "5678", device_id=device_entry.id)
   .opp.states.async_set(
        "alarm_control_panel.test_5678", "attributes", {"supported_features": 15}
    )
    expected_actions = [
        {
            "domain": DOMAIN,
            "type": "arm_away",
            "device_id": device_entry.id,
            "entity_id": "alarm_control_panel.test_5678",
        },
        {
            "domain": DOMAIN,
            "type": "arm_home",
            "device_id": device_entry.id,
            "entity_id": "alarm_control_panel.test_5678",
        },
        {
            "domain": DOMAIN,
            "type": "arm_night",
            "device_id": device_entry.id,
            "entity_id": "alarm_control_panel.test_5678",
        },
        {
            "domain": DOMAIN,
            "type": "disarm",
            "device_id": device_entry.id,
            "entity_id": "alarm_control_panel.test_5678",
        },
        {
            "domain": DOMAIN,
            "type": "trigger",
            "device_id": device_entry.id,
            "entity_id": "alarm_control_panel.test_5678",
        },
    ]
    actions = await async_get_device_automations.opp, "action", device_entry.id)
    assert_lists_same(actions, expected_actions)


async def test_get_actions_arm_night_only.opp, device_reg, entity_reg):
    """Test we get the expected actions from a alarm_control_panel."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(DOMAIN, "test", "5678", device_id=device_entry.id)
   .opp.states.async_set(
        "alarm_control_panel.test_5678", "attributes", {"supported_features": 4}
    )
    expected_actions = [
        {
            "domain": DOMAIN,
            "type": "arm_night",
            "device_id": device_entry.id,
            "entity_id": "alarm_control_panel.test_5678",
        },
        {
            "domain": DOMAIN,
            "type": "disarm",
            "device_id": device_entry.id,
            "entity_id": "alarm_control_panel.test_5678",
        },
    ]
    actions = await async_get_device_automations.opp, "action", device_entry.id)
    assert_lists_same(actions, expected_actions)


async def test_get_action_capabilities.opp, device_reg, entity_reg):
    """Test we get the expected capabilities from a sensor trigger."""
    platform = getattr.opp.components, f"test.{DOMAIN}")
    platform.init()

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(
        DOMAIN,
        "test",
        platform.ENTITIES["no_arm_code"].unique_id,
        device_id=device_entry.id,
    )
    assert await async_setup_component.opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await opp.async_block_till_done()

    expected_capabilities = {
        "arm_away": {"extra_fields": []},
        "arm_home": {"extra_fields": []},
        "arm_night": {"extra_fields": []},
        "disarm": {
            "extra_fields": [{"name": "code", "optional": True, "type": "string"}]
        },
        "trigger": {"extra_fields": []},
    }
    actions = await async_get_device_automations.opp, "action", device_entry.id)
    assert len(actions) == 5
    for action in actions:
        capabilities = await async_get_device_automation_capabilities(
           .opp, "action", action
        )
        assert capabilities == expected_capabilities[action["type"]]


async def test_get_action_capabilities_arm_code.opp, device_reg, entity_reg):
    """Test we get the expected capabilities from a sensor trigger."""
    platform = getattr.opp.components, f"test.{DOMAIN}")
    platform.init()

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(
        DOMAIN,
        "test",
        platform.ENTITIES["arm_code"].unique_id,
        device_id=device_entry.id,
    )
    assert await async_setup_component.opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await opp.async_block_till_done()

    expected_capabilities = {
        "arm_away": {
            "extra_fields": [{"name": "code", "optional": True, "type": "string"}]
        },
        "arm_home": {
            "extra_fields": [{"name": "code", "optional": True, "type": "string"}]
        },
        "arm_night": {
            "extra_fields": [{"name": "code", "optional": True, "type": "string"}]
        },
        "disarm": {
            "extra_fields": [{"name": "code", "optional": True, "type": "string"}]
        },
        "trigger": {"extra_fields": []},
    }
    actions = await async_get_device_automations.opp, "action", device_entry.id)
    assert len(actions) == 5
    for action in actions:
        capabilities = await async_get_device_automation_capabilities(
           .opp, "action", action
        )
        assert capabilities == expected_capabilities[action["type"]]


async def test_action.opp):
    """Test for turn_on and turn_off actions."""
    platform = getattr.opp.components, f"test.{DOMAIN}")
    platform.init()

    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_arm_away",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "abcdefgh",
                        "entity_id": "alarm_control_panel.alarm_no_arm_code",
                        "type": "arm_away",
                    },
                },
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_arm_home",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "abcdefgh",
                        "entity_id": "alarm_control_panel.alarm_no_arm_code",
                        "type": "arm_home",
                    },
                },
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_arm_night",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "abcdefgh",
                        "entity_id": "alarm_control_panel.alarm_no_arm_code",
                        "type": "arm_night",
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event_disarm"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "abcdefgh",
                        "entity_id": "alarm_control_panel.alarm_no_arm_code",
                        "type": "disarm",
                        "code": "1234",
                    },
                },
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_trigger",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "abcdefgh",
                        "entity_id": "alarm_control_panel.alarm_no_arm_code",
                        "type": "trigger",
                    },
                },
            ]
        },
    )
    assert await async_setup_component.opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await opp.async_block_till_done()

    assert (
       .opp.states.get("alarm_control_panel.alarm_no_arm_code").state == STATE_UNKNOWN
    )

   .opp.bus.async_fire("test_event_arm_away")
    await opp.async_block_till_done()
    assert (
       .opp.states.get("alarm_control_panel.alarm_no_arm_code").state
        == STATE_ALARM_ARMED_AWAY
    )

   .opp.bus.async_fire("test_event_arm_home")
    await opp.async_block_till_done()
    assert (
       .opp.states.get("alarm_control_panel.alarm_no_arm_code").state
        == STATE_ALARM_ARMED_HOME
    )

   .opp.bus.async_fire("test_event_arm_night")
    await opp.async_block_till_done()
    assert (
       .opp.states.get("alarm_control_panel.alarm_no_arm_code").state
        == STATE_ALARM_ARMED_NIGHT
    )

   .opp.bus.async_fire("test_event_disarm")
    await opp.async_block_till_done()
    assert (
       .opp.states.get("alarm_control_panel.alarm_no_arm_code").state
        == STATE_ALARM_DISARMED
    )

   .opp.bus.async_fire("test_event_trigger")
    await opp.async_block_till_done()
    assert (
       .opp.states.get("alarm_control_panel.alarm_no_arm_code").state
        == STATE_ALARM_TRIGGERED
    )
