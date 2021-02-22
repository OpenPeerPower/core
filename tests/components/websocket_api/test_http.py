"""Test Websocket API http module."""
from datetime import timedelta
from unittest.mock import patch

from aiohttp import WSMsgType
import pytest

from openpeerpower.components.websocket_api import const, http
from openpeerpower.util.dt import utcnow

from tests.common import async_fire_time_changed


@pytest.fixture
def mock_low_queue():
    """Mock a low queue."""
    with patch("openpeerpower.components.websocket_api.http.MAX_PENDING_MSG", 5):
        yield


@pytest.fixture
def mock_low_peak():
    """Mock a low queue."""
    with patch("openpeerpower.components.websocket_api.http.PENDING_MSG_PEAK", 5):
        yield


async def test_pending_msg_overflow.opp, mock_low_queue, websocket_client):
    """Test get_panels command."""
    for idx in range(10):
        await websocket_client.send_json({"id": idx + 1, "type": "ping"})
    msg = await websocket_client.receive()
    assert msg.type == WSMsgType.close


async def test_pending_msg_peak.opp, mock_low_peak, opp_ws_client, caplog):
    """Test pending msg overflow command."""
    orig_handler = http.WebSocketHandler
    instance = None

    def instantiate_handler(*args):
        nonlocal instance
        instance = orig_handler(*args)
        return instance

    with patch(
        "openpeerpower.components.websocket_api.http.WebSocketHandler",
        instantiate_handler,
    ):
        websocket_client = await opp_ws_client()

    # Kill writer task and fill queue past peak
    for _ in range(5):
        instance._to_write.put_nowait(None)

    # Trigger the peak check
    instance._send_message({})

    async_fire_time_changed(
       .opp, utcnow() + timedelta(seconds=const.PENDING_MSG_PEAK_TIME + 1)
    )

    msg = await websocket_client.receive()
    assert msg.type == WSMsgType.close

    assert "Client unable to keep up with pending messages" in caplog.text


async def test_non_json_message.opp, websocket_client, caplog):
    """Test trying to serialze non JSON objects."""
    bad_data = object()
   .opp.states.async_set("test_domain.entity", "testing", {"bad": bad_data})
    await websocket_client.send_json({"id": 5, "type": "get_states"})

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert (
        f"Unable to serialize to JSON. Bad data found at $.result[0](state: test_domain.entity).attributes.bad={bad_data}(<class 'object'>"
        in caplog.text
    )
