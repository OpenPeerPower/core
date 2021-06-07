"""The tests for the notify demo platform."""

import logging
from unittest.mock import patch

import pytest
import voluptuous as vol

import openpeerpower.components.demo.notify as demo
import openpeerpower.components.notify as notify
from openpeerpower.core import callback
from openpeerpower.helpers import discovery
from openpeerpower.setup import async_setup_component

from tests.common import assert_setup_component, async_capture_events

CONFIG = {notify.DOMAIN: {"platform": "demo"}}


@pytest.fixture
def events(opp):
    """Fixture that catches notify events."""
    return async_capture_events(opp, demo.EVENT_NOTIFY)


@pytest.fixture
def calls():
    """Fixture to calls."""
    return []


@pytest.fixture
def record_calls(calls):
    """Fixture to record calls."""

    @callback
    def record_calls(*args):
        """Record calls."""
        calls.append(args)

    return record_calls


@pytest.fixture(name="mock_demo_notify")
def mock_demo_notify_fixture():
    """Mock demo notify service."""
    with patch("openpeerpower.components.demo.notify.get_service", autospec=True) as ns:
        yield ns


async def setup_notify(opp):
    """Test setup."""
    with assert_setup_component(1, notify.DOMAIN) as config:
        assert await async_setup_component(opp, notify.DOMAIN, CONFIG)
    assert config[notify.DOMAIN]
    await opp.async_block_till_done()


async def test_no_notify_service(opp, mock_demo_notify, caplog):
    """Test missing platform notify service instance."""
    caplog.set_level(logging.ERROR)
    mock_demo_notify.return_value = None
    await setup_notify(opp)
    await opp.async_block_till_done()
    assert mock_demo_notify.called
    assert "Failed to initialize notification service demo" in caplog.text


async def test_discover_notify(opp, mock_demo_notify):
    """Test discovery of notify demo platform."""
    assert notify.DOMAIN not in opp.config.components
    mock_demo_notify.return_value = None
    await discovery.async_load_platform(
        opp, "notify", "demo", {"test_key": "test_val"}, {"notify": {}}
    )
    await opp.async_block_till_done()
    assert notify.DOMAIN in opp.config.components
    assert mock_demo_notify.called
    assert mock_demo_notify.mock_calls[0][1] == (
        opp,
        {},
        {"test_key": "test_val"},
    )


async def test_sending_none_message(opp, events):
    """Test send with None as message."""
    await setup_notify(opp)
    with pytest.raises(vol.Invalid):
        await opp.services.async_call(
            notify.DOMAIN, notify.SERVICE_NOTIFY, {notify.ATTR_MESSAGE: None}
        )
    await opp.async_block_till_done()
    assert len(events) == 0


async def test_sending_templated_message(opp, events):
    """Send a templated message."""
    await setup_notify(opp)
    opp.states.async_set("sensor.temperature", 10)
    data = {
        notify.ATTR_MESSAGE: "{{states.sensor.temperature.state}}",
        notify.ATTR_TITLE: "{{ states.sensor.temperature.name }}",
    }
    await opp.services.async_call(notify.DOMAIN, notify.SERVICE_NOTIFY, data)
    await opp.async_block_till_done()
    last_event = events[-1]
    assert last_event.data[notify.ATTR_TITLE] == "temperature"
    assert last_event.data[notify.ATTR_MESSAGE] == "10"


async def test_method_forwards_correct_data(opp, events):
    """Test that all data from the service gets forwarded to service."""
    await setup_notify(opp)
    data = {
        notify.ATTR_MESSAGE: "my message",
        notify.ATTR_TITLE: "my title",
        notify.ATTR_DATA: {"hello": "world"},
    }
    await opp.services.async_call(notify.DOMAIN, notify.SERVICE_NOTIFY, data)
    await opp.async_block_till_done()
    assert len(events) == 1
    data = events[0].data
    assert {
        "message": "my message",
        "title": "my title",
        "data": {"hello": "world"},
    } == data


async def test_calling_notify_from_script_loaded_from_yaml_without_title(opp, events):
    """Test if we can call a notify from a script."""
    await setup_notify(opp)
    step = {
        "service": "notify.notify",
        "data": {
            "data": {"push": {"sound": "US-EN-Morgan-Freeman-Roommate-Is-Arriving.wav"}}
        },
        "data_template": {"message": "Test 123 {{ 2 + 2 }}\n"},
    }
    await async_setup_component(
        opp, "script", {"script": {"test": {"sequence": step}}}
    )
    await opp.services.async_call("script", "test")
    await opp.async_block_till_done()
    assert len(events) == 1
    assert {
        "message": "Test 123 4",
        "data": {"push": {"sound": "US-EN-Morgan-Freeman-Roommate-Is-Arriving.wav"}},
    } == events[0].data


async def test_calling_notify_from_script_loaded_from_yaml_with_title(opp, events):
    """Test if we can call a notify from a script."""
    await setup_notify(opp)
    step = {
        "service": "notify.notify",
        "data": {
            "data": {"push": {"sound": "US-EN-Morgan-Freeman-Roommate-Is-Arriving.wav"}}
        },
        "data_template": {"message": "Test 123 {{ 2 + 2 }}\n", "title": "Test"},
    }
    await async_setup_component(
        opp, "script", {"script": {"test": {"sequence": step}}}
    )
    await opp.services.async_call("script", "test")
    await opp.async_block_till_done()
    assert len(events) == 1
    assert {
        "message": "Test 123 4",
        "title": "Test",
        "data": {"push": {"sound": "US-EN-Morgan-Freeman-Roommate-Is-Arriving.wav"}},
    } == events[0].data


async def test_targets_are_services(opp):
    """Test that all targets are exposed as individual services."""
    await setup_notify(opp)
    assert opp.services.has_service("notify", "demo") is not None
    service = "demo_test_target_name"
    assert opp.services.has_service("notify", service) is not None


async def test_messages_to_targets_route(opp, calls, record_calls):
    """Test message routing to specific target services."""
    await setup_notify(opp)
    opp.bus.async_listen_once("notify", record_calls)

    await opp.services.async_call(
        "notify",
        "demo_test_target_name",
        {"message": "my message", "title": "my title", "data": {"hello": "world"}},
    )

    await opp.async_block_till_done()

    data = calls[0][0].data

    assert {
        "message": "my message",
        "target": ["test target id"],
        "title": "my title",
        "data": {"hello": "world"},
    } == data
