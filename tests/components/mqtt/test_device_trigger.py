"""The tests for MQTT device triggers."""
import json

import pytest

import openpeerpower.components.automation as automation
from openpeerpower.components.mqtt import DOMAIN, debug_info
from openpeerpower.components.mqtt.device_trigger import async_attach_trigger
from openpeerpower.setup import async_setup_component

from tests.common import (
    assert_lists_same,
    async_fire_mqtt_message,
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


async def test_get_triggers(opp, device_reg, entity_reg, mqtt_mock):
    """Test we get the expected triggers from a discovered mqtt device."""
    data1 = (
        '{ "automation_type":"trigger",'
        '  "device":{"identifiers":["0AFFD2"]},'
        '  "payload": "short_press",'
        '  "topic": "foobar/triggers/button1",'
        '  "type": "button_short_press",'
        '  "subtype": "button_1" }'
    )
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla/config", data1)
    await opp.async_block_till_done()

    device_entry = device_reg.async_get_device({("mqtt", "0AFFD2")})
    expected_triggers = [
        {
            "platform": "device",
            "domain": DOMAIN,
            "device_id": device_entry.id,
            "discovery_id": "bla",
            "type": "button_short_press",
            "subtype": "button_1",
        },
    ]
    triggers = await async_get_device_automations(opp, "trigger", device_entry.id)
    assert_lists_same(triggers, expected_triggers)


async def test_get_unknown_triggers(opp, device_reg, entity_reg, mqtt_mock):
    """Test we don't get unknown triggers."""
    # Discover a sensor (without device triggers)
    data1 = (
        '{ "device":{"identifiers":["0AFFD2"]},'
        '  "state_topic": "foobar/sensor",'
        '  "unique_id": "unique" }'
    )
    async_fire_mqtt_message(opp, "openpeerpower/sensor/bla/config", data1)
    await opp.async_block_till_done()

    device_entry = device_reg.async_get_device({("mqtt", "0AFFD2")})

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "bla1",
                        "type": "button_short_press",
                        "subtype": "button_1",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("short_press")},
                    },
                },
            ]
        },
    )

    triggers = await async_get_device_automations(opp, "trigger", device_entry.id)
    assert_lists_same(triggers, [])


async def test_get_non_existing_triggers(opp, device_reg, entity_reg, mqtt_mock):
    """Test getting non existing triggers."""
    # Discover a sensor (without device triggers)
    data1 = (
        '{ "device":{"identifiers":["0AFFD2"]},'
        '  "state_topic": "foobar/sensor",'
        '  "unique_id": "unique" }'
    )
    async_fire_mqtt_message(opp, "openpeerpower/sensor/bla/config", data1)
    await opp.async_block_till_done()

    device_entry = device_reg.async_get_device({("mqtt", "0AFFD2")})
    triggers = await async_get_device_automations(opp, "trigger", device_entry.id)
    assert_lists_same(triggers, [])


@pytest.mark.no_fail_on_log_exception
async def test_discover_bad_triggers(opp, device_reg, entity_reg, mqtt_mock):
    """Test bad discovery message."""
    # Test sending bad data
    data0 = (
        '{ "automation_type":"trigger",'
        '  "device":{"identifiers":["0AFFD2"]},'
        '  "payloads": "short_press",'
        '  "topic": "foobar/triggers/button1",'
        '  "type": "button_short_press",'
        '  "subtype": "button_1" }'
    )
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla/config", data0)
    await opp.async_block_till_done()
    assert device_reg.async_get_device({("mqtt", "0AFFD2")}) is None

    # Test sending correct data
    data1 = (
        '{ "automation_type":"trigger",'
        '  "device":{"identifiers":["0AFFD2"]},'
        '  "payload": "short_press",'
        '  "topic": "foobar/triggers/button1",'
        '  "type": "button_short_press",'
        '  "subtype": "button_1" }'
    )
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla/config", data1)
    await opp.async_block_till_done()

    device_entry = device_reg.async_get_device({("mqtt", "0AFFD2")})
    expected_triggers = [
        {
            "platform": "device",
            "domain": DOMAIN,
            "device_id": device_entry.id,
            "discovery_id": "bla",
            "type": "button_short_press",
            "subtype": "button_1",
        },
    ]
    triggers = await async_get_device_automations(opp, "trigger", device_entry.id)
    assert_lists_same(triggers, expected_triggers)


