"""The tests for the Tasmota fan platform."""
import copy
import json
from unittest.mock import patch

from hatasmota.utils import (
    get_topic_stat_result,
    get_topic_tele_state,
    get_topic_tele_will,
)
import pytest

from openpeerpower.components import fan
from openpeerpower.components.tasmota.const import DEFAULT_PREFIX
from openpeerpower.const import ATTR_ASSUMED_STATE, STATE_OFF, STATE_ON

from .test_common import (
    DEFAULT_CONFIG,
    help_test_availability,
    help_test_availability_discovery_update,
    help_test_availability_poll_state,
    help_test_availability_when_connection_lost,
    help_test_discovery_device_remove,
    help_test_discovery_removal,
    help_test_discovery_update_unchanged,
    help_test_entity_id_update_discovery_update,
    help_test_entity_id_update_subscriptions,
)

from tests.common import async_fire_mqtt_message
from tests.components.fan import common


async def test_controlling_state_via_mqtt.opp, mqtt_mock, setup_tasmota):
    """Test state update via MQTT."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["if"] = 1
    mac = config["mac"]

    async_fire_mqtt_message(
        opp,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await opp.async_block_till_done()

    state = opp.states.get("fan.tasmota")
    assert state.state == "unavailable"
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message.opp, "tasmota_49A3BC/tele/LWT", "Online")
    state = opp.states.get("fan.tasmota")
    assert state.state == STATE_OFF
    assert state.attributes["speed"] is None
    assert state.attributes["speed_list"] == ["off", "low", "medium", "high"]
    assert state.attributes["supported_features"] == fan.SUPPORT_SET_SPEED
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message.opp, "tasmota_49A3BC/tele/STATE", '{"FanSpeed":1}')
    state = opp.states.get("fan.tasmota")
    assert state.state == STATE_ON
    assert state.attributes["speed"] == "low"

    async_fire_mqtt_message.opp, "tasmota_49A3BC/tele/STATE", '{"FanSpeed":2}')
    state = opp.states.get("fan.tasmota")
    assert state.state == STATE_ON
    assert state.attributes["speed"] == "medium"

    async_fire_mqtt_message.opp, "tasmota_49A3BC/tele/STATE", '{"FanSpeed":3}')
    state = opp.states.get("fan.tasmota")
    assert state.state == STATE_ON
    assert state.attributes["speed"] == "high"

    async_fire_mqtt_message.opp, "tasmota_49A3BC/tele/STATE", '{"FanSpeed":0}')
    state = opp.states.get("fan.tasmota")
    assert state.state == STATE_OFF
    assert state.attributes["speed"] == "off"

    async_fire_mqtt_message.opp, "tasmota_49A3BC/stat/RESULT", '{"FanSpeed":1}')
    state = opp.states.get("fan.tasmota")
    assert state.state == STATE_ON
    assert state.attributes["speed"] == "low"

    async_fire_mqtt_message.opp, "tasmota_49A3BC/stat/RESULT", '{"FanSpeed":0}')
    state = opp.states.get("fan.tasmota")
    assert state.state == STATE_OFF
    assert state.attributes["speed"] == "off"


async def test_sending_mqtt_commands.opp, mqtt_mock, setup_tasmota):
    """Test the sending MQTT commands."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["if"] = 1
    mac = config["mac"]

    async_fire_mqtt_message(
        opp,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await opp.async_block_till_done()

    async_fire_mqtt_message.opp, "tasmota_49A3BC/tele/LWT", "Online")
    state = opp.states.get("fan.tasmota")
    assert state.state == STATE_OFF
    await opp.async_block_till_done()
    await opp.async_block_till_done()
    mqtt_mock.async_publish.reset_mock()

    # Turn the fan on and verify MQTT message is sent
    await common.async_turn_on.opp, "fan.tasmota")
    mqtt_mock.async_publish.assert_called_once_with(
        "tasmota_49A3BC/cmnd/FanSpeed", "2", 0, False
    )
    mqtt_mock.async_publish.reset_mock()

    # Tasmota is not optimistic, the state should still be off
    state = opp.states.get("fan.tasmota")
    assert state.state == STATE_OFF

    # Turn the fan off and verify MQTT message is sent
    await common.async_turn_off.opp, "fan.tasmota")
    mqtt_mock.async_publish.assert_called_once_with(
        "tasmota_49A3BC/cmnd/FanSpeed", "0", 0, False
    )
    mqtt_mock.async_publish.reset_mock()

    # Set speed  and verify MQTT message is sent
    await common.async_set_speed.opp, "fan.tasmota", fan.SPEED_OFF)
    mqtt_mock.async_publish.assert_called_once_with(
        "tasmota_49A3BC/cmnd/FanSpeed", "0", 0, False
    )
    mqtt_mock.async_publish.reset_mock()

    # Set speed  and verify MQTT message is sent
    await common.async_set_speed.opp, "fan.tasmota", fan.SPEED_LOW)
    mqtt_mock.async_publish.assert_called_once_with(
        "tasmota_49A3BC/cmnd/FanSpeed", "1", 0, False
    )
    mqtt_mock.async_publish.reset_mock()

    # Set speed  and verify MQTT message is sent
    await common.async_set_speed.opp, "fan.tasmota", fan.SPEED_MEDIUM)
    mqtt_mock.async_publish.assert_called_once_with(
        "tasmota_49A3BC/cmnd/FanSpeed", "2", 0, False
    )
    mqtt_mock.async_publish.reset_mock()

    # Set speed  and verify MQTT message is sent
    await common.async_set_speed.opp, "fan.tasmota", fan.SPEED_HIGH)
    mqtt_mock.async_publish.assert_called_once_with(
        "tasmota_49A3BC/cmnd/FanSpeed", "3", 0, False
    )


