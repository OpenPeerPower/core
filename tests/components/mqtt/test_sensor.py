"""The tests for the MQTT sensor platform."""
import copy
from datetime import datetime, timedelta
import json
from unittest.mock import patch

import pytest

import openpeerpower.components.sensor as sensor
from openpeerpower.const import EVENT_STATE_CHANGED, STATE_UNAVAILABLE
import openpeerpower.core as ha
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util

from .test_common import (
    help_test_availability_when_connection_lost,
    help_test_availability_without_topic,
    help_test_custom_availability_payload,
    help_test_default_availability_list_payload,
    help_test_default_availability_list_payload_all,
    help_test_default_availability_list_payload_any,
    help_test_default_availability_list_single,
    help_test_default_availability_payload,
    help_test_discovery_broken,
    help_test_discovery_removal,
    help_test_discovery_update,
    help_test_discovery_update_attr,
    help_test_discovery_update_availability,
    help_test_discovery_update_unchanged,
    help_test_entity_debug_info,
    help_test_entity_debug_info_max_messages,
    help_test_entity_debug_info_message,
    help_test_entity_debug_info_remove,
    help_test_entity_debug_info_update_entity_id,
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

from tests.common import async_fire_mqtt_message, async_fire_time_changed

DEFAULT_CONFIG = {
    sensor.DOMAIN: {"platform": "mqtt", "name": "test", "state_topic": "test-topic"}
}


async def test_setting_sensor_value_via_mqtt_message.opp, mqtt_mock):
    """Test the setting of the value via MQTT."""
    assert await async_setup_component(
        opp,
        sensor.DOMAIN,
        {
            sensor.DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "state_topic": "test-topic",
                "unit_of_measurement": "fav unit",
            }
        },
    )
    await opp.async_block_till_done()

    async_fire_mqtt_message.opp, "test-topic", "100")
    state = opp.states.get("sensor.test")

    assert state.state == "100"
    assert state.attributes.get("unit_of_measurement") == "fav unit"


async def test_setting_sensor_value_expires_availability_topic.opp, mqtt_mock, caplog):
    """Test the expiration of the value."""
    assert await async_setup_component(
        opp,
        sensor.DOMAIN,
        {
            sensor.DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "state_topic": "test-topic",
                "expire_after": 4,
                "force_update": True,
                "availability_topic": "availability-topic",
            }
        },
    )
    await opp.async_block_till_done()

    state = opp.states.get("sensor.test")
    assert state.state == STATE_UNAVAILABLE

    async_fire_mqtt_message.opp, "availability-topic", "online")

    # State should be unavailable since expire_after is defined and > 0
    state = opp.states.get("sensor.test")
    assert state.state == STATE_UNAVAILABLE

    await expires_helper.opp, mqtt_mock, caplog)


async def test_setting_sensor_value_expires.opp, mqtt_mock, caplog):
    """Test the expiration of the value."""
    assert await async_setup_component(
        opp,
        sensor.DOMAIN,
        {
            sensor.DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "state_topic": "test-topic",
                "unit_of_measurement": "fav unit",
                "expire_after": "4",
                "force_update": True,
            }
        },
    )
    await opp.async_block_till_done()

    # State should be unavailable since expire_after is defined and > 0
    state = opp.states.get("sensor.test")
    assert state.state == STATE_UNAVAILABLE

    await expires_helper.opp, mqtt_mock, caplog)


async def expires_helper.opp, mqtt_mock, caplog):
    """Run the basic expiry code."""
    realnow = dt_util.utcnow()
    now = datetime(realnow.year + 1, 1, 1, 1, tzinfo=dt_util.UTC)
    with patch(("openpeerpower.helpers.event.dt_util.utcnow"), return_value=now):
        async_fire_time_changed.opp, now)
        async_fire_mqtt_message.opp, "test-topic", "100")
        await opp.async_block_till_done()

    # Value was set correctly.
    state = opp.states.get("sensor.test")
    assert state.state == "100"

    # Time jump +3s
    now = now + timedelta(seconds=3)
    async_fire_time_changed.opp, now)
    await opp.async_block_till_done()

    # Value is not yet expired
    state = opp.states.get("sensor.test")
    assert state.state == "100"

    # Next message resets timer
    with patch(("openpeerpower.helpers.event.dt_util.utcnow"), return_value=now):
        async_fire_time_changed.opp, now)
        async_fire_mqtt_message.opp, "test-topic", "101")
        await opp.async_block_till_done()

    # Value was updated correctly.
    state = opp.states.get("sensor.test")
    assert state.state == "101"

    # Time jump +3s
    now = now + timedelta(seconds=3)
    async_fire_time_changed.opp, now)
    await opp.async_block_till_done()

    # Value is not yet expired
    state = opp.states.get("sensor.test")
    assert state.state == "101"

    # Time jump +2s
    now = now + timedelta(seconds=2)
    async_fire_time_changed.opp, now)
    await opp.async_block_till_done()

    # Value is expired now
    state = opp.states.get("sensor.test")
    assert state.state == STATE_UNAVAILABLE