async def test_update_remove_triggers(opp, device_reg, entity_reg, mqtt_mock):
    """Test triggers can be updated and removed."""
    data1 = (
        '{ "automation_type":"trigger",'
        '  "device":{"identifiers":["0AFFD2"]},'
        '  "payload": "short_press",'
        '  "topic": "foobar/triggers/button1",'
        '  "type": "button_short_press",'
        '  "subtype": "button_1" }'
    )
    data2 = (
        '{ "automation_type":"trigger",'
        '  "device":{"identifiers":["0AFFD2"]},'
        '  "payload": "short_press",'
        '  "topic": "foobar/triggers/button1",'
        '  "type": "button_short_press",'
        '  "subtype": "button_2" }'
    )
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla/config", data1)
    await opp.async_block_till_done()

    device_entry = device_reg.async_get_device({("mqtt", "0AFFD2")})
    expected_triggers1 = [
        {
            "platform": "device",
            "domain": DOMAIN,
            "device_id": device_entry.id,
            "discovery_id": "bla",
            "type": "button_short_press",
            "subtype": "button_1",
        },
    ]
    expected_triggers2 = [dict(expected_triggers1[0])]
    expected_triggers2[0]["subtype"] = "button_2"

    triggers = await async_get_device_automations(opp, "trigger", device_entry.id)
    assert_lists_same(triggers, expected_triggers1)

    # Update trigger
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla/config", data2)
    await opp.async_block_till_done()

    triggers = await async_get_device_automations(opp, "trigger", device_entry.id)
    assert_lists_same(triggers, expected_triggers2)

    # Remove trigger
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla/config", "")
    await opp.async_block_till_done()

    device_entry = device_reg.async_get_device({("mqtt", "0AFFD2")})
    assert device_entry is None


async def test_if_fires_on_mqtt_message(opp, device_reg, calls, mqtt_mock):
    """Test triggers firing."""
    data1 = (
        '{ "automation_type":"trigger",'
        '  "device":{"identifiers":["0AFFD2"]},'
        '  "payload": "short_press",'
        '  "topic": "foobar/triggers/button1",'
        '  "type": "button_short_press",'
        '  "subtype": "button_1" }'
    )
    data2 = (
        '{ "automation_type":"trigger",'
        '  "device":{"identifiers":["0AFFD2"]},'
        '  "payload": "long_press",'
        '  "topic": "foobar/triggers/button1",'
        '  "type": "button_long_press",'
        '  "subtype": "button_2" }'
    )
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla1/config", data1)
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla2/config", data2)
    await opp.async_block_till_done()
    device_entry = device_reg.async_get_device({("mqtt", "0AFFD2")})

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "bla1",
                        "type": "button_short_press",
                        "subtype": "button_1",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("short_press")},
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "bla2",
                        "type": "button_1",
                        "subtype": "button_long_press",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("long_press")},
                    },
                },
            ]
        },
    )

    # Fake short press.
    async_fire_mqtt_message(opp, "foobar/triggers/button1", "short_press")
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["some"] == "short_press"

    # Fake long press.
    async_fire_mqtt_message(opp, "foobar/triggers/button1", "long_press")
    await opp.async_block_till_done()
    assert len(calls) == 2
    assert calls[1].data["some"] == "long_press"


