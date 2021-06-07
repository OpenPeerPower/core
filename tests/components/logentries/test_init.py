"""The tests for the Logentries component."""

from unittest.mock import MagicMock, call, patch

import pytest

import openpeerpower.components.logentries as logentries
from openpeerpower.const import EVENT_STATE_CHANGED, STATE_OFF, STATE_ON
from openpeerpower.setup import async_setup_component


async def test_setup_config_full(opp):
    """Test setup with all data."""
    config = {"logentries": {"token": "secret"}}
    opp.bus.listen = MagicMock()
    assert await async_setup_component(opp, logentries.DOMAIN, config)
    assert opp.bus.listen.called
    assert opp.bus.listen.call_args_list[0][0][0] == EVENT_STATE_CHANGED


async def test_setup_config_defaults(opp):
    """Test setup with defaults."""
    config = {"logentries": {"token": "token"}}
    opp.bus.listen = MagicMock()
    assert await async_setup_component(opp, logentries.DOMAIN, config)
    assert opp.bus.listen.called
    assert opp.bus.listen.call_args_list[0][0][0] == EVENT_STATE_CHANGED


@pytest.fixture
def mock_dump():
    """Mock json dumps."""
    with patch("json.dumps") as mock_dump:
        yield mock_dump


@pytest.fixture
def mock_requests():
    """Mock requests."""
    with patch.object(logentries, "requests") as mock_requests:
        yield mock_requests


async def test_event_listener(opp, mock_dump, mock_requests):
    """Test event listener."""
    mock_dump.side_effect = lambda x: x
    mock_post = mock_requests.post
    mock_requests.exceptions.RequestException = Exception
    config = {"logentries": {"token": "token"}}
    opp.bus.listen = MagicMock()
    assert await async_setup_component(opp, logentries.DOMAIN, config)
    handler_method = opp.bus.listen.call_args_list[0][0][1]

    valid = {"1": 1, "1.0": 1.0, STATE_ON: 1, STATE_OFF: 0, "foo": "foo"}
    for in_, out in valid.items():
        state = MagicMock(state=in_, domain="fake", object_id="entity", attributes={})
        event = MagicMock(data={"new_state": state}, time_fired=12345)
        body = [
            {
                "domain": "fake",
                "entity_id": "entity",
                "attributes": {},
                "time": "12345",
                "value": out,
            }
        ]
        payload = {
            "host": "https://webhook.logentries.com/noformat/logs/token",
            "event": body,
        }
        handler_method(event)
        assert mock_post.call_count == 1
        assert mock_post.call_args == call(payload["host"], data=payload, timeout=10)
        mock_post.reset_mock()