async def test_setting_sensor_value_via_mqtt_json_message.opp, mqtt_mock):
    """Test the setting of the value via MQTT with JSON payload."""
    assert await async_setup_component(
        opp,
        sensor.DOMAIN,
        {
            sensor.DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "state_topic": "test-topic",
                "unit_of_measurement": "fav unit",
                "value_template": "{{ value_json.val }}",
            }
        },
    )
    await opp.async_block_till_done()

    async_fire_mqtt_message.opp, "test-topic", '{ "val": "100" }')
    state = opp.states.get("sensor.test")

    assert state.state == "100"


async def test_force_update_disabled.opp, mqtt_mock):
    """Test force update option."""
    assert await async_setup_component(
        opp,
        sensor.DOMAIN,
        {
            sensor.DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "state_topic": "test-topic",
                "unit_of_measurement": "fav unit",
            }
        },
    )
    await opp.async_block_till_done()

    events = []

    @ha.callback
    def callback(event):
        events.append(event)

   .opp.bus.async_listen(EVENT_STATE_CHANGED, callback)

    async_fire_mqtt_message.opp, "test-topic", "100")
    await opp.async_block_till_done()
    assert len(events) == 1

    async_fire_mqtt_message.opp, "test-topic", "100")
    await opp.async_block_till_done()
    assert len(events) == 1


async def test_force_update_enabled.opp, mqtt_mock):
    """Test force update option."""
    assert await async_setup_component(
        opp,
        sensor.DOMAIN,
        {
            sensor.DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "state_topic": "test-topic",
                "unit_of_measurement": "fav unit",
                "force_update": True,
            }
        },
    )
    await opp.async_block_till_done()

    events = []

    @ha.callback
    def callback(event):
        events.append(event)

   .opp.bus.async_listen(EVENT_STATE_CHANGED, callback)

    async_fire_mqtt_message.opp, "test-topic", "100")
    await opp.async_block_till_done()
    assert len(events) == 1

    async_fire_mqtt_message.opp, "test-topic", "100")
    await opp.async_block_till_done()
    assert len(events) == 2


async def test_availability_when_connection_lost.opp, mqtt_mock):
    """Test availability after MQTT disconnection."""
    await help_test_availability_when_connection_lost(
        opp, mqtt_mock, sensor.DOMAIN, DEFAULT_CONFIG
    )


async def test_availability_without_topic.opp, mqtt_mock):
    """Test availability without defined availability topic."""
    await help_test_availability_without_topic(
        opp, mqtt_mock, sensor.DOMAIN, DEFAULT_CONFIG
    )


async def test_default_availability_payload.opp, mqtt_mock):
    """Test availability by default payload with defined topic."""
    await help_test_default_availability_payload(
        opp, mqtt_mock, sensor.DOMAIN, DEFAULT_CONFIG
    )


async def test_default_availability_list_payload.opp, mqtt_mock):
    """Test availability by default payload with defined topic."""
    await help_test_default_availability_list_payload(
        opp, mqtt_mock, sensor.DOMAIN, DEFAULT_CONFIG
    )


async def test_default_availability_list_payload_all.opp, mqtt_mock):
    """Test availability by default payload with defined topic."""
    await help_test_default_availability_list_payload_all(
        opp, mqtt_mock, sensor.DOMAIN, DEFAULT_CONFIG
    )


async def test_default_availability_list_payload_any.opp, mqtt_mock):
    """Test availability by default payload with defined topic."""
    await help_test_default_availability_list_payload_any(
        opp, mqtt_mock, sensor.DOMAIN, DEFAULT_CONFIG
    )


async def test_default_availability_list_single.opp, mqtt_mock, caplog):
    """Test availability list and availability_topic are mutually exclusive."""
    await help_test_default_availability_list_single(
        opp, mqtt_mock, caplog, sensor.DOMAIN, DEFAULT_CONFIG
    )


async def test_custom_availability_payload.opp, mqtt_mock):
    """Test availability by custom payload with defined topic."""
    await help_test_custom_availability_payload(
        opp, mqtt_mock, sensor.DOMAIN, DEFAULT_CONFIG
    )


async def test_discovery_update_availability.opp, mqtt_mock):
    """Test availability discovery update."""
    await help_test_discovery_update_availability(
        opp, mqtt_mock, sensor.DOMAIN, DEFAULT_CONFIG
    )