async def test_if_fires_on_mqtt_message_template(opp, device_reg, calls, mqtt_mock):
    """Test triggers firing."""
    data1 = (
        '{ "automation_type":"trigger",'
        '  "device":{"identifiers":["0AFFD2"]},'
        "  \"payload\": \"{{ 'foo_press'|regex_replace('foo', 'short') }}\","
        '  "topic": "foobar/triggers/button{{ sqrt(16)|round }}",'
        '  "type": "button_short_press",'
        '  "subtype": "button_1",'
        '  "value_template": "{{ value_json.button }}"}'
    )
    data2 = (
        '{ "automation_type":"trigger",'
        '  "device":{"identifiers":["0AFFD2"]},'
        "  \"payload\": \"{{ 'foo_press'|regex_replace('foo', 'long') }}\","
        '  "topic": "foobar/triggers/button{{ sqrt(16)|round }}",'
        '  "type": "button_long_press",'
        '  "subtype": "button_2",'
        '  "value_template": "{{ value_json.button }}"}'
    )
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla1/config", data1)
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla2/config", data2)
    await opp.async_block_till_done()
    device_entry = device_reg.async_get_device({("mqtt", "0AFFD2")})

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "bla1",
                        "type": "button_short_press",
                        "subtype": "button_1",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("short_press")},
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "bla2",
                        "type": "button_1",
                        "subtype": "button_long_press",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("long_press")},
                    },
                },
            ]
        },
    )

    # Fake short press.
    async_fire_mqtt_message(opp, "foobar/triggers/button4", '{"button":"short_press"}')
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["some"] == "short_press"

    # Fake long press.
    async_fire_mqtt_message(opp, "foobar/triggers/button4", '{"button":"long_press"}')
    await opp.async_block_till_done()
    assert len(calls) == 2
    assert calls[1].data["some"] == "long_press"


async def test_if_fires_on_mqtt_message_late_discover(
    opp, device_reg, calls, mqtt_mock
):
    """Test triggers firing of MQTT device triggers discovered after setup."""
    data0 = (
        '{ "device":{"identifiers":["0AFFD2"]},'
        '  "state_topic": "foobar/sensor",'
        '  "unique_id": "unique" }'
    )
    data1 = (
        '{ "automation_type":"trigger",'
        '  "device":{"identifiers":["0AFFD2"]},'
        '  "payload": "short_press",'
        '  "topic": "foobar/triggers/button1",'
        '  "type": "button_short_press",'
        '  "subtype": "button_1" }'
    )
    data2 = (
        '{ "automation_type":"trigger",'
        '  "device":{"identifiers":["0AFFD2"]},'
        '  "payload": "long_press",'
        '  "topic": "foobar/triggers/button1",'
        '  "type": "button_long_press",'
        '  "subtype": "button_2" }'
    )
    async_fire_mqtt_message(opp, "openpeerpower/sensor/bla0/config", data0)
    await opp.async_block_till_done()
    device_entry = device_reg.async_get_device({("mqtt", "0AFFD2")})

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "bla1",
                        "type": "button_short_press",
                        "subtype": "button_1",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("short_press")},
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "bla2",
                        "type": "button_1",
                        "subtype": "button_long_press",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("long_press")},
                    },
                },
            ]
        },
    )

    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla1/config", data1)
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla2/config", data2)
    await opp.async_block_till_done()

    # Fake short press.
    async_fire_mqtt_message(opp, "foobar/triggers/button1", "short_press")
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["some"] == "short_press"

    # Fake long press.
    async_fire_mqtt_message(opp, "foobar/triggers/button1", "long_press")
    await opp.async_block_till_done()
    assert len(calls) == 2
    assert calls[1].data["some"] == "long_press"


