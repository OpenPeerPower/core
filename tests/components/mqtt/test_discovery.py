"""The tests for the MQTT discovery."""
from pathlib import Path
import re
from unittest.mock import AsyncMock, patch

import pytest

from openpeerpower import config_entries
from openpeerpower.components import mqtt
from openpeerpower.components.mqtt.abbreviations import (
    ABBREVIATIONS,
    DEVICE_ABBREVIATIONS,
)
from openpeerpower.components.mqtt.discovery import ALREADY_DISCOVERED, async_start
from openpeerpower.const import EVENT_STATE_CHANGED, STATE_OFF, STATE_ON
import openpeerpowerr.core as ha

from tests.common import (
    async_fire_mqtt_message,
    mock_device_registry,
    mock_entity_platform,
    mock_registry,
)


@pytest.fixture
def device_reg.opp):
    """Return an empty, loaded, registry."""
    return mock_device_registry.opp)


@pytest.fixture
def entity_reg.opp):
    """Return an empty, loaded, registry."""
    return mock_registry.opp)


@pytest.mark.parametrize(
    "mqtt_config",
    [{mqtt.CONF_BROKER: "mock-broker", mqtt.CONF_DISCOVERY: False}],
)
async def test_subscribing_config_topic.opp, mqtt_mock):
    """Test setting up discovery."""
    entry =.opp.config_entries.async_entries(mqtt.DOMAIN)[0]

    discovery_topic = "openpeerpowerr"
    await async_start.opp, discovery_topic, entry)

    call_args1 = mqtt_mock.async_subscribe.mock_calls[0][1]
    assert call_args1[2] == 0
    call_args2 = mqtt_mock.async_subscribe.mock_calls[1][1]
    assert call_args2[2] == 0
    topics = [call_args1[0], call_args2[0]]
    assert discovery_topic + "/+/+/config" in topics
    assert discovery_topic + "/+/+/+/config" in topics


async def test_invalid_topic.opp, mqtt_mock):
    """Test sending to invalid topic."""
    with patch(
        "openpeerpower.components.mqtt.discovery.async_dispatcher_send"
    ) as mock_dispatcher_send:
        mock_dispatcher_send = AsyncMock(return_value=None)

        async_fire_mqtt_message(
           .opp, "openpeerpower/binary_sensor/bla/not_config", "{}"
        )
        await.opp.async_block_till_done()
        assert not mock_dispatcher_send.called


async def test_invalid_json.opp, mqtt_mock, caplog):
    """Test sending in invalid JSON."""
    with patch(
        "openpeerpower.components.mqtt.discovery.async_dispatcher_send"
    ) as mock_dispatcher_send:

        mock_dispatcher_send = AsyncMock(return_value=None)

        async_fire_mqtt_message(
           .opp, "openpeerpower/binary_sensor/bla/config", "not json"
        )
        await.opp.async_block_till_done()
        assert "Unable to parse JSON" in caplog.text
        assert not mock_dispatcher_send.called


async def test_only_valid_components.opp, mqtt_mock, caplog):
    """Test for a valid component."""
    with patch(
        "openpeerpower.components.mqtt.discovery.async_dispatcher_send"
    ) as mock_dispatcher_send:

        invalid_component = "timer"

        mock_dispatcher_send = AsyncMock(return_value=None)

        async_fire_mqtt_message(
           .opp, f"openpeerpower/{invalid_component}/bla/config", "{}"
        )

    await.opp.async_block_till_done()

    assert f"Integration {invalid_component} is not supported" in caplog.text

    assert not mock_dispatcher_send.called


async def test_correct_config_discovery.opp, mqtt_mock, caplog):
    """Test sending in correct JSON."""
    async_fire_mqtt_message(
       .opp,
        "openpeerpower/binary_sensor/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic" }',
    )
    await.opp.async_block_till_done()

    state =.opp.states.get("binary_sensor.beer")

    assert state is not None
    assert state.name == "Beer"
    assert ("binary_sensor", "bla") in.opp.data[ALREADY_DISCOVERED]


async def test_discover_fan.opp, mqtt_mock, caplog):
    """Test discovering an MQTT fan."""
    async_fire_mqtt_message(
       .opp,
        "openpeerpower/fan/bla/config",
        ('{ "name": "Beer",' '  "command_topic": "test_topic" }'),
    )
    await.opp.async_block_till_done()

    state =.opp.states.get("fan.beer")

    assert state is not None
    assert state.name == "Beer"
    assert ("fan", "bla") in.opp.data[ALREADY_DISCOVERED]