async def test_invalid_device_class.opp, mqtt_mock):
    """Test device_class option with invalid value."""
    assert await async_setup_component(
        opp,
        sensor.DOMAIN,
        {
            sensor.DOMAIN: {
                "platform": "mqtt",
                "name": "test",
                "state_topic": "test-topic",
                "device_class": "foobarnotreal",
            }
        },
    )
    await opp.async_block_till_done()

    state = opp.states.get("sensor.test")
    assert state is None


async def test_valid_device_class.opp, mqtt_mock):
    """Test device_class option with valid values."""
    assert await async_setup_component(
        opp,
        "sensor",
        {
            "sensor": [
                {
                    "platform": "mqtt",
                    "name": "Test 1",
                    "state_topic": "test-topic",
                    "device_class": "temperature",
                },
                {"platform": "mqtt", "name": "Test 2", "state_topic": "test-topic"},
            ]
        },
    )
    await opp.async_block_till_done()

    state = opp.states.get("sensor.test_1")
    assert state.attributes["device_class"] == "temperature"
    state = opp.states.get("sensor.test_2")
    assert "device_class" not in state.attributes


async def test_setting_attribute_via_mqtt_json_message.opp, mqtt_mock):
    """Test the setting of attribute via MQTT with JSON payload."""
    await help_test_setting_attribute_via_mqtt_json_message(
        opp, mqtt_mock, sensor.DOMAIN, DEFAULT_CONFIG
    )


async def test_setting_attribute_with_template.opp, mqtt_mock):
    """Test the setting of attribute via MQTT with JSON payload."""
    await help_test_setting_attribute_with_template(
        opp, mqtt_mock, sensor.DOMAIN, DEFAULT_CONFIG
    )


async def test_update_with_json_attrs_not_dict.opp, mqtt_mock, caplog):
    """Test attributes get extracted from a JSON result."""
    await help_test_update_with_json_attrs_not_dict(
        opp, mqtt_mock, caplog, sensor.DOMAIN, DEFAULT_CONFIG
    )


async def test_update_with_json_attrs_bad_JSON.opp, mqtt_mock, caplog):
    """Test attributes get extracted from a JSON result."""
    await help_test_update_with_json_attrs_bad_JSON(
        opp, mqtt_mock, caplog, sensor.DOMAIN, DEFAULT_CONFIG
    )


async def test_discovery_update_attr.opp, mqtt_mock, caplog):
    """Test update of discovered MQTTAttributes."""
    await help_test_discovery_update_attr(
        opp, mqtt_mock, caplog, sensor.DOMAIN, DEFAULT_CONFIG
    )


async def test_unique_id.opp, mqtt_mock):
    """Test unique id option only creates one sensor per unique_id."""
    config = {
        sensor.DOMAIN: [
            {
                "platform": "mqtt",
                "name": "Test 1",
                "state_topic": "test-topic",
                "unique_id": "TOTALLY_UNIQUE",
            },
            {
                "platform": "mqtt",
                "name": "Test 2",
                "state_topic": "test-topic",
                "unique_id": "TOTALLY_UNIQUE",
            },
        ]
    }
    await help_test_unique_id.opp, mqtt_mock, sensor.DOMAIN, config)


async def test_discovery_removal_sensor.opp, mqtt_mock, caplog):
    """Test removal of discovered sensor."""
    data = '{ "name": "test", "state_topic": "test_topic" }'
    await help_test_discovery_removal.opp, mqtt_mock, caplog, sensor.DOMAIN, data)


async def test_discovery_update_sensor_topic_template.opp, mqtt_mock, caplog):
    """Test update of discovered sensor."""
    config = {"name": "test", "state_topic": "test_topic"}
    config1 = copy.deepcopy(config)
    config2 = copy.deepcopy(config)
    config1["name"] = "Beer"
    config2["name"] = "Milk"
    config1["state_topic"] = "sensor/state1"
    config2["state_topic"] = "sensor/state2"
    config1["value_template"] = "{{ value_json.state | int }}"
    config2["value_template"] = "{{ value_json.state | int * 2 }}"

    state_data1 = [
        ([("sensor/state1", '{"state":100}')], "100", None),
    ]
    state_data2 = [
        ([("sensor/state1", '{"state":1000}')], "100", None),
        ([("sensor/state1", '{"state":1000}')], "100", None),
        ([("sensor/state2", '{"state":100}')], "200", None),
    ]

    data1 = json.dumps(config1)
    data2 = json.dumps(config2)
    await help_test_discovery_update(
        opp,
        mqtt_mock,
        caplog,
        sensor.DOMAIN,
        data1,
        data2,
        state_data1=state_data1,
        state_data2=state_data2,
    )