async def test_if_fires_on_mqtt_message_after_update(opp, device_reg, calls, mqtt_mock):
    """Test triggers firing after update."""
    data1 = (
        '{ "automation_type":"trigger",'
        '  "device":{"identifiers":["0AFFD2"]},'
        '  "topic": "foobar/triggers/button1",'
        '  "type": "button_short_press",'
        '  "subtype": "button_1" }'
    )
    data2 = (
        '{ "automation_type":"trigger",'
        '  "device":{"identifiers":["0AFFD2"]},'
        '  "topic": "foobar/triggers/buttonOne",'
        '  "type": "button_long_press",'
        '  "subtype": "button_2" }'
    )
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla1/config", data1)
    await opp.async_block_till_done()
    device_entry = device_reg.async_get_device({("mqtt", "0AFFD2")})

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "bla1",
                        "type": "button_short_press",
                        "subtype": "button_1",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("short_press")},
                    },
                },
            ]
        },
    )

    # Fake short press.
    async_fire_mqtt_message(opp, "foobar/triggers/button1", "")
    await opp.async_block_till_done()
    assert len(calls) == 1

    # Update the trigger with different topic
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla1/config", data2)
    await opp.async_block_till_done()

    async_fire_mqtt_message(opp, "foobar/triggers/button1", "")
    await opp.async_block_till_done()
    assert len(calls) == 1

    async_fire_mqtt_message(opp, "foobar/triggers/buttonOne", "")
    await opp.async_block_till_done()
    assert len(calls) == 2

    # Update the trigger with same topic
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla1/config", data2)
    await opp.async_block_till_done()

    async_fire_mqtt_message(opp, "foobar/triggers/button1", "")
    await opp.async_block_till_done()
    assert len(calls) == 2

    async_fire_mqtt_message(opp, "foobar/triggers/buttonOne", "")
    await opp.async_block_till_done()
    assert len(calls) == 3


async def test_no_resubscribe_same_topic(opp, device_reg, mqtt_mock):
    """Test subscription to topics without change."""
    data1 = (
        '{ "automation_type":"trigger",'
        '  "device":{"identifiers":["0AFFD2"]},'
        '  "topic": "foobar/triggers/button1",'
        '  "type": "button_short_press",'
        '  "subtype": "button_1" }'
    )
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla1/config", data1)
    await opp.async_block_till_done()
    device_entry = device_reg.async_get_device({("mqtt", "0AFFD2")})

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "bla1",
                        "type": "button_short_press",
                        "subtype": "button_1",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("short_press")},
                    },
                },
            ]
        },
    )

    call_count = mqtt_mock.async_subscribe.call_count
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla1/config", data1)
    await opp.async_block_till_done()
    assert mqtt_mock.async_subscribe.call_count == call_count


async def test_not_fires_on_mqtt_message_after_remove_by_mqtt(
    opp, device_reg, calls, mqtt_mock
):
    """Test triggers not firing after removal."""
    data1 = (
        '{ "automation_type":"trigger",'
        '  "device":{"identifiers":["0AFFD2"]},'
        '  "topic": "foobar/triggers/button1",'
        '  "type": "button_short_press",'
        '  "subtype": "button_1" }'
    )
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla1/config", data1)
    await opp.async_block_till_done()
    device_entry = device_reg.async_get_device({("mqtt", "0AFFD2")})

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "bla1",
                        "type": "button_short_press",
                        "subtype": "button_1",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("short_press")},
                    },
                },
            ]
        },
    )

    # Fake short press.
    async_fire_mqtt_message(opp, "foobar/triggers/button1", "short_press")
    await opp.async_block_till_done()
    assert len(calls) == 1

    # Remove the trigger
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla1/config", "")
    await opp.async_block_till_done()

    async_fire_mqtt_message(opp, "foobar/triggers/button1", "short_press")
    await opp.async_block_till_done()
    assert len(calls) == 1

    # Rediscover the trigger
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla1/config", data1)
    await opp.async_block_till_done()

    async_fire_mqtt_message(opp, "foobar/triggers/button1", "short_press")
    await opp.async_block_till_done()
    assert len(calls) == 2


