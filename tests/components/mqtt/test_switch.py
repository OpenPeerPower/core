"""The tests for the MQTT switch platform."""
import copy
import json
from unittest.mock import patch

import pytest

from openpeerpower.components import switch
from openpeerpower.const import ATTR_ASSUMED_STATE, STATE_OFF, STATE_ON
import openpeerpower.core as op
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
from tests.components.switch import common

DEFAULT_CONFIG = {
    switch.DOMAIN: {"platform": "mqtt", "name": "test", "command_topic": "test-topic"}
}


async def test_controlling_state_via_topic(opp, mqtt_mock):
    """Test the controlling state via topic."""
    assert await async_setup_component(
        opp,
        switch.DOMAIN,
        {
            switch.DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "state_topic": "state-topic",
                "command_topic": "command-topic",
                "payload_on": 1,
                "payload_off": 0,
            }
        },
    )
    await opp.async_block_till_done()

    state = opp.states.get("switch.test")
    assert state.state == STATE_OFF
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(opp, "state-topic", "1")

    state = opp.states.get("switch.test")
    assert state.state == STATE_ON

    async_fire_mqtt_message(opp, "state-topic", "0")

    state = opp.states.get("switch.test")
    assert state.state == STATE_OFF


async def test_sending_mqtt_commands_and_optimistic(opp, mqtt_mock):
    """Test the sending MQTT commands in optimistic mode."""
    fake_state = op.State("switch.test", "on")

    with patch(
        "openpeerpower.helpers.restore_state.RestoreEntity.async_get_last_state",
        return_value=fake_state,
    ):
        assert await async_setup_component(
            opp,
            switch.DOMAIN,
            {
                switch.DOMAIN: {
                    "platform": "mqtt",
                    "name": "test",
                    "command_topic": "command-topic",
                    "payload_on": "beer on",
                    "payload_off": "beer off",
                    "qos": "2",
                }
            },
        )
        await opp.async_block_till_done()

    state = opp.states.get("switch.test")
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_turn_on(opp, "switch.test")

    mqtt_mock.async_publish.assert_called_once_with(
        "command-topic", "beer on", 2, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get("switch.test")
    assert state.state == STATE_ON

    await common.async_turn_off(opp, "switch.test")

    mqtt_mock.async_publish.assert_called_once_with(
        "command-topic", "beer off", 2, False
    )
    state = opp.states.get("switch.test")
    assert state.state == STATE_OFF


async def test_controlling_state_via_topic_and_json_message(opp, mqtt_mock):
    """Test the controlling state via topic and JSON message."""
    assert await async_setup_component(
        opp,
        switch.DOMAIN,
        {
            switch.DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "state_topic": "state-topic",
                "command_topic": "command-topic",
                "payload_on": "beer on",
                "payload_off": "beer off",
                "value_template": "{{ value_json.val }}",
            }
        },
    )
    await opp.async_block_till_done()

    state = opp.states.get("switch.test")
    assert state.state == STATE_OFF

    async_fire_mqtt_message(opp, "state-topic", '{"val":"beer on"}')

    state = opp.states.get("switch.test")
    assert state.state == STATE_ON

    async_fire_mqtt_message(opp, "state-topic", '{"val":"beer off"}')

    state = opp.states.get("switch.test")
    assert state.state == STATE_OFF


async def test_availability_when_connection_lost(opp, mqtt_mock):
    """Test availability after MQTT disconnection."""
    await help_test_availability_when_connection_lost(
        opp. mqtt_mock, switch.DOMAIN, DEFAULT_CONFIG
    )


async def test_availability_without_topic(opp, mqtt_mock):
    """Test availability without defined availability topic."""
    await help_test_availability_without_topic(
        opp. mqtt_mock, switch.DOMAIN, DEFAULT_CONFIG
    )


async def test_default_availability_payload(opp, mqtt_mock):
    """Test availability by default payload with defined topic."""
    config = {
        switch.DOMAIN: {
            "platform": "mqtt",
            "name": "test",
            "state_topic": "state-topic",
            "command_topic": "command-topic",
            "payload_on": 1,
            "payload_off": 0,
        }
    }

    await help_test_default_availability_payload(
        opp. mqtt_mock, switch.DOMAIN, config, True, "state-topic", "1"
    )


