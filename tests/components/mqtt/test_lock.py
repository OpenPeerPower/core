"""The tests for the MQTT lock platform."""
from unittest.mock import patch

import pytest

from openpeerpower.components.lock import (
    DOMAIN as LOCK_DOMAIN,
    SERVICE_LOCK,
    SERVICE_UNLOCK,
    STATE_LOCKED,
    STATE_UNLOCKED,
)
from openpeerpower.const import ATTR_ASSUMED_STATE, ATTR_ENTITY_ID
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

DEFAULT_CONFIG = {
    LOCK_DOMAIN: {"platform": "mqtt", "name": "test", "command_topic": "test-topic"}
}


async def test_controlling_state_via_topic(opp, mqtt_mock):
    """Test the controlling state via topic."""
    assert await async_setup_component(
        opp,
        LOCK_DOMAIN,
        {
            LOCK_DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "state_topic": "state-topic",
                "command_topic": "command-topic",
                "payload_lock": "LOCK",
                "payload_unlock": "UNLOCK",
                "state_locked": "LOCKED",
                "state_unlocked": "UNLOCKED",
            }
        },
    )
    await opp.async_block_till_done()

    state = opp.states.get("lock.test")
    assert state.state is STATE_UNLOCKED
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(opp, "state-topic", "LOCKED")

    state = opp.states.get("lock.test")
    assert state.state is STATE_LOCKED

    async_fire_mqtt_message(opp, "state-topic", "UNLOCKED")

    state = opp.states.get("lock.test")
    assert state.state is STATE_UNLOCKED


async def test_controlling_non_default_state_via_topic(opp, mqtt_mock):
    """Test the controlling state via topic."""
    assert await async_setup_component(
        opp,
        LOCK_DOMAIN,
        {
            LOCK_DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "state_topic": "state-topic",
                "command_topic": "command-topic",
                "payload_lock": "LOCK",
                "payload_unlock": "UNLOCK",
                "state_locked": "closed",
                "state_unlocked": "open",
            }
        },
    )
    await opp.async_block_till_done()

    state = opp.states.get("lock.test")
    assert state.state is STATE_UNLOCKED
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(opp, "state-topic", "closed")

    state = opp.states.get("lock.test")
    assert state.state is STATE_LOCKED

    async_fire_mqtt_message(opp, "state-topic", "open")

    state = opp.states.get("lock.test")
    assert state.state is STATE_UNLOCKED


async def test_controlling_state_via_topic_and_json_message(opp, mqtt_mock):
    """Test the controlling state via topic and JSON message."""
    assert await async_setup_component(
        opp,
        LOCK_DOMAIN,
        {
            LOCK_DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "state_topic": "state-topic",
                "command_topic": "command-topic",
                "payload_lock": "LOCK",
                "payload_unlock": "UNLOCK",
                "state_locked": "LOCKED",
                "state_unlocked": "UNLOCKED",
                "value_template": "{{ value_json.val }}",
            }
        },
    )
    await opp.async_block_till_done()

    state = opp.states.get("lock.test")
    assert state.state is STATE_UNLOCKED

    async_fire_mqtt_message(opp, "state-topic", '{"val":"LOCKED"}')

    state = opp.states.get("lock.test")
    assert state.state is STATE_LOCKED

    async_fire_mqtt_message(opp, "state-topic", '{"val":"UNLOCKED"}')

    state = opp.states.get("lock.test")
    assert state.state is STATE_UNLOCKED


async def test_controlling_non_default_state_via_topic_and_json_message(
    opp, mqtt_mock
):
    """Test the controlling state via topic and JSON message."""
    assert await async_setup_component(
        opp,
        LOCK_DOMAIN,
        {
            LOCK_DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "state_topic": "state-topic",
                "command_topic": "command-topic",
                "payload_lock": "LOCK",
                "payload_unlock": "UNLOCK",
                "state_locked": "closed",
                "state_unlocked": "open",
                "value_template": "{{ value_json.val }}",
            }
        },
    )
    await opp.async_block_till_done()

    state = opp.states.get("lock.test")
    assert state.state is STATE_UNLOCKED

    async_fire_mqtt_message(opp, "state-topic", '{"val":"closed"}')

    state = opp.states.get("lock.test")
    assert state.state is STATE_LOCKED

    async_fire_mqtt_message(opp, "state-topic", '{"val":"open"}')

    state = opp.states.get("lock.test")
    assert state.state is STATE_UNLOCKED