async def test_not_fires_on_mqtt_message_after_remove_from_registry(
    opp, device_reg, calls, mqtt_mock
):
    """Test triggers not firing after removal."""
    data1 = (
        '{ "automation_type":"trigger",'
        '  "device":{"identifiers":["0AFFD2"]},'
        '  "topic": "foobar/triggers/button1",'
        '  "type": "button_short_press",'
        '  "subtype": "button_1" }'
    )
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla1/config", data1)
    await opp.async_block_till_done()
    device_entry = device_reg.async_get_device({("mqtt", "0AFFD2")})

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "bla1",
                        "type": "button_short_press",
                        "subtype": "button_1",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("short_press")},
                    },
                },
            ]
        },
    )

    # Fake short press.
    async_fire_mqtt_message(opp, "foobar/triggers/button1", "short_press")
    await opp.async_block_till_done()
    assert len(calls) == 1

    # Remove the device
    device_reg.async_remove_device(device_entry.id)
    await opp.async_block_till_done()

    async_fire_mqtt_message(opp, "foobar/triggers/button1", "short_press")
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_attach_remove(opp, device_reg, mqtt_mock):
    """Test attach and removal of trigger."""
    data1 = (
        '{ "automation_type":"trigger",'
        '  "device":{"identifiers":["0AFFD2"]},'
        '  "payload": "short_press",'
        '  "topic": "foobar/triggers/button1",'
        '  "type": "button_short_press",'
        '  "subtype": "button_1" }'
    )
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla1/config", data1)
    await opp.async_block_till_done()
    device_entry = device_reg.async_get_device({("mqtt", "0AFFD2")})

    calls = []

    def callback(trigger):
        calls.append(trigger["trigger"]["payload"])

    remove = await async_attach_trigger(
        opp,
        {
            "platform": "device",
            "domain": DOMAIN,
            "device_id": device_entry.id,
            "discovery_id": "bla1",
            "type": "button_short_press",
            "subtype": "button_1",
        },
        callback,
        None,
    )

    # Fake short press.
    async_fire_mqtt_message(opp, "foobar/triggers/button1", "short_press")
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0] == "short_press"

    # Remove the trigger
    remove()
    await opp.async_block_till_done()

    # Verify the triggers are no longer active
    async_fire_mqtt_message(opp, "foobar/triggers/button1", "short_press")
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_attach_remove_late(opp, device_reg, mqtt_mock):
    """Test attach and removal of trigger ."""
    data0 = (
        '{ "device":{"identifiers":["0AFFD2"]},'
        '  "state_topic": "foobar/sensor",'
        '  "unique_id": "unique" }'
    )
    data1 = (
        '{ "automation_type":"trigger",'
        '  "device":{"identifiers":["0AFFD2"]},'
        '  "payload": "short_press",'
        '  "topic": "foobar/triggers/button1",'
        '  "type": "button_short_press",'
        '  "subtype": "button_1" }'
    )
    async_fire_mqtt_message(opp, "openpeerpower/sensor/bla0/config", data0)
    await opp.async_block_till_done()
    device_entry = device_reg.async_get_device({("mqtt", "0AFFD2")})

    calls = []

    def callback(trigger):
        calls.append(trigger["trigger"]["payload"])

    remove = await async_attach_trigger(
        opp,
        {
            "platform": "device",
            "domain": DOMAIN,
            "device_id": device_entry.id,
            "discovery_id": "bla1",
            "type": "button_short_press",
            "subtype": "button_1",
        },
        callback,
        None,
    )

    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla1/config", data1)
    await opp.async_block_till_done()

    # Fake short press.
    async_fire_mqtt_message(opp, "foobar/triggers/button1", "short_press")
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0] == "short_press"

    # Remove the trigger
    remove()
    await opp.async_block_till_done()

    # Verify the triggers are no longer active
    async_fire_mqtt_message(opp, "foobar/triggers/button1", "short_press")
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_attach_remove_late2(opp, device_reg, mqtt_mock):
    """Test attach and removal of trigger ."""
    data0 = (
        '{ "device":{"identifiers":["0AFFD2"]},'
        '  "state_topic": "foobar/sensor",'
        '  "unique_id": "unique" }'
    )
    data1 = (
        '{ "automation_type":"trigger",'
        '  "device":{"identifiers":["0AFFD2"]},'
        '  "payload": "short_press",'
        '  "topic": "foobar/triggers/button1",'
        '  "type": "button_short_press",'
        '  "subtype": "button_1" }'
    )
    async_fire_mqtt_message(opp, "openpeerpower/sensor/bla0/config", data0)
    await opp.async_block_till_done()
    device_entry = device_reg.async_get_device({("mqtt", "0AFFD2")})

    calls = []

    def callback(trigger):
        calls.append(trigger["trigger"]["payload"])

    remove = await async_attach_trigger(
        opp,
        {
            "platform": "device",
            "domain": DOMAIN,
            "device_id": device_entry.id,
            "discovery_id": "bla1",
            "type": "button_short_press",
            "subtype": "button_1",
        },
        callback,
        None,
    )

    # Remove the trigger
    remove()
    await opp.async_block_till_done()

    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla1/config", data1)
    await opp.async_block_till_done()

    # Verify the triggers are no longer active
    async_fire_mqtt_message(opp, "foobar/triggers/button1", "short_press")
    await opp.async_block_till_done()
    assert len(calls) == 0