async def test_discover_climate.opp, mqtt_mock, caplog):
    """Test discovering an MQTT climate component."""
    data = (
        '{ "name": "ClimateTest",'
        '  "current_temperature_topic": "climate/bla/current_temp",'
        '  "temperature_command_topic": "climate/bla/target_temp" }'
    )

    async_fire_mqtt_message.opp, "openpeerpower/climate/bla/config", data)
    await.opp.async_block_till_done()

    state =.opp.states.get("climate.ClimateTest")

    assert state is not None
    assert state.name == "ClimateTest"
    assert ("climate", "bla") in.opp.data[ALREADY_DISCOVERED]


async def test_discover_alarm_control_panel.opp, mqtt_mock, caplog):
    """Test discovering an MQTT alarm control panel component."""
    data = (
        '{ "name": "AlarmControlPanelTest",'
        '  "state_topic": "test_topic",'
        '  "command_topic": "test_topic" }'
    )

    async_fire_mqtt_message.opp, "openpeerpower/alarm_control_panel/bla/config", data)
    await.opp.async_block_till_done()

    state =.opp.states.get("alarm_control_panel.AlarmControlPanelTest")

    assert state is not None
    assert state.name == "AlarmControlPanelTest"
    assert ("alarm_control_panel", "bla") in.opp.data[ALREADY_DISCOVERED]


async def test_discovery_incl_nodeid.opp, mqtt_mock, caplog):
    """Test sending in correct JSON with optional node_id included."""
    async_fire_mqtt_message(
       .opp,
        "openpeerpower/binary_sensor/my_node_id/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic" }',
    )
    await.opp.async_block_till_done()

    state =.opp.states.get("binary_sensor.beer")

    assert state is not None
    assert state.name == "Beer"
    assert ("binary_sensor", "my_node_id bla") in.opp.data[ALREADY_DISCOVERED]


async def test_non_duplicate_discovery.opp, mqtt_mock, caplog):
    """Test for a non duplicate component."""
    async_fire_mqtt_message(
       .opp,
        "openpeerpower/binary_sensor/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic" }',
    )
    async_fire_mqtt_message(
       .opp,
        "openpeerpower/binary_sensor/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic" }',
    )
    await.opp.async_block_till_done()

    state =.opp.states.get("binary_sensor.beer")
    state_duplicate =.opp.states.get("binary_sensor.beer1")

    assert state is not None
    assert state.name == "Beer"
    assert state_duplicate is None
    assert "Component has already been discovered: binary_sensor bla" in caplog.text


async def test_removal.opp, mqtt_mock, caplog):
    """Test removal of component through empty discovery message."""
    async_fire_mqtt_message(
       .opp,
        "openpeerpower/binary_sensor/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic" }',
    )
    await.opp.async_block_till_done()
    state =.opp.states.get("binary_sensor.beer")
    assert state is not None

    async_fire_mqtt_message.opp, "openpeerpower/binary_sensor/bla/config", "")
    await.opp.async_block_till_done()
    state =.opp.states.get("binary_sensor.beer")
    assert state is None


async def test_rediscover.opp, mqtt_mock, caplog):
    """Test rediscover of removed component."""
    async_fire_mqtt_message(
       .opp,
        "openpeerpower/binary_sensor/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic" }',
    )
    await.opp.async_block_till_done()
    state =.opp.states.get("binary_sensor.beer")
    assert state is not None

    async_fire_mqtt_message.opp, "openpeerpower/binary_sensor/bla/config", "")
    await.opp.async_block_till_done()
    state =.opp.states.get("binary_sensor.beer")
    assert state is None

    async_fire_mqtt_message(
       .opp,
        "openpeerpower/binary_sensor/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic" }',
    )
    await.opp.async_block_till_done()
    state =.opp.states.get("binary_sensor.beer")
    assert state is not None


