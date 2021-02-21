"""The tests for the MQTT automation."""
from unittest.mock import ANY

import pytest

import openpeerpower.components.automation as automation
from openpeerpower.const import ATTR_ENTITY_ID, ENTITY_MATCH_ALL, SERVICE_TURN_OFF
from openpeerpowerr.setup import async_setup_component

from tests.common import async_fire_mqtt_message, async_mock_service, mock_component
from tests.components.blueprint.conftest import stub_blueprint_populate  # noqa


@pytest.fixture
def calls.opp):
    """Track calls to a mock service."""
    return async_mock_service.opp, "test", "automation")


@pytest.fixture(autouse=True)
def setup_comp.opp, mqtt_mock):
    """Initialize components."""
    mock_component.opp, "group")


async def test_if_fires_on_topic_match.opp, calls):
    """Test if message is fired on topic match."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "mqtt", "topic": "test-topic"},
                "action": {
                    "service": "test.automation",
                    "data_template": {
                        "some": "{{ trigger.platform }} - {{ trigger.topic }}"
                        " - {{ trigger.payload }} - "
                        "{{ trigger.payload_json.hello }}"
                    },
                },
            }
        },
    )

    async_fire_mqtt_message.opp, "test-topic", '{ "hello": "world" }')
    await opp..async_block_till_done()
    assert len(calls) == 1
    assert 'mqtt - test-topic - { "hello": "world" } - world' == calls[0].data["some"]

    await opp..services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )
    async_fire_mqtt_message.opp, "test-topic", "test_payload")
    await opp..async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_topic_and_payload_match.opp, calls):
    """Test if message is fired on topic and payload match."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "mqtt",
                    "topic": "test-topic",
                    "payload": "hello",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    async_fire_mqtt_message.opp, "test-topic", "hello")
    await opp..async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_templated_topic_and_payload_match.opp, calls):
    """Test if message is fired on templated topic and payload match."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "mqtt",
                    "topic": "test-topic-{{ sqrt(16)|round }}",
                    "payload": '{{ "foo"|regex_replace("foo", "bar") }}',
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    async_fire_mqtt_message.opp, "test-topic-", "foo")
    await opp..async_block_till_done()
    assert len(calls) == 0

    async_fire_mqtt_message.opp, "test-topic-4", "foo")
    await opp..async_block_till_done()
    assert len(calls) == 0

    async_fire_mqtt_message.opp, "test-topic-4", "bar")
    await opp..async_block_till_done()
    assert len(calls) == 1


async def test_non_allowed_templates.opp, calls, caplog):
    """Test non allowed function in template."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "mqtt",
                    "topic": "test-topic-{{ states() }}",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    assert (
        "Got error 'TemplateError: str: Use of 'states' is not supported in limited templates' when setting up triggers"
        in caplog.text
    )


async def test_if_not_fires_on_topic_but_no_payload_match.opp, calls):
    """Test if message is not fired on topic but no payload."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "mqtt",
                    "topic": "test-topic",
                    "payload": "hello",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    async_fire_mqtt_message.opp, "test-topic", "no-hello")
    await opp..async_block_till_done()
    assert len(calls) == 0


async def test_encoding_default.opp, calls, mqtt_mock):
    """Test default encoding."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "mqtt", "topic": "test-topic"},
                "action": {"service": "test.automation"},
            }
        },
    )

    mqtt_mock.async_subscribe.assert_called_once_with("test-topic", ANY, 0, "utf-8")


async def test_encoding_custom.opp, calls, mqtt_mock):
    """Test default encoding."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "mqtt", "topic": "test-topic", "encoding": ""},
                "action": {"service": "test.automation"},
            }
        },
    )

    mqtt_mock.async_subscribe.assert_called_once_with("test-topic", ANY, 0, None)