async def test_entity_device_info_with_connection(opp, mqtt_mock):
    """Test MQTT device registry integration."""
    registry = await opp.helpers.device_registry.async_get_registry()

    data = json.dumps(
        {
            "automation_type": "trigger",
            "topic": "test-topic",
            "type": "foo",
            "subtype": "bar",
            "device": {
                "connections": [["mac", "02:5b:26:a8:dc:12"]],
                "manufacturer": "Whatever",
                "name": "Beer",
                "model": "Glass",
                "sw_version": "0.1-beta",
            },
        }
    )
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla/config", data)
    await opp.async_block_till_done()

    device = registry.async_get_device(set(), {("mac", "02:5b:26:a8:dc:12")})
    assert device is not None
    assert device.connections == {("mac", "02:5b:26:a8:dc:12")}
    assert device.manufacturer == "Whatever"
    assert device.name == "Beer"
    assert device.model == "Glass"
    assert device.sw_version == "0.1-beta"


async def test_entity_device_info_with_identifier(opp, mqtt_mock):
    """Test MQTT device registry integration."""
    registry = await opp.helpers.device_registry.async_get_registry()

    data = json.dumps(
        {
            "automation_type": "trigger",
            "topic": "test-topic",
            "type": "foo",
            "subtype": "bar",
            "device": {
                "identifiers": ["helloworld"],
                "manufacturer": "Whatever",
                "name": "Beer",
                "model": "Glass",
                "sw_version": "0.1-beta",
            },
        }
    )
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla/config", data)
    await opp.async_block_till_done()

    device = registry.async_get_device({("mqtt", "helloworld")})
    assert device is not None
    assert device.identifiers == {("mqtt", "helloworld")}
    assert device.manufacturer == "Whatever"
    assert device.name == "Beer"
    assert device.model == "Glass"
    assert device.sw_version == "0.1-beta"


async def test_entity_device_info_update(opp, mqtt_mock):
    """Test device registry update."""
    registry = await opp.helpers.device_registry.async_get_registry()

    config = {
        "automation_type": "trigger",
        "topic": "test-topic",
        "type": "foo",
        "subtype": "bar",
        "device": {
            "identifiers": ["helloworld"],
            "connections": [["mac", "02:5b:26:a8:dc:12"]],
            "manufacturer": "Whatever",
            "name": "Beer",
            "model": "Glass",
            "sw_version": "0.1-beta",
        },
    }

    data = json.dumps(config)
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla/config", data)
    await opp.async_block_till_done()

    device = registry.async_get_device({("mqtt", "helloworld")})
    assert device is not None
    assert device.name == "Beer"

    config["device"]["name"] = "Milk"
    data = json.dumps(config)
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla/config", data)
    await opp.async_block_till_done()

    device = registry.async_get_device({("mqtt", "helloworld")})
    assert device is not None
    assert device.name == "Milk"