async def test_invalid_fan_speed.opp, mqtt_mock, setup_tasmota):
    """Test the sending MQTT commands."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["if"] = 1
    mac = config["mac"]

    async_fire_mqtt_message(
        opp,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await opp.async_block_till_done()

    async_fire_mqtt_message.opp, "tasmota_49A3BC/tele/LWT", "Online")
    state = opp.states.get("fan.tasmota")
    assert state.state == STATE_OFF
    await opp.async_block_till_done()
    await opp.async_block_till_done()
    mqtt_mock.async_publish.reset_mock()

    # Set an unsupported speed and verify MQTT message is not sent
    with pytest.raises(ValueError) as excinfo:
        await common.async_set_speed.opp, "fan.tasmota", "no_such_speed")
    assert "Unsupported speed no_such_speed" in str(excinfo.value)
    mqtt_mock.async_publish.assert_not_called()


async def test_availability_when_connection_lost(
    opp. mqtt_client_mock, mqtt_mock, setup_tasmota
):
    """Test availability after MQTT disconnection."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["dn"] = "Test"
    config["if"] = 1
    await help_test_availability_when_connection_lost(
        opp. mqtt_client_mock, mqtt_mock, fan.DOMAIN, config
    )


async def test_availability.opp, mqtt_mock, setup_tasmota):
    """Test availability."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["dn"] = "Test"
    config["if"] = 1
    await help_test_availability.opp, mqtt_mock, fan.DOMAIN, config)


async def test_availability_discovery_update.opp, mqtt_mock, setup_tasmota):
    """Test availability discovery update."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["dn"] = "Test"
    config["if"] = 1
    await help_test_availability_discovery_update.opp, mqtt_mock, fan.DOMAIN, config)


async def test_availability_poll_state(
    opp. mqtt_client_mock, mqtt_mock, setup_tasmota
):
    """Test polling after MQTT connection (re)established."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["if"] = 1
    poll_topic = "tasmota_49A3BC/cmnd/STATE"
    await help_test_availability_poll_state(
        opp. mqtt_client_mock, mqtt_mock, fan.DOMAIN, config, poll_topic, ""
    )


async def test_discovery_removal_fan.opp, mqtt_mock, caplog, setup_tasmota):
    """Test removal of discovered fan."""
    config1 = copy.deepcopy(DEFAULT_CONFIG)
    config1["dn"] = "Test"
    config1["if"] = 1
    config2 = copy.deepcopy(DEFAULT_CONFIG)
    config2["dn"] = "Test"
    config2["if"] = 0

    await help_test_discovery_removal(
        opp. mqtt_mock, caplog, fan.DOMAIN, config1, config2
    )


async def test_discovery_update_unchanged_fan.opp, mqtt_mock, caplog, setup_tasmota):
    """Test update of discovered fan."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["dn"] = "Test"
    config["if"] = 1
    with patch(
        "openpeerpower.components.tasmota.fan.TasmotaFan.discovery_update"
    ) as discovery_update:
        await help_test_discovery_update_unchanged(
            opp. mqtt_mock, caplog, fan.DOMAIN, config, discovery_update
        )


async def test_discovery_device_remove.opp, mqtt_mock, setup_tasmota):
    """Test device registry remove."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["dn"] = "Test"
    config["if"] = 1
    unique_id = f"{DEFAULT_CONFIG['mac']}_fan_fan_ifan"
    await help_test_discovery_device_remove(
        opp. mqtt_mock, fan.DOMAIN, unique_id, config
    )


async def test_entity_id_update_subscriptions.opp, mqtt_mock, setup_tasmota):
    """Test MQTT subscriptions are managed when entity_id is updated."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["dn"] = "Test"
    config["if"] = 1
    topics = [
        get_topic_stat_result(config),
        get_topic_tele_state(config),
        get_topic_tele_will(config),
    ]
    await help_test_entity_id_update_subscriptions(
        opp. mqtt_mock, fan.DOMAIN, config, topics
    )


async def test_entity_id_update_discovery_update.opp, mqtt_mock, setup_tasmota):
    """Test MQTT discovery update when entity_id is updated."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["dn"] = "Test"
    config["if"] = 1
    await help_test_entity_id_update_discovery_update(
        opp. mqtt_mock, fan.DOMAIN, config
    )