async def test_sending_mqtt_commands_and_optimistic(opp, mqtt_mock):
    """Test optimistic mode without state topic."""
    assert await async_setup_component(
        opp,
        LOCK_DOMAIN,
        {
            LOCK_DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "command_topic": "command-topic",
                "payload_lock": "LOCK",
                "payload_unlock": "UNLOCK",
                "state_locked": "LOCKED",
                "state_unlocked": "UNLOCKED",
            }
        },
    )
    await opp.async_block_till_done()

    state = opp.states.get("lock.test")
    assert state.state is STATE_UNLOCKED
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await opp.services.async_call(
        LOCK_DOMAIN, SERVICE_LOCK, {ATTR_ENTITY_ID: "lock.test"}, blocking=True
    )

    mqtt_mock.async_publish.assert_called_once_with("command-topic", "LOCK", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get("lock.test")
    assert state.state is STATE_LOCKED
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await opp.services.async_call(
        LOCK_DOMAIN, SERVICE_UNLOCK, {ATTR_ENTITY_ID: "lock.test"}, blocking=True
    )

    mqtt_mock.async_publish.assert_called_once_with("command-topic", "UNLOCK", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get("lock.test")
    assert state.state is STATE_UNLOCKED
    assert state.attributes.get(ATTR_ASSUMED_STATE)


async def test_sending_mqtt_commands_and_explicit_optimistic(opp, mqtt_mock):
    """Test optimistic mode without state topic."""
    assert await async_setup_component(
        opp,
        LOCK_DOMAIN,
        {
            LOCK_DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "state_topic": "state-topic",
                "command_topic": "command-topic",
                "payload_lock": "LOCK",
                "payload_unlock": "UNLOCK",
                "state_locked": "LOCKED",
                "state_unlocked": "UNLOCKED",
                "optimistic": True,
            }
        },
    )
    await opp.async_block_till_done()

    state = opp.states.get("lock.test")
    assert state.state is STATE_UNLOCKED
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await opp.services.async_call(
        LOCK_DOMAIN, SERVICE_LOCK, {ATTR_ENTITY_ID: "lock.test"}, blocking=True
    )

    mqtt_mock.async_publish.assert_called_once_with("command-topic", "LOCK", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get("lock.test")
    assert state.state is STATE_LOCKED
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await opp.services.async_call(
        LOCK_DOMAIN, SERVICE_UNLOCK, {ATTR_ENTITY_ID: "lock.test"}, blocking=True
    )

    mqtt_mock.async_publish.assert_called_once_with("command-topic", "UNLOCK", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get("lock.test")
    assert state.state is STATE_UNLOCKED
    assert state.attributes.get(ATTR_ASSUMED_STATE)


async def test_availability_when_connection_lost(opp, mqtt_mock):
    """Test availability after MQTT disconnection."""
    await help_test_availability_when_connection_lost(
        opp, mqtt_mock, LOCK_DOMAIN, DEFAULT_CONFIG
    )


async def test_availability_without_topic(opp, mqtt_mock):
    """Test availability without defined availability topic."""
    await help_test_availability_without_topic(
        opp, mqtt_mock, LOCK_DOMAIN, DEFAULT_CONFIG
    )


async def test_default_availability_payload(opp, mqtt_mock):
    """Test availability by default payload with defined topic."""
    await help_test_default_availability_payload(
        opp, mqtt_mock, LOCK_DOMAIN, DEFAULT_CONFIG
    )


async def test_custom_availability_payload(opp, mqtt_mock):
    """Test availability by custom payload with defined topic."""
    await help_test_custom_availability_payload(
        opp, mqtt_mock, LOCK_DOMAIN, DEFAULT_CONFIG
    )


async def test_setting_attribute_via_mqtt_json_message(opp, mqtt_mock):
    """Test the setting of attribute via MQTT with JSON payload."""
    await help_test_setting_attribute_via_mqtt_json_message(
        opp, mqtt_mock, LOCK_DOMAIN, DEFAULT_CONFIG
    )


async def test_setting_attribute_with_template(opp, mqtt_mock):
    """Test the setting of attribute via MQTT with JSON payload."""
    await help_test_setting_attribute_with_template(
        opp, mqtt_mock, LOCK_DOMAIN, DEFAULT_CONFIG
    )


async def test_update_with_json_attrs_not_dict(opp, mqtt_mock, caplog):
    """Test attributes get extracted from a JSON result."""
    await help_test_update_with_json_attrs_not_dict(
        opp, mqtt_mock, caplog, LOCK_DOMAIN, DEFAULT_CONFIG
    )


async def test_update_with_json_attrs_bad_json(opp, mqtt_mock, caplog):
    """Test attributes get extracted from a JSON result."""
    await help_test_update_with_json_attrs_bad_JSON(
        opp, mqtt_mock, caplog, LOCK_DOMAIN, DEFAULT_CONFIG
    )


async def test_discovery_update_attr(opp, mqtt_mock, caplog):
    """Test update of discovered MQTTAttributes."""
    await help_test_discovery_update_attr(
        opp, mqtt_mock, caplog, LOCK_DOMAIN, DEFAULT_CONFIG
    )


async def test_unique_id(opp, mqtt_mock):
    """Test unique id option only creates one lock per unique_id."""
    config = {
        LOCK_DOMAIN: [
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
    await help_test_unique_id(opp, mqtt_mock, LOCK_DOMAIN, config)


async def test_discovery_removal_lock(opp, mqtt_mock, caplog):
    """Test removal of discovered lock."""
    data = '{ "name": "test",' '  "command_topic": "test_topic" }'
    await help_test_discovery_removal(opp, mqtt_mock, caplog, LOCK_DOMAIN, data)


async def test_discovery_update_lock(opp, mqtt_mock, caplog):
    """Test update of discovered lock."""
    data1 = (
        '{ "name": "Beer",'
        '  "state_topic": "test_topic",'
        '  "command_topic": "command_topic",'
        '  "availability_topic": "availability_topic1" }'
    )
    data2 = (
        '{ "name": "Milk",'
        '  "state_topic": "test_topic2",'
        '  "command_topic": "command_topic",'
        '  "availability_topic": "availability_topic2" }'
    )
    await help_test_discovery_update(opp, mqtt_mock, caplog, LOCK_DOMAIN, data1, data2)


async def test_discovery_update_unchanged_lock(opp, mqtt_mock, caplog):
    """Test update of discovered lock."""
    data1 = (
        '{ "name": "Beer",'
        '  "state_topic": "test_topic",'
        '  "command_topic": "command_topic" }'
    )
    with patch(
        "openpeerpower.components.mqtt.lock.MqttLock.discovery_update"
    ) as discovery_update:
        await help_test_discovery_update_unchanged(
            opp, mqtt_mock, caplog, LOCK_DOMAIN, data1, discovery_update
        )


@pytest.mark.no_fail_on_log_exception
async def test_discovery_broken(opp, mqtt_mock, caplog):
    """Test handling of bad discovery message."""
    data1 = '{ "name": "Beer" }'
    data2 = '{ "name": "Milk",' '  "command_topic": "test_topic" }'
    await help_test_discovery_broken(opp, mqtt_mock, caplog, LOCK_DOMAIN, data1, data2)


async def test_entity_device_info_with_connection(opp, mqtt_mock):
    """Test MQTT lock device registry integration."""
    await help_test_entity_device_info_with_connection(
        opp, mqtt_mock, LOCK_DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_device_info_with_identifier(opp, mqtt_mock):
    """Test MQTT lock device registry integration."""
    await help_test_entity_device_info_with_identifier(
        opp, mqtt_mock, LOCK_DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_device_info_update(opp, mqtt_mock):
    """Test device registry update."""
    await help_test_entity_device_info_update(
        opp, mqtt_mock, LOCK_DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_device_info_remove(opp, mqtt_mock):
    """Test device registry remove."""
    await help_test_entity_device_info_remove(
        opp, mqtt_mock, LOCK_DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_id_update_subscriptions(opp, mqtt_mock):
    """Test MQTT subscriptions are managed when entity_id is updated."""
    await help_test_entity_id_update_subscriptions(
        opp, mqtt_mock, LOCK_DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_id_update_discovery_update(opp, mqtt_mock):
    """Test MQTT discovery update when entity_id is updated."""
    await help_test_entity_id_update_discovery_update(
        opp, mqtt_mock, LOCK_DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_debug_info_message(opp, mqtt_mock):
    """Test MQTT debug info."""
    await help_test_entity_debug_info_message(
        opp, mqtt_mock, LOCK_DOMAIN, DEFAULT_CONFIG
    )