async def test_cleanup_trigger(opp, device_reg, entity_reg, mqtt_mock):
    """Test trigger discovery topic is cleaned when device is removed from registry."""
    config = {
        "automation_type": "trigger",
        "topic": "test-topic",
        "type": "foo",
        "subtype": "bar",
        "device": {"identifiers": ["helloworld"]},
    }

    data = json.dumps(config)
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla/config", data)
    await opp.async_block_till_done()

    # Verify device registry entry is created
    device_entry = device_reg.async_get_device({("mqtt", "helloworld")})
    assert device_entry is not None

    triggers = await async_get_device_automations(opp, "trigger", device_entry.id)
    assert triggers[0]["type"] == "foo"

    device_reg.async_remove_device(device_entry.id)
    await opp.async_block_till_done()
    await opp.async_block_till_done()

    # Verify device registry entry is cleared
    device_entry = device_reg.async_get_device({("mqtt", "helloworld")})
    assert device_entry is None

    # Verify retained discovery topic has been cleared
    mqtt_mock.async_publish.assert_called_once_with(
        "openpeerpower/device_automation/bla/config", "", 0, True
    )


async def test_cleanup_device(opp, device_reg, entity_reg, mqtt_mock):
    """Test removal from device registry when trigger is removed."""
    config = {
        "automation_type": "trigger",
        "topic": "test-topic",
        "type": "foo",
        "subtype": "bar",
        "device": {"identifiers": ["helloworld"]},
    }

    data = json.dumps(config)
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla/config", data)
    await opp.async_block_till_done()

    # Verify device registry entry is created
    device_entry = device_reg.async_get_device({("mqtt", "helloworld")})
    assert device_entry is not None

    triggers = await async_get_device_automations(opp, "trigger", device_entry.id)
    assert triggers[0]["type"] == "foo"

    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla/config", "")
    await opp.async_block_till_done()

    # Verify device registry entry is cleared
    device_entry = device_reg.async_get_device({("mqtt", "helloworld")})
    assert device_entry is None


async def test_cleanup_device_several_triggers(opp, device_reg, entity_reg, mqtt_mock):
    """Test removal from device registry when the last trigger is removed."""
    config1 = {
        "automation_type": "trigger",
        "topic": "test-topic",
        "type": "foo",
        "subtype": "bar",
        "device": {"identifiers": ["helloworld"]},
    }

    config2 = {
        "automation_type": "trigger",
        "topic": "test-topic",
        "type": "foo2",
        "subtype": "bar",
        "device": {"identifiers": ["helloworld"]},
    }

    data1 = json.dumps(config1)
    data2 = json.dumps(config2)
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla1/config", data1)
    await opp.async_block_till_done()
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla2/config", data2)
    await opp.async_block_till_done()

    # Verify device registry entry is created
    device_entry = device_reg.async_get_device({("mqtt", "helloworld")})
    assert device_entry is not None

    triggers = await async_get_device_automations(opp, "trigger", device_entry.id)
    assert len(triggers) == 2
    assert triggers[0]["type"] == "foo"
    assert triggers[1]["type"] == "foo2"

    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla1/config", "")
    await opp.async_block_till_done()

    # Verify device registry entry is not cleared
    device_entry = device_reg.async_get_device({("mqtt", "helloworld")})
    assert device_entry is not None

    triggers = await async_get_device_automations(opp, "trigger", device_entry.id)
    assert len(triggers) == 1
    assert triggers[0]["type"] == "foo2"

    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla2/config", "")
    await opp.async_block_till_done()

    # Verify device registry entry is cleared
    device_entry = device_reg.async_get_device({("mqtt", "helloworld")})
    assert device_entry is None