async def test_custom_availability_payload(opp, mqtt_mock):
    """Test availability by custom payload with defined topic."""
    config = {
        switch.DOMAIN: {
            "platform": "mqtt",
            "name": "test",
            "state_topic": "state-topic",
            "command_topic": "command-topic",
            "payload_on": 1,
            "payload_off": 0,
        }
    }

    await help_test_custom_availability_payload(
        opp. mqtt_mock, switch.DOMAIN, config, True, "state-topic", "1"
    )


async def test_custom_state_payload(opp, mqtt_mock):
    """Test the state payload."""
    assert await async_setup_component(
        opp,
        switch.DOMAIN,
        {
            switch.DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "state_topic": "state-topic",
                "command_topic": "command-topic",
                "payload_on": 1,
                "payload_off": 0,
                "state_on": "HIGH",
                "state_off": "LOW",
            }
        },
    )
    await opp.async_block_till_done()

    state = opp.states.get("switch.test")
    assert state.state == STATE_OFF
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(opp, "state-topic", "HIGH")

    state = opp.states.get("switch.test")
    assert state.state == STATE_ON

    async_fire_mqtt_message(opp, "state-topic", "LOW")

    state = opp.states.get("switch.test")
    assert state.state == STATE_OFF


async def test_setting_attribute_via_mqtt_json_message(opp, mqtt_mock):
    """Test the setting of attribute via MQTT with JSON payload."""
    await help_test_setting_attribute_via_mqtt_json_message(
        opp. mqtt_mock, switch.DOMAIN, DEFAULT_CONFIG
    )


async def test_setting_attribute_with_template(opp, mqtt_mock):
    """Test the setting of attribute via MQTT with JSON payload."""
    await help_test_setting_attribute_with_template(
        opp. mqtt_mock, switch.DOMAIN, DEFAULT_CONFIG
    )


async def test_update_with_json_attrs_not_dict(opp, mqtt_mock, caplog):
    """Test attributes get extracted from a JSON result."""
    await help_test_update_with_json_attrs_not_dict(
        opp. mqtt_mock, caplog, switch.DOMAIN, DEFAULT_CONFIG
    )


async def test_update_with_json_attrs_bad_JSON.opp, mqtt_mock, caplog):
    """Test attributes get extracted from a JSON result."""
    await help_test_update_with_json_attrs_bad_JSON(
        opp. mqtt_mock, caplog, switch.DOMAIN, DEFAULT_CONFIG
    )


async def test_discovery_update_attr(opp, mqtt_mock, caplog):
    """Test update of discovered MQTTAttributes."""
    await help_test_discovery_update_attr(
        opp. mqtt_mock, caplog, switch.DOMAIN, DEFAULT_CONFIG
    )


async def test_unique_id(opp, mqtt_mock):
    """Test unique id option only creates one switch per unique_id."""
    config = {
        switch.DOMAIN: [
            {
                "platform": "mqtt",
                "name": "Test 1",
                "state_topic": "test-topic",
                "command_topic": "command-topic",
                "unique_id": "TOTALLY_UNIQUE",
            },
            {
                "platform": "mqtt",
                "name": "Test 2",
                "state_topic": "test-topic",
                "command_topic": "command-topic",
                "unique_id": "TOTALLY_UNIQUE",
            },
        ]
    }
    await help_test_unique_id(opp, mqtt_mock, switch.DOMAIN, config)


async def test_discovery_removal_switch(opp, mqtt_mock, caplog):
    """Test removal of discovered switch."""
    data = (
        '{ "name": "test",'
        '  "state_topic": "test_topic",'
        '  "command_topic": "test_topic" }'
    )
    await help_test_discovery_removal(opp, mqtt_mock, caplog, switch.DOMAIN, data)


async def test_discovery_update_switch_topic_template(opp, mqtt_mock, caplog):
    """Test update of discovered switch."""
    config1 = copy.deepcopy(DEFAULT_CONFIG[switch.DOMAIN])
    config2 = copy.deepcopy(DEFAULT_CONFIG[switch.DOMAIN])
    config1["name"] = "Beer"
    config2["name"] = "Milk"
    config1["state_topic"] = "switch/state1"
    config2["state_topic"] = "switch/state2"
    config1["value_template"] = "{{ value_json.state1.state }}"
    config2["value_template"] = "{{ value_json.state2.state }}"

    state_data1 = [
        ([("switch/state1", '{"state1":{"state":"ON"}}')], "on", None),
    ]
    state_data2 = [
        ([("switch/state2", '{"state2":{"state":"OFF"}}')], "off", None),
        ([("switch/state2", '{"state2":{"state":"ON"}}')], "on", None),
        ([("switch/state1", '{"state1":{"state":"OFF"}}')], "on", None),
        ([("switch/state1", '{"state2":{"state":"OFF"}}')], "on", None),
        ([("switch/state2", '{"state1":{"state":"OFF"}}')], "on", None),
        ([("switch/state2", '{"state2":{"state":"OFF"}}')], "off", None),
    ]

    data1 = json.dumps(config1)
    data2 = json.dumps(config2)
    await help_test_discovery_update(
        opp,
        mqtt_mock,
        caplog,
        switch.DOMAIN,
        data1,
        data2,
        state_data1=state_data1,
        state_data2=state_data2,
    )