async def test_discovery_update_sensor_template.opp, mqtt_mock, caplog):
    """Test update of discovered sensor."""
    config = {"name": "test", "state_topic": "test_topic"}
    config1 = copy.deepcopy(config)
    config2 = copy.deepcopy(config)
    config1["name"] = "Beer"
    config2["name"] = "Milk"
    config1["state_topic"] = "sensor/state1"
    config2["state_topic"] = "sensor/state1"
    config1["value_template"] = "{{ value_json.state | int }}"
    config2["value_template"] = "{{ value_json.state | int * 2 }}"

    state_data1 = [
        ([("sensor/state1", '{"state":100}')], "100", None),
    ]
    state_data2 = [
        ([("sensor/state1", '{"state":100}')], "200", None),
    ]

    data1 = json.dumps(config1)
    data2 = json.dumps(config2)
    await help_test_discovery_update(
        opp,
        mqtt_mock,
        caplog,
        sensor.DOMAIN,
        data1,
        data2,
        state_data1=state_data1,
        state_data2=state_data2,
    )


async def test_discovery_update_unchanged_sensor.opp, mqtt_mock, caplog):
    """Test update of discovered sensor."""
    data1 = '{ "name": "Beer", "state_topic": "test_topic" }'
    with patch(
        "openpeerpower.components.mqtt.sensor.MqttSensor.discovery_update"
    ) as discovery_update:
        await help_test_discovery_update_unchanged(
            opp, mqtt_mock, caplog, sensor.DOMAIN, data1, discovery_update
        )


@pytest.mark.no_fail_on_log_exception
async def test_discovery_broken.opp, mqtt_mock, caplog):
    """Test handling of bad discovery message."""
    data1 = '{ "name": "Beer", "state_topic": "test_topic#" }'
    data2 = '{ "name": "Milk", "state_topic": "test_topic" }'
    await help_test_discovery_broken(
        opp, mqtt_mock, caplog, sensor.DOMAIN, data1, data2
    )


async def test_entity_device_info_with_connection.opp, mqtt_mock):
    """Test MQTT sensor device registry integration."""
    await help_test_entity_device_info_with_connection(
        opp, mqtt_mock, sensor.DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_device_info_with_identifier.opp, mqtt_mock):
    """Test MQTT sensor device registry integration."""
    await help_test_entity_device_info_with_identifier(
        opp, mqtt_mock, sensor.DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_device_info_update.opp, mqtt_mock):
    """Test device registry update."""
    await help_test_entity_device_info_update(
        opp, mqtt_mock, sensor.DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_device_info_remove.opp, mqtt_mock):
    """Test device registry remove."""
    await help_test_entity_device_info_remove(
        opp, mqtt_mock, sensor.DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_id_update_subscriptions.opp, mqtt_mock):
    """Test MQTT subscriptions are managed when entity_id is updated."""
    await help_test_entity_id_update_subscriptions(
        opp, mqtt_mock, sensor.DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_id_update_discovery_update.opp, mqtt_mock):
    """Test MQTT discovery update when entity_id is updated."""
    await help_test_entity_id_update_discovery_update(
        opp, mqtt_mock, sensor.DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_device_info_with_hub.opp, mqtt_mock):
    """Test MQTT sensor device registry integration."""
    registry = await opp.helpers.device_registry.async_get_registry()
    hub = registry.async_get_or_create(
        config_entry_id="123",
        connections=set(),
        identifiers={("mqtt", "hub-id")},
        manufacturer="manufacturer",
        model="hub",
    )

    data = json.dumps(
        {
            "platform": "mqtt",
            "name": "Test 1",
            "state_topic": "test-topic",
            "device": {"identifiers": ["helloworld"], "via_device": "hub-id"},
            "unique_id": "veryunique",
        }
    )
    async_fire_mqtt_message.opp, "openpeerpower/sensor/bla/config", data)
    await opp.async_block_till_done()

    device = registry.async_get_device({("mqtt", "helloworld")})
    assert device is not None
    assert device.via_device_id == hub.id


async def test_entity_debug_info.opp, mqtt_mock):
    """Test MQTT sensor debug info."""
    await help_test_entity_debug_info.opp, mqtt_mock, sensor.DOMAIN, DEFAULT_CONFIG)


async def test_entity_debug_info_max_messages.opp, mqtt_mock):
    """Test MQTT sensor debug info."""
    await help_test_entity_debug_info_max_messages(
        opp, mqtt_mock, sensor.DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_debug_info_message.opp, mqtt_mock):
    """Test MQTT debug info."""
    await help_test_entity_debug_info_message(
        opp, mqtt_mock, sensor.DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_debug_info_remove.opp, mqtt_mock):
    """Test MQTT sensor debug info."""
    await help_test_entity_debug_info_remove(
        opp, mqtt_mock, sensor.DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_debug_info_update_entity_id.opp, mqtt_mock):
    """Test MQTT sensor debug info."""
    await help_test_entity_debug_info_update_entity_id(
        opp, mqtt_mock, sensor.DOMAIN, DEFAULT_CONFIG
    )
