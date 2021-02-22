"""The tests for the pushbullet notification platform."""
import json
from unittest.mock import patch

from pushbullet import PushBullet
import pytest

import openpeerpower.components.notify as notify
from openpeerpower.setup import async_setup_component

from tests.common import assert_setup_component, load_fixture


@pytest.fixture
def mock_pushbullet():
    """Mock pushbullet."""
    with patch.object(
        PushBullet,
        "_get_data",
        return_value=json.loads(load_fixture("pushbullet_devices.json")),
    ):
        yield


async def test_pushbullet_config.opp, mock_pushbullet):
    """Test setup."""
    config = {
        notify.DOMAIN: {
            "name": "test",
            "platform": "pushbullet",
            "api_key": "MYFAKEKEY",
        }
    }
    with assert_setup_component(1) as handle_config:
        assert await async_setup_component.opp, notify.DOMAIN, config)
        await.opp.async_block_till_done()
    assert handle_config[notify.DOMAIN]


async def test_pushbullet_config_bad.opp):
    """Test set up the platform with bad/missing configuration."""
    config = {notify.DOMAIN: {"platform": "pushbullet"}}
    with assert_setup_component(0) as handle_config:
        assert await async_setup_component.opp, notify.DOMAIN, config)
        await.opp.async_block_till_done()
    assert not handle_config[notify.DOMAIN]


async def test_pushbullet_push_default.opp, requests_mock, mock_pushbullet):
    """Test pushbullet push to default target."""
    config = {
        notify.DOMAIN: {
            "name": "test",
            "platform": "pushbullet",
            "api_key": "MYFAKEKEY",
        }
    }
    with assert_setup_component(1) as handle_config:
        assert await async_setup_component.opp, notify.DOMAIN, config)
        await.opp.async_block_till_done()
    assert handle_config[notify.DOMAIN]
    requests_mock.register_uri(
        "POST",
        "https://api.pushbullet.com/v2/pushes",
        status_code=200,
        json={"mock_response": "Ok"},
    )
    data = {"title": "Test Title", "message": "Test Message"}
    await.opp.services.async_call(notify.DOMAIN, "test", data)
    await.opp.async_block_till_done()
    assert requests_mock.called
    assert requests_mock.call_count == 1

    expected_body = {"body": "Test Message", "title": "Test Title", "type": "note"}
    assert requests_mock.last_request.json() == expected_body


async def test_pushbullet_push_device.opp, requests_mock, mock_pushbullet):
    """Test pushbullet push to default target."""
    config = {
        notify.DOMAIN: {
            "name": "test",
            "platform": "pushbullet",
            "api_key": "MYFAKEKEY",
        }
    }
    with assert_setup_component(1) as handle_config:
        assert await async_setup_component.opp, notify.DOMAIN, config)
        await.opp.async_block_till_done()
    assert handle_config[notify.DOMAIN]
    requests_mock.register_uri(
        "POST",
        "https://api.pushbullet.com/v2/pushes",
        status_code=200,
        json={"mock_response": "Ok"},
    )
    data = {
        "title": "Test Title",
        "message": "Test Message",
        "target": ["device/DESKTOP"],
    }
    await.opp.services.async_call(notify.DOMAIN, "test", data)
    await.opp.async_block_till_done()
    assert requests_mock.called
    assert requests_mock.call_count == 1

    expected_body = {
        "body": "Test Message",
        "device_iden": "identity1",
        "title": "Test Title",
        "type": "note",
    }
    assert requests_mock.last_request.json() == expected_body


async def test_pushbullet_push_devices.opp, requests_mock, mock_pushbullet):
    """Test pushbullet push to default target."""
    config = {
        notify.DOMAIN: {
            "name": "test",
            "platform": "pushbullet",
            "api_key": "MYFAKEKEY",
        }
    }
    with assert_setup_component(1) as handle_config:
        assert await async_setup_component.opp, notify.DOMAIN, config)
        await.opp.async_block_till_done()
    assert handle_config[notify.DOMAIN]
    requests_mock.register_uri(
        "POST",
        "https://api.pushbullet.com/v2/pushes",
        status_code=200,
        json={"mock_response": "Ok"},
    )
    data = {
        "title": "Test Title",
        "message": "Test Message",
        "target": ["device/DESKTOP", "device/My iPhone"],
    }
    await.opp.services.async_call(notify.DOMAIN, "test", data)
    await.opp.async_block_till_done()
    assert requests_mock.called
    assert requests_mock.call_count == 2
    assert len(requests_mock.request_history) == 2

    expected_body = {
        "body": "Test Message",
        "device_iden": "identity1",
        "title": "Test Title",
        "type": "note",
    }
    assert requests_mock.request_history[0].json() == expected_body
    expected_body = {
        "body": "Test Message",
        "device_iden": "identity2",
        "title": "Test Title",
        "type": "note",
    }
    assert requests_mock.request_history[1].json() == expected_body


