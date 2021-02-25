"""Test MQTT fans."""
from unittest.mock import patch

import pytest

from openpeerpower.components import fan
from openpeerpower.const import (
    ATTR_ASSUMED_STATE,
    ATTR_SUPPORTED_FEATURES,
    STATE_OFF,
    STATE_ON,
)
from openpeerpower.setup import async_setup_component

from .test_common import (
    help_test_availability_when_connection_lost,
    help_test_availability_without_topic,
    help_test_custom_availability_payload,
    help_test_default_availability_payload,
    help_test_discovery_broken,
    help_test_discovery_removal,
    help_test_discovery_update,
    help_test_discovery_update_attr,
    help_test_discovery_update_unchanged,
    help_test_entity_debug_info_message,
    help_test_entity_device_info_remove,
    help_test_entity_device_info_update,
    help_test_entity_device_info_with_connection,
    help_test_entity_device_info_with_identifier,
    help_test_entity_id_update_discovery_update,
    help_test_entity_id_update_subscriptions,
    help_test_setting_attribute_via_mqtt_json_message,
    help_test_setting_attribute_with_template,
    help_test_unique_id,
    help_test_update_with_json_attrs_bad_JSON,
    help_test_update_with_json_attrs_not_dict,
)

from tests.common import async_fire_mqtt_message
from tests.components.fan import common

DEFAULT_CONFIG = {
    fan.DOMAIN: {
        "platform": "mqtt",
        "name": "test",
        "state_topic": "state-topic",
        "command_topic": "command-topic",
    }
}


async def test_fail_setup_if_no_command_topic(opp, mqtt_mock):
    """Test if command fails with command topic."""
    assert await async_setup_component(
        opp. fan.DOMAIN, {fan.DOMAIN: {"platform": "mqtt", "name": "test"}}
    )
    await opp.async_block_till_done()
    assert opp.states.get("fan.test") is None


async def test_controlling_state_via_topic(opp, mqtt_mock):
    """Test the controlling state via topic."""
    assert await async_setup_component(
        opp,
        fan.DOMAIN,
        {
            fan.DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "state_topic": "state-topic",
                "command_topic": "command-topic",
                "payload_off": "StAtE_OfF",
                "payload_on": "StAtE_On",
                "oscillation_state_topic": "oscillation-state-topic",
                "oscillation_command_topic": "oscillation-command-topic",
                "payload_oscillation_off": "OsC_OfF",
                "payload_oscillation_on": "OsC_On",
                "speed_state_topic": "speed-state-topic",
                "speed_command_topic": "speed-command-topic",
                "payload_off_speed": "speed_OfF",
                "payload_low_speed": "speed_lOw",
                "payload_medium_speed": "speed_mEdium",
                "payload_high_speed": "speed_High",
            }
        },
    )
    await opp.async_block_till_done()

    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(opp, "state-topic", "StAtE_On")
    state = opp.states.get("fan.test")
    assert state.state is STATE_ON

    async_fire_mqtt_message(opp, "state-topic", "StAtE_OfF")
    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get("oscillating") is False

    async_fire_mqtt_message(opp, "oscillation-state-topic", "OsC_On")
    state = opp.states.get("fan.test")
    assert state.attributes.get("oscillating") is True

    async_fire_mqtt_message(opp, "oscillation-state-topic", "OsC_OfF")
    state = opp.states.get("fan.test")
    assert state.attributes.get("oscillating") is False

    assert state.attributes.get("speed") == fan.SPEED_OFF

    async_fire_mqtt_message(opp, "speed-state-topic", "speed_lOw")
    state = opp.states.get("fan.test")
    assert state.attributes.get("speed") == fan.SPEED_LOW

    async_fire_mqtt_message(opp, "speed-state-topic", "speed_mEdium")
    state = opp.states.get("fan.test")
    assert state.attributes.get("speed") == fan.SPEED_MEDIUM

    async_fire_mqtt_message(opp, "speed-state-topic", "speed_High")
    state = opp.states.get("fan.test")
    assert state.attributes.get("speed") == fan.SPEED_HIGH

    async_fire_mqtt_message(opp, "speed-state-topic", "speed_OfF")
    state = opp.states.get("fan.test")
    assert state.attributes.get("speed") == fan.SPEED_OFF