async def test_rapid_rediscover.opp, mqtt_mock, caplog):
    """Test immediate rediscover of removed component."""

    events = []

    @op.callback
    def callback(event):
        """Verify event got called."""
        events.append(event)

   .opp.bus.async_listen(EVENT_STATE_CHANGED, callback)

    async_fire_mqtt_message(
       .opp,
        "openpeerpower/binary_sensor/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic" }',
    )
    await.opp.async_block_till_done()
    state =.opp.states.get("binary_sensor.beer")
    assert state is not None
    assert len(events) == 1

    # Removal immediately followed by rediscover
    async_fire_mqtt_message.opp, "openpeerpower/binary_sensor/bla/config", "")
    async_fire_mqtt_message(
       .opp,
        "openpeerpower/binary_sensor/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic" }',
    )
    async_fire_mqtt_message.opp, "openpeerpower/binary_sensor/bla/config", "")
    async_fire_mqtt_message(
       .opp,
        "openpeerpower/binary_sensor/bla/config",
        '{ "name": "Milk", "state_topic": "test-topic" }',
    )
    await.opp.async_block_till_done()

    assert len.opp.states.async_entity_ids("binary_sensor")) == 1
    state =.opp.states.get("binary_sensor.milk")
    assert state is not None

    assert len(events) == 5
    # Remove the entity
    assert events[1].data["entity_id"] == "binary_sensor.beer"
    assert events[1].data["new_state"] is None
    # Add the entity
    assert events[2].data["entity_id"] == "binary_sensor.beer"
    assert events[2].data["old_state"] is None
    # Remove the entity
    assert events[3].data["entity_id"] == "binary_sensor.beer"
    assert events[3].data["new_state"] is None
    # Add the entity
    assert events[4].data["entity_id"] == "binary_sensor.milk"
    assert events[4].data["old_state"] is None


async def test_rapid_rediscover_unique.opp, mqtt_mock, caplog):
    """Test immediate rediscover of removed component."""

    events = []

    @op.callback
    def callback(event):
        """Verify event got called."""
        events.append(event)

   .opp.bus.async_listen(EVENT_STATE_CHANGED, callback)

    async_fire_mqtt_message(
       .opp,
        "openpeerpower/binary_sensor/bla2/config",
        '{ "name": "Ale", "state_topic": "test-topic", "unique_id": "very_unique" }',
    )
    await.opp.async_block_till_done()
    state =.opp.states.get("binary_sensor.ale")
    assert state is not None
    assert len(events) == 1

    # Duplicate unique_id, immediately followed by correct unique_id
    async_fire_mqtt_message(
       .opp,
        "openpeerpower/binary_sensor/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic", "unique_id": "very_unique" }',
    )
    async_fire_mqtt_message(
       .opp,
        "openpeerpower/binary_sensor/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic", "unique_id": "even_uniquer" }',
    )
    async_fire_mqtt_message.opp, "openpeerpower/binary_sensor/bla/config", "")
    async_fire_mqtt_message(
       .opp,
        "openpeerpower/binary_sensor/bla/config",
        '{ "name": "Milk", "state_topic": "test-topic", "unique_id": "even_uniquer" }',
    )
    await.opp.async_block_till_done()

    assert len.opp.states.async_entity_ids("binary_sensor")) == 2
    state =.opp.states.get("binary_sensor.ale")
    assert state is not None
    state =.opp.states.get("binary_sensor.milk")
    assert state is not None

    assert len(events) == 4
    # Add the entity
    assert events[1].data["entity_id"] == "binary_sensor.beer"
    assert events[1].data["old_state"] is None
    # Remove the entity
    assert events[2].data["entity_id"] == "binary_sensor.beer"
    assert events[2].data["new_state"] is None
    # Add the entity
    assert events[3].data["entity_id"] == "binary_sensor.milk"
    assert events[3].data["old_state"] is None


async def test_duplicate_removal.opp, mqtt_mock, caplog):
    """Test for a non duplicate component."""
    async_fire_mqtt_message(
       .opp,
        "openpeerpower/binary_sensor/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic" }',
    )
    await.opp.async_block_till_done()
    async_fire_mqtt_message.opp, "openpeerpower/binary_sensor/bla/config", "")
    await.opp.async_block_till_done()
    assert "Component has already been discovered: binary_sensor bla" in caplog.text
    caplog.clear()
    async_fire_mqtt_message.opp, "openpeerpower/binary_sensor/bla/config", "")
    await.opp.async_block_till_done()

    assert "Component has already been discovered: binary_sensor bla" not in caplog.text