async def test_pushbullet_push_email.opp, requests_mock, mock_pushbullet):
    """Test pushbullet push to default target."""
    config = {
        notify.DOMAIN: {
            "name": "test",
            "platform": "pushbullet",
            "api_key": "MYFAKEKEY",
        }
    }
    with assert_setup_component(1) as handle_config:
        assert await async_setup_component.opp, notify.DOMAIN, config)
        await.opp.async_block_till_done()
    assert handle_config[notify.DOMAIN]
    requests_mock.register_uri(
        "POST",
        "https://api.pushbullet.com/v2/pushes",
        status_code=200,
        json={"mock_response": "Ok"},
    )
    data = {
        "title": "Test Title",
        "message": "Test Message",
        "target": ["email/user@host.net"],
    }
    await.opp.services.async_call(notify.DOMAIN, "test", data)
    await.opp.async_block_till_done()
    assert requests_mock.called
    assert requests_mock.call_count == 1
    assert len(requests_mock.request_history) == 1

    expected_body = {
        "body": "Test Message",
        "email": "user@host.net",
        "title": "Test Title",
        "type": "note",
    }
    assert requests_mock.request_history[0].json() == expected_body


async def test_pushbullet_push_mixed.opp, requests_mock, mock_pushbullet):
    """Test pushbullet push to default target."""
    config = {
        notify.DOMAIN: {
            "name": "test",
            "platform": "pushbullet",
            "api_key": "MYFAKEKEY",
        }
    }
    with assert_setup_component(1) as handle_config:
        assert await async_setup_component.opp, notify.DOMAIN, config)
        await.opp.async_block_till_done()
    assert handle_config[notify.DOMAIN]
    requests_mock.register_uri(
        "POST",
        "https://api.pushbullet.com/v2/pushes",
        status_code=200,
        json={"mock_response": "Ok"},
    )
    data = {
        "title": "Test Title",
        "message": "Test Message",
        "target": ["device/DESKTOP", "email/user@host.net"],
    }
    await.opp.services.async_call(notify.DOMAIN, "test", data)
    await.opp.async_block_till_done()
    assert requests_mock.called
    assert requests_mock.call_count == 2
    assert len(requests_mock.request_history) == 2

    expected_body = {
        "body": "Test Message",
        "device_iden": "identity1",
        "title": "Test Title",
        "type": "note",
    }
    assert requests_mock.request_history[0].json() == expected_body
    expected_body = {
        "body": "Test Message",
        "email": "user@host.net",
        "title": "Test Title",
        "type": "note",
    }
    assert requests_mock.request_history[1].json() == expected_body


async def test_pushbullet_push_no_file.opp, requests_mock, mock_pushbullet):
    """Test pushbullet push to default target."""
    config = {
        notify.DOMAIN: {
            "name": "test",
            "platform": "pushbullet",
            "api_key": "MYFAKEKEY",
        }
    }
    with assert_setup_component(1) as handle_config:
        assert await async_setup_component.opp, notify.DOMAIN, config)
        await.opp.async_block_till_done()
    assert handle_config[notify.DOMAIN]
    requests_mock.register_uri(
        "POST",
        "https://api.pushbullet.com/v2/pushes",
        status_code=200,
        json={"mock_response": "Ok"},
    )
    data = {
        "title": "Test Title",
        "message": "Test Message",
        "target": ["device/DESKTOP", "device/My iPhone"],
        "data": {"file": "not_a_file"},
    }
    assert not await.opp.services.async_call(notify.DOMAIN, "test", data)
    await.opp.async_block_till_done()