async def test_discovery_update_switch_template(opp, mqtt_mock, caplog):
    """Test update of discovered switch."""
    config1 = copy.deepcopy(DEFAULT_CONFIG[switch.DOMAIN])
    config2 = copy.deepcopy(DEFAULT_CONFIG[switch.DOMAIN])
    config1["name"] = "Beer"
    config2["name"] = "Milk"
    config1["state_topic"] = "switch/state1"
    config2["state_topic"] = "switch/state1"
    config1["value_template"] = "{{ value_json.state1.state }}"
    config2["value_template"] = "{{ value_json.state2.state }}"

    state_data1 = [
        ([("switch/state1", '{"state1":{"state":"ON"}}')], "on", None),
    ]
    state_data2 = [
        ([("switch/state1", '{"state2":{"state":"OFF"}}')], "off", None),
        ([("switch/state1", '{"state2":{"state":"ON"}}')], "on", None),
        ([("switch/state1", '{"state1":{"state":"OFF"}}')], "on", None),
        ([("switch/state1", '{"state2":{"state":"OFF"}}')], "off", None),
    ]

    data1 = json.dumps(config1)
    data2 = json.dumps(config2)
    await help_test_discovery_update(
        opp,
        mqtt_mock,
        caplog,
        switch.DOMAIN,
        data1,
        data2,
        state_data1=state_data1,
        state_data2=state_data2,
    )


async def test_discovery_update_unchanged_switch(opp, mqtt_mock, caplog):
    """Test update of discovered switch."""
    data1 = (
        '{ "name": "Beer",'
        '  "state_topic": "test_topic",'
        '  "command_topic": "test_topic" }'
    )
    with patch(
        "openpeerpower.components.mqtt.switch.MqttSwitch.discovery_update"
    ) as discovery_update:
        await help_test_discovery_update_unchanged(
            opp. mqtt_mock, caplog, switch.DOMAIN, data1, discovery_update
        )


@pytest.mark.no_fail_on_log_exception
async def test_discovery_broken(opp, mqtt_mock, caplog):
    """Test handling of bad discovery message."""
    data1 = '{ "name": "Beer" }'
    data2 = (
        '{ "name": "Milk",'
        '  "state_topic": "test_topic",'
        '  "command_topic": "test_topic" }'
    )
    await help_test_discovery_broken(
        opp. mqtt_mock, caplog, switch.DOMAIN, data1, data2
    )


async def test_entity_device_info_with_connection(opp, mqtt_mock):
    """Test MQTT switch device registry integration."""
    await help_test_entity_device_info_with_connection(
        opp. mqtt_mock, switch.DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_device_info_with_identifier(opp, mqtt_mock):
    """Test MQTT switch device registry integration."""
    await help_test_entity_device_info_with_identifier(
        opp. mqtt_mock, switch.DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_device_info_update(opp, mqtt_mock):
    """Test device registry update."""
    await help_test_entity_device_info_update(
        opp. mqtt_mock, switch.DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_device_info_remove(opp, mqtt_mock):
    """Test device registry remove."""
    await help_test_entity_device_info_remove(
        opp. mqtt_mock, switch.DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_id_update_subscriptions(opp, mqtt_mock):
    """Test MQTT subscriptions are managed when entity_id is updated."""
    await help_test_entity_id_update_subscriptions(
        opp. mqtt_mock, switch.DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_id_update_discovery_update(opp, mqtt_mock):
    """Test MQTT discovery update when entity_id is updated."""
    await help_test_entity_id_update_discovery_update(
        opp. mqtt_mock, switch.DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_debug_info_message(opp, mqtt_mock):
    """Test MQTT debug info."""
    await help_test_entity_debug_info_message(
        opp. mqtt_mock, switch.DOMAIN, DEFAULT_CONFIG
    )