async def test_cleanup_device_with_entity1(opp, device_reg, entity_reg, mqtt_mock):
    """Test removal from device registry for device with entity.

    Trigger removed first, then entity.
    """
    config1 = {
        "automation_type": "trigger",
        "topic": "test-topic",
        "type": "foo",
        "subtype": "bar",
        "device": {"identifiers": ["helloworld"]},
    }

    config2 = {
        "name": "test_binary_sensor",
        "state_topic": "test-topic",
        "device": {"identifiers": ["helloworld"]},
        "unique_id": "veryunique",
    }

    data1 = json.dumps(config1)
    data2 = json.dumps(config2)
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla1/config", data1)
    await opp.async_block_till_done()
    async_fire_mqtt_message(opp, "openpeerpower/binary_sensor/bla2/config", data2)
    await opp.async_block_till_done()

    # Verify device registry entry is created
    device_entry = device_reg.async_get_device({("mqtt", "helloworld")})
    assert device_entry is not None

    triggers = await async_get_device_automations(opp, "trigger", device_entry.id)
    assert len(triggers) == 3  # 2 binary_sensor triggers + device trigger

    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla1/config", "")
    await opp.async_block_till_done()

    # Verify device registry entry is not cleared
    device_entry = device_reg.async_get_device({("mqtt", "helloworld")})
    assert device_entry is not None

    triggers = await async_get_device_automations(opp, "trigger", device_entry.id)
    assert len(triggers) == 2  # 2 binary_sensor triggers

    async_fire_mqtt_message(opp, "openpeerpower/binary_sensor/bla2/config", "")
    await opp.async_block_till_done()

    # Verify device registry entry is cleared
    device_entry = device_reg.async_get_device({("mqtt", "helloworld")})
    assert device_entry is None


async def test_cleanup_device_with_entity2(opp, device_reg, entity_reg, mqtt_mock):
    """Test removal from device registry for device with entity.

    Entity removed first, then trigger.
    """
    config1 = {
        "automation_type": "trigger",
        "topic": "test-topic",
        "type": "foo",
        "subtype": "bar",
        "device": {"identifiers": ["helloworld"]},
    }

    config2 = {
        "name": "test_binary_sensor",
        "state_topic": "test-topic",
        "device": {"identifiers": ["helloworld"]},
        "unique_id": "veryunique",
    }

    data1 = json.dumps(config1)
    data2 = json.dumps(config2)
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla1/config", data1)
    await opp.async_block_till_done()
    async_fire_mqtt_message(opp, "openpeerpower/binary_sensor/bla2/config", data2)
    await opp.async_block_till_done()

    # Verify device registry entry is created
    device_entry = device_reg.async_get_device({("mqtt", "helloworld")})
    assert device_entry is not None

    triggers = await async_get_device_automations(opp, "trigger", device_entry.id)
    assert len(triggers) == 3  # 2 binary_sensor triggers + device trigger

    async_fire_mqtt_message(opp, "openpeerpower/binary_sensor/bla2/config", "")
    await opp.async_block_till_done()

    # Verify device registry entry is not cleared
    device_entry = device_reg.async_get_device({("mqtt", "helloworld")})
    assert device_entry is not None

    triggers = await async_get_device_automations(opp, "trigger", device_entry.id)
    assert len(triggers) == 1  # device trigger

    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla1/config", "")
    await opp.async_block_till_done()

    # Verify device registry entry is cleared
    device_entry = device_reg.async_get_device({("mqtt", "helloworld")})
    assert device_entry is None


async def test_trigger_debug_info(opp, mqtt_mock):
    """Test debug_info.

    This is a test helper for MQTT debug_info.
    """
    registry = await opp.helpers.device_registry.async_get_registry()

    config = {
        "platform": "mqtt",
        "automation_type": "trigger",
        "topic": "test-topic",
        "type": "foo",
        "subtype": "bar",
        "device": {
            "connections": [["mac", "02:5b:26:a8:dc:12"]],
            "manufacturer": "Whatever",
            "name": "Beer",
            "model": "Glass",
            "sw_version": "0.1-beta",
        },
    }
    data = json.dumps(config)
    async_fire_mqtt_message(opp, "openpeerpower/device_automation/bla/config", data)
    await opp.async_block_till_done()

    device = registry.async_get_device(set(), {("mac", "02:5b:26:a8:dc:12")})
    assert device is not None

    debug_info_data = await debug_info.info_for_device(opp, device.id)
    assert len(debug_info_data["entities"]) == 0
    assert len(debug_info_data["triggers"]) == 1
    assert (
        debug_info_data["triggers"][0]["discovery_data"]["topic"]
        == "openpeerpower/device_automation/bla/config"
    )
    assert debug_info_data["triggers"][0]["discovery_data"]["payload"] == config