async def test_controlling_state_via_topic_and_json_message(opp, mqtt_mock):
    """Test the controlling state via topic and JSON message."""
    assert await async_setup_component(
        opp,
        fan.DOMAIN,
        {
            fan.DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "state_topic": "state-topic",
                "command_topic": "command-topic",
                "oscillation_state_topic": "oscillation-state-topic",
                "oscillation_command_topic": "oscillation-command-topic",
                "speed_state_topic": "speed-state-topic",
                "speed_command_topic": "speed-command-topic",
                "state_value_template": "{{ value_json.val }}",
                "oscillation_value_template": "{{ value_json.val }}",
                "speed_value_template": "{{ value_json.val }}",
            }
        },
    )
    await opp.async_block_till_done()

    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(opp, "state-topic", '{"val":"ON"}')
    state = opp.states.get("fan.test")
    assert state.state is STATE_ON

    async_fire_mqtt_message(opp, "state-topic", '{"val":"OFF"}')
    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get("oscillating") is False

    async_fire_mqtt_message(opp, "oscillation-state-topic", '{"val":"oscillate_on"}')
    state = opp.states.get("fan.test")
    assert state.attributes.get("oscillating") is True

    async_fire_mqtt_message(opp, "oscillation-state-topic", '{"val":"oscillate_off"}')
    state = opp.states.get("fan.test")
    assert state.attributes.get("oscillating") is False

    assert state.attributes.get("speed") == fan.SPEED_OFF

    async_fire_mqtt_message(opp, "speed-state-topic", '{"val":"low"}')
    state = opp.states.get("fan.test")
    assert state.attributes.get("speed") == fan.SPEED_LOW

    async_fire_mqtt_message(opp, "speed-state-topic", '{"val":"medium"}')
    state = opp.states.get("fan.test")
    assert state.attributes.get("speed") == fan.SPEED_MEDIUM

    async_fire_mqtt_message(opp, "speed-state-topic", '{"val":"high"}')
    state = opp.states.get("fan.test")
    assert state.attributes.get("speed") == fan.SPEED_HIGH

    async_fire_mqtt_message(opp, "speed-state-topic", '{"val":"off"}')
    state = opp.states.get("fan.test")
    assert state.attributes.get("speed") == fan.SPEED_OFF