async def test_cleanup_device.opp, device_reg, entity_reg, mqtt_mock):
    """Test discvered device is cleaned up when removed from registry."""
    data = (
        '{ "device":{"identifiers":["0AFFD2"]},'
        '  "state_topic": "foobar/sensor",'
        '  "unique_id": "unique" }'
    )

    async_fire_mqtt_message.opp, "openpeerpower/sensor/bla/config", data)
    await.opp.async_block_till_done()

    # Verify device and registry entries are created
    device_entry = device_reg.async_get_device({("mqtt", "0AFFD2")})
    assert device_entry is not None
    entity_entry = entity_reg.async_get("sensor.mqtt_sensor")
    assert entity_entry is not None

    state =.opp.states.get("sensor.mqtt_sensor")
    assert state is not None

    device_reg.async_remove_device(device_entry.id)
    await.opp.async_block_till_done()
    await.opp.async_block_till_done()

    # Verify device and registry entries are cleared
    device_entry = device_reg.async_get_device({("mqtt", "0AFFD2")})
    assert device_entry is None
    entity_entry = entity_reg.async_get("sensor.mqtt_sensor")
    assert entity_entry is None

    # Verify state is removed
    state =.opp.states.get("sensor.mqtt_sensor")
    assert state is None
    await.opp.async_block_till_done()

    # Verify retained discovery topic has been cleared
    mqtt_mock.async_publish.assert_called_once_with(
        "openpeerpower/sensor/bla/config", "", 0, True
    )


async def test_discovery_expansion.opp, mqtt_mock, caplog):
    """Test expansion of abbreviated discovery payload."""
    data = (
        '{ "~": "some/base/topic",'
        '  "name": "DiscoveryExpansionTest1",'
        '  "stat_t": "test_topic/~",'
        '  "cmd_t": "~/test_topic",'
        '  "dev":{'
        '    "ids":["5706DF"],'
        '    "name":"DiscoveryExpansionTest1 Device",'
        '    "mdl":"Generic",'
        '    "sw":"1.2.3.4",'
        '    "mf":"None"'
        "  }"
        "}"
    )

    async_fire_mqtt_message.opp, "openpeerpower/switch/bla/config", data)
    await.opp.async_block_till_done()

    state =.opp.states.get("switch.DiscoveryExpansionTest1")
    assert state is not None
    assert state.name == "DiscoveryExpansionTest1"
    assert ("switch", "bla") in.opp.data[ALREADY_DISCOVERED]
    assert state.state == STATE_OFF

    async_fire_mqtt_message.opp, "test_topic/some/base/topic", "ON")

    state =.opp.states.get("switch.DiscoveryExpansionTest1")
    assert state.state == STATE_ON


ABBREVIATIONS_WHITE_LIST = [
    # MQTT client/server/trigger settings
    "CONF_BIRTH_MESSAGE",
    "CONF_BROKER",
    "CONF_CERTIFICATE",
    "CONF_CLIENT_CERT",
    "CONF_CLIENT_ID",
    "CONF_CLIENT_KEY",
    "CONF_DISCOVERY",
    "CONF_DISCOVERY_ID",
    "CONF_DISCOVERY_PREFIX",
    "CONF_EMBEDDED",
    "CONF_KEEPALIVE",
    "CONF_TLS_INSECURE",
    "CONF_TLS_VERSION",
    "CONF_WILL_MESSAGE",
    # Undocumented device configuration
    "CONF_DEPRECATED_VIA_HUB",
    "CONF_VIA_DEVICE",
    # Already short
    "CONF_FAN_MODE_LIST",
    "CONF_HOLD_LIST",
    "CONF_HS",
    "CONF_MODE_LIST",
    "CONF_PRECISION",
    "CONF_QOS",
    "CONF_SCHEMA",
    "CONF_SWING_MODE_LIST",
    "CONF_TEMP_STEP",
]


async def test_missing_discover_abbreviations.opp, mqtt_mock, caplog):
    """Check MQTT platforms for missing abbreviations."""
    missing = []
    regex = re.compile(r"(CONF_[a-zA-Z\d_]*) *= *[\'\"]([a-zA-Z\d_]*)[\'\"]")
    for fil in Path(mqtt.__file__).parent.rglob("*.py"):
        if fil.name == "trigger.py":
            continue
        with open(fil) as file:
            matches = re.findall(regex, file.read())
            for match in matches:
                if (
                    match[1] not in ABBREVIATIONS.values()
                    and match[1] not in DEVICE_ABBREVIATIONS.values()
                    and match[0] not in ABBREVIATIONS_WHITE_LIST
                ):
                    missing.append(
                        "{}: no abbreviation for {} ({})".format(
                            fil, match[1], match[0]
                        )
                    )

    assert not missing


async def test_no_implicit_state_topic_switch.opp, mqtt_mock, caplog):
    """Test no implicit state topic for switch."""
    data = '{ "name": "Test1",' '  "command_topic": "cmnd"' "}"

    async_fire_mqtt_message.opp, "openpeerpower/switch/bla/config", data)
    await.opp.async_block_till_done()
    assert "implicit state_topic is deprecated" not in caplog.text

    state =.opp.states.get("switch.Test1")
    assert state is not None
    assert state.name == "Test1"
    assert ("switch", "bla") in.opp.data[ALREADY_DISCOVERED]
    assert state.state == "off"
    assert state.attributes["assumed_state"] is True

    async_fire_mqtt_message.opp, "openpeerpower/switch/bla/state", "ON")

    state =.opp.states.get("switch.Test1")
    assert state.state == "off"


@pytest.mark.parametrize(
    "mqtt_config",
    [
        {
            mqtt.CONF_BROKER: "mock-broker",
            mqtt.CONF_DISCOVERY_PREFIX: "my_home/openpeerpower/register",
        }
    ],
)
async def test_complex_discovery_topic_prefix.opp, mqtt_mock, caplog):
    """Tests handling of discovery topic prefix with multiple slashes."""
    async_fire_mqtt_message(
       .opp,
        ("my_home/openpeerpower/register/binary_sensor/node1/object1/config"),
        '{ "name": "Beer", "state_topic": "test-topic" }',
    )
    await.opp.async_block_till_done()

    state =.opp.states.get("binary_sensor.beer")

    assert state is not None
    assert state.name == "Beer"
    assert ("binary_sensor", "node1 object1") in.opp.data[ALREADY_DISCOVERED]


async def test_mqtt_integration_discovery_subscribe_unsubscribe(
   .opp, mqtt_client_mock, mqtt_mock
):
    """Check MQTT integration discovery subscribe and unsubscribe."""
    mock_entity_platform.opp, "config_flow.comp", None)

    entry =.opp.config_entries.async_entries("mqtt")[0]
    mqtt_mock().connected = True

    with patch(
        "openpeerpower.components.mqtt.discovery.async_get_mqtt",
        return_value={"comp": ["comp/discovery/#"]},
    ):
        await async_start.opp, "openpeerpowerr", entry)
        await.opp.async_block_till_done()

    mqtt_client_mock.subscribe.assert_any_call("comp/discovery/#", 0)
    assert not mqtt_client_mock.unsubscribe.called

    class TestFlow(config_entries.ConfigFlow):
        """Test flow."""

        async def async_step_mqtt(self, discovery_info):
            """Test mqtt step."""
            return self.async_abort(reason="already_configured")

    with patch.dict(config_entries.HANDLERS, {"comp": TestFlow}):
        mqtt_client_mock.subscribe.assert_any_call("comp/discovery/#", 0)
        assert not mqtt_client_mock.unsubscribe.called

        async_fire_mqtt_message.opp, "comp/discovery/bla/config", "")
        await.opp.async_block_till_done()
        mqtt_client_mock.unsubscribe.assert_called_once_with("comp/discovery/#")
        mqtt_client_mock.unsubscribe.reset_mock()

        async_fire_mqtt_message.opp, "comp/discovery/bla/config", "")
        await.opp.async_block_till_done()
        assert not mqtt_client_mock.unsubscribe.called


async def test_mqtt_discovery_unsubscribe_once.opp, mqtt_client_mock, mqtt_mock):
    """Check MQTT integration discovery unsubscribe once."""
    mock_entity_platform.opp, "config_flow.comp", None)

    entry =.opp.config_entries.async_entries("mqtt")[0]
    mqtt_mock().connected = True

    with patch(
        "openpeerpower.components.mqtt.discovery.async_get_mqtt",
        return_value={"comp": ["comp/discovery/#"]},
    ):
        await async_start.opp, "openpeerpowerr", entry)
        await.opp.async_block_till_done()

    mqtt_client_mock.subscribe.assert_any_call("comp/discovery/#", 0)
    assert not mqtt_client_mock.unsubscribe.called

    class TestFlow(config_entries.ConfigFlow):
        """Test flow."""

        async def async_step_mqtt(self, discovery_info):
            """Test mqtt step."""
            return self.async_abort(reason="already_configured")

    with patch.dict(config_entries.HANDLERS, {"comp": TestFlow}):
        async_fire_mqtt_message.opp, "comp/discovery/bla/config", "")
        async_fire_mqtt_message.opp, "comp/discovery/bla/config", "")
        await.opp.async_block_till_done()
        await.opp.async_block_till_done()
        mqtt_client_mock.unsubscribe.assert_called_once_with("comp/discovery/#")