async def test_sending_mqtt_commands_and_optimistic(opp, mqtt_mock):
    """Test optimistic mode without state topic."""
    assert await async_setup_component(
        opp,
        fan.DOMAIN,
        {
            fan.DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "command_topic": "command-topic",
                "payload_off": "StAtE_OfF",
                "payload_on": "StAtE_On",
                "oscillation_command_topic": "oscillation-command-topic",
                "oscillation_state_topic": "oscillation-state-topic",
                "payload_oscillation_off": "OsC_OfF",
                "payload_oscillation_on": "OsC_On",
                "speed_command_topic": "speed-command-topic",
                "speed_state_topic": "speed-state-topic",
                "payload_off_speed": "speed_OfF",
                "payload_low_speed": "speed_lOw",
                "payload_medium_speed": "speed_mEdium",
                "payload_high_speed": "speed_High",
            }
        },
    )
    await opp.async_block_till_done()

    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_turn_on(opp, "fan.test")
    mqtt_mock.async_publish.assert_called_once_with(
        "command-topic", "StAtE_On", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get("fan.test")
    assert state.state is STATE_ON
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_turn_off(opp, "fan.test")
    mqtt_mock.async_publish.assert_called_once_with(
        "command-topic", "StAtE_OfF", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_oscillate(opp, "fan.test", True)
    mqtt_mock.async_publish.assert_called_once_with(
        "oscillation-command-topic", "OsC_On", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_oscillate(opp, "fan.test", False)
    mqtt_mock.async_publish.assert_called_once_with(
        "oscillation-command-topic", "OsC_OfF", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_speed(opp, "fan.test", fan.SPEED_LOW)
    mqtt_mock.async_publish.assert_called_once_with(
        "speed-command-topic", "speed_lOw", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_speed(opp, "fan.test", fan.SPEED_MEDIUM)
    mqtt_mock.async_publish.assert_called_once_with(
        "speed-command-topic", "speed_mEdium", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_speed(opp, "fan.test", fan.SPEED_HIGH)
    mqtt_mock.async_publish.assert_called_once_with(
        "speed-command-topic", "speed_High", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_speed(opp, "fan.test", fan.SPEED_OFF)
    mqtt_mock.async_publish.assert_called_once_with(
        "speed-command-topic", "speed_OfF", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)


async def test_on_sending_mqtt_commands_and_optimistic(opp, mqtt_mock):
    """Test on with speed."""
    assert await async_setup_component(
        opp,
        fan.DOMAIN,
        {
            fan.DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "command_topic": "command-topic",
                "oscillation_command_topic": "oscillation-command-topic",
                "speed_command_topic": "speed-command-topic",
            }
        },
    )
    await opp.async_block_till_done()

    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_turn_on(opp, "fan.test")
    mqtt_mock.async_publish.assert_called_once_with("command-topic", "ON", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get("fan.test")
    assert state.state is STATE_ON
    assert state.attributes.get(ATTR_ASSUMED_STATE)
    assert state.attributes.get(fan.ATTR_SPEED) is None
    assert state.attributes.get(fan.ATTR_OSCILLATING) is None

    await common.async_turn_off(opp, "fan.test")
    mqtt_mock.async_publish.assert_called_once_with("command-topic", "OFF", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_turn_on(opp, "fan.test", speed="low")
    assert mqtt_mock.async_publish.call_count == 2
    mqtt_mock.async_publish.assert_any_call("command-topic", "ON", 0, False)
    mqtt_mock.async_publish.assert_any_call("speed-command-topic", "low", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get("fan.test")
    assert state.state is STATE_ON
    assert state.attributes.get(ATTR_ASSUMED_STATE)
    assert state.attributes.get(fan.ATTR_SPEED) == "low"
    assert state.attributes.get(fan.ATTR_OSCILLATING) is None


async def test_sending_mqtt_commands_and_explicit_optimistic(opp, mqtt_mock):
    """Test optimistic mode with state topic."""
    assert await async_setup_component(
        opp,
        fan.DOMAIN,
        {
            fan.DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "state_topic": "state-topic",
                "command_topic": "command-topic",
                "oscillation_state_topic": "oscillation-state-topic",
                "oscillation_command_topic": "oscillation-command-topic",
                "speed_state_topic": "speed-state-topic",
                "speed_command_topic": "speed-command-topic",
                "optimistic": True,
            }
        },
    )
    await opp.async_block_till_done()

    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_turn_on(opp, "fan.test")
    mqtt_mock.async_publish.assert_called_once_with("command-topic", "ON", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get("fan.test")
    assert state.state is STATE_ON
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_turn_off(opp, "fan.test")
    mqtt_mock.async_publish.assert_called_once_with("command-topic", "OFF", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_oscillate(opp, "fan.test", True)
    mqtt_mock.async_publish.assert_called_once_with(
        "oscillation-command-topic", "oscillate_on", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_oscillate(opp, "fan.test", False)
    mqtt_mock.async_publish.assert_called_once_with(
        "oscillation-command-topic", "oscillate_off", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_speed(opp, "fan.test", fan.SPEED_LOW)
    mqtt_mock.async_publish.assert_called_once_with(
        "speed-command-topic", "low", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_speed(opp, "fan.test", fan.SPEED_MEDIUM)
    mqtt_mock.async_publish.assert_called_once_with(
        "speed-command-topic", "medium", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_speed(opp, "fan.test", fan.SPEED_HIGH)
    mqtt_mock.async_publish.assert_called_once_with(
        "speed-command-topic", "high", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_speed(opp, "fan.test", fan.SPEED_OFF)
    mqtt_mock.async_publish.assert_called_once_with(
        "speed-command-topic", "off", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    with pytest.raises(ValueError):
        await common.async_set_speed(opp, "fan.test", "cUsToM")


async def test_attributes(opp, mqtt_mock):
    """Test attributes."""
    assert await async_setup_component(
        opp,
        fan.DOMAIN,
        {
            fan.DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "command_topic": "command-topic",
                "oscillation_command_topic": "oscillation-command-topic",
                "speed_command_topic": "speed-command-topic",
            }
        },
    )
    await opp.async_block_till_done()

    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(fan.ATTR_SPEED_LIST) == ["off", "low", "medium", "high"]

    await common.async_turn_on(opp, "fan.test")
    state = opp.states.get("fan.test")
    assert state.state is STATE_ON
    assert state.attributes.get(ATTR_ASSUMED_STATE)
    assert state.attributes.get(fan.ATTR_SPEED) is None
    assert state.attributes.get(fan.ATTR_OSCILLATING) is None

    await common.async_turn_off(opp, "fan.test")
    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)
    assert state.attributes.get(fan.ATTR_SPEED) is None
    assert state.attributes.get(fan.ATTR_OSCILLATING) is None

    await common.async_oscillate(opp, "fan.test", True)
    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)
    assert state.attributes.get(fan.ATTR_SPEED) is None
    assert state.attributes.get(fan.ATTR_OSCILLATING) is True

    await common.async_oscillate(opp, "fan.test", False)
    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)
    assert state.attributes.get(fan.ATTR_SPEED) is None
    assert state.attributes.get(fan.ATTR_OSCILLATING) is False

    await common.async_set_speed(opp, "fan.test", fan.SPEED_LOW)
    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)
    assert state.attributes.get(fan.ATTR_SPEED) == "low"
    assert state.attributes.get(fan.ATTR_OSCILLATING) is False

    await common.async_set_speed(opp, "fan.test", fan.SPEED_MEDIUM)
    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)
    assert state.attributes.get(fan.ATTR_SPEED) == "medium"
    assert state.attributes.get(fan.ATTR_OSCILLATING) is False

    await common.async_set_speed(opp, "fan.test", fan.SPEED_HIGH)
    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)
    assert state.attributes.get(fan.ATTR_SPEED) == "high"
    assert state.attributes.get(fan.ATTR_OSCILLATING) is False

    await common.async_set_speed(opp, "fan.test", fan.SPEED_OFF)
    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)
    assert state.attributes.get(fan.ATTR_SPEED) == "off"
    assert state.attributes.get(fan.ATTR_OSCILLATING) is False

    with pytest.raises(ValueError):
        await common.async_set_speed(opp, "fan.test", "cUsToM")


async def test_custom_speed_list(opp, mqtt_mock):
    """Test optimistic mode without state topic."""
    assert await async_setup_component(
        opp,
        fan.DOMAIN,
        {
            fan.DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "command_topic": "command-topic",
                "oscillation_command_topic": "oscillation-command-topic",
                "oscillation_state_topic": "oscillation-state-topic",
                "speed_command_topic": "speed-command-topic",
                "speed_state_topic": "speed-state-topic",
                "speeds": ["off", "high"],
            }
        },
    )
    await opp.async_block_till_done()

    state = opp.states.get("fan.test")
    assert state.state is STATE_OFF
    assert state.attributes.get(fan.ATTR_SPEED_LIST) == ["off", "high"]


async def test_supported_features(opp, mqtt_mock):
    """Test optimistic mode without state topic."""
    assert await async_setup_component(
        opp,
        fan.DOMAIN,
        {
            fan.DOMAIN: [
                {
                    "platform": "mqtt",
                    "name": "test1",
                    "command_topic": "command-topic",
                },
                {
                    "platform": "mqtt",
                    "name": "test2",
                    "command_topic": "command-topic",
                    "oscillation_command_topic": "oscillation-command-topic",
                },
                {
                    "platform": "mqtt",
                    "name": "test3",
                    "command_topic": "command-topic",
                    "speed_command_topic": "speed-command-topic",
                },
                {
                    "platform": "mqtt",
                    "name": "test4",
                    "command_topic": "command-topic",
                    "oscillation_command_topic": "oscillation-command-topic",
                    "speed_command_topic": "speed-command-topic",
                },
            ]
        },
    )
    await opp.async_block_till_done()

    state = opp.states.get("fan.test1")
    assert state.attributes.get(ATTR_SUPPORTED_FEATURES) == 0
    state = opp.states.get("fan.test2")
    assert state.attributes.get(ATTR_SUPPORTED_FEATURES) == fan.SUPPORT_OSCILLATE
    state = opp.states.get("fan.test3")
    assert state.attributes.get(ATTR_SUPPORTED_FEATURES) == fan.SUPPORT_SET_SPEED
    state = opp.states.get("fan.test4")
    assert (
        state.attributes.get(ATTR_SUPPORTED_FEATURES)
        == fan.SUPPORT_OSCILLATE | fan.SUPPORT_SET_SPEED
    )


async def test_availability_when_connection_lost(opp, mqtt_mock):
    """Test availability after MQTT disconnection."""
    await help_test_availability_when_connection_lost(
        opp. mqtt_mock, fan.DOMAIN, DEFAULT_CONFIG
    )


async def test_availability_without_topic(opp, mqtt_mock):
    """Test availability without defined availability topic."""
    await help_test_availability_without_topic(
        opp. mqtt_mock, fan.DOMAIN, DEFAULT_CONFIG
    )


async def test_default_availability_payload(opp, mqtt_mock):
    """Test availability by default payload with defined topic."""
    await help_test_default_availability_payload(
        opp. mqtt_mock, fan.DOMAIN, DEFAULT_CONFIG, True, "state-topic", "1"
    )


async def test_custom_availability_payload(opp, mqtt_mock):
    """Test availability by custom payload with defined topic."""
    await help_test_custom_availability_payload(
        opp. mqtt_mock, fan.DOMAIN, DEFAULT_CONFIG, True, "state-topic", "1"
    )


async def test_setting_attribute_via_mqtt_json_message(opp, mqtt_mock):
    """Test the setting of attribute via MQTT with JSON payload."""
    await help_test_setting_attribute_via_mqtt_json_message(
        opp. mqtt_mock, fan.DOMAIN, DEFAULT_CONFIG
    )


async def test_setting_attribute_with_template(opp, mqtt_mock):
    """Test the setting of attribute via MQTT with JSON payload."""
    await help_test_setting_attribute_with_template(
        opp. mqtt_mock, fan.DOMAIN, DEFAULT_CONFIG
    )


async def test_update_with_json_attrs_not_dict(opp, mqtt_mock, caplog):
    """Test attributes get extracted from a JSON result."""
    await help_test_update_with_json_attrs_not_dict(
        opp. mqtt_mock, caplog, fan.DOMAIN, DEFAULT_CONFIG
    )


async def test_update_with_json_attrs_bad_JSON.opp, mqtt_mock, caplog):
    """Test attributes get extracted from a JSON result."""
    await help_test_update_with_json_attrs_bad_JSON(
        opp. mqtt_mock, caplog, fan.DOMAIN, DEFAULT_CONFIG
    )


async def test_discovery_update_attr(opp, mqtt_mock, caplog):
    """Test update of discovered MQTTAttributes."""
    await help_test_discovery_update_attr(
        opp. mqtt_mock, caplog, fan.DOMAIN, DEFAULT_CONFIG
    )


async def test_unique_id(opp, mqtt_mock):
    """Test unique_id option only creates one fan per id."""
    config = {
        fan.DOMAIN: [
            {
                "platform": "mqtt",
                "name": "Test 1",
                "state_topic": "test-topic",
                "command_topic": "test_topic",
                "unique_id": "TOTALLY_UNIQUE",
            },
            {
                "platform": "mqtt",
                "name": "Test 2",
                "state_topic": "test-topic",
                "command_topic": "test_topic",
                "unique_id": "TOTALLY_UNIQUE",
            },
        ]
    }
    await help_test_unique_id(opp, mqtt_mock, fan.DOMAIN, config)


async def test_discovery_removal_fan(opp, mqtt_mock, caplog):
    """Test removal of discovered fan."""
    data = '{ "name": "test", "command_topic": "test_topic" }'
    await help_test_discovery_removal(opp, mqtt_mock, caplog, fan.DOMAIN, data)


async def test_discovery_update_fan(opp, mqtt_mock, caplog):
    """Test update of discovered fan."""
    data1 = '{ "name": "Beer", "command_topic": "test_topic" }'
    data2 = '{ "name": "Milk", "command_topic": "test_topic" }'
    await help_test_discovery_update(opp, mqtt_mock, caplog, fan.DOMAIN, data1, data2)


async def test_discovery_update_unchanged_fan(opp, mqtt_mock, caplog):
    """Test update of discovered fan."""
    data1 = '{ "name": "Beer", "command_topic": "test_topic" }'
    with patch(
        "openpeerpower.components.mqtt.fan.MqttFan.discovery_update"
    ) as discovery_update:
        await help_test_discovery_update_unchanged(
            opp. mqtt_mock, caplog, fan.DOMAIN, data1, discovery_update
        )


@pytest.mark.no_fail_on_log_exception
async def test_discovery_broken(opp, mqtt_mock, caplog):
    """Test handling of bad discovery message."""
    data1 = '{ "name": "Beer" }'
    data2 = '{ "name": "Milk", "command_topic": "test_topic" }'
    await help_test_discovery_broken(opp, mqtt_mock, caplog, fan.DOMAIN, data1, data2)


async def test_entity_device_info_with_connection(opp, mqtt_mock):
    """Test MQTT fan device registry integration."""
    await help_test_entity_device_info_with_connection(
        opp. mqtt_mock, fan.DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_device_info_with_identifier(opp, mqtt_mock):
    """Test MQTT fan device registry integration."""
    await help_test_entity_device_info_with_identifier(
        opp. mqtt_mock, fan.DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_device_info_update(opp, mqtt_mock):
    """Test device registry update."""
    await help_test_entity_device_info_update(
        opp. mqtt_mock, fan.DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_device_info_remove(opp, mqtt_mock):
    """Test device registry remove."""
    await help_test_entity_device_info_remove(
        opp. mqtt_mock, fan.DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_id_update_subscriptions(opp, mqtt_mock):
    """Test MQTT subscriptions are managed when entity_id is updated."""
    await help_test_entity_id_update_subscriptions(
        opp. mqtt_mock, fan.DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_id_update_discovery_update(opp, mqtt_mock):
    """Test MQTT discovery update when entity_id is updated."""
    await help_test_entity_id_update_discovery_update(
        opp. mqtt_mock, fan.DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_debug_info_message(opp, mqtt_mock):
    """Test MQTT debug info."""
    await help_test_entity_debug_info_message(
        opp. mqtt_mock, fan.DOMAIN, DEFAULT_CONFIG
    )
