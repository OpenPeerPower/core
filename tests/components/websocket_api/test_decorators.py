"""Test decorators."""
from openpeerpower.components import http, websocket_api


async def test_async_response_request_context(opp, websocket_client):
    """Test we can access current request."""

    def handle_request(request, connection, msg):
        if request is not None:
            connection.send_result(msg["id"], request.path)
        else:
            connection.send_error(msg["id"], "not_found", "")

    @websocket_api.websocket_command({"type": "test-get-request-executor"})
    @websocket_api.async_response
    async def executor_get_request(opp, connection, msg):
        handle_request(
            await opp.async_add_executor_job(http.current_request.get), connection, msg
        )

    @websocket_api.websocket_command({"type": "test-get-request-async"})
    @websocket_api.async_response
    async def async_get_request(opp, connection, msg):
        handle_request(http.current_request.get(), connection, msg)

    @websocket_api.websocket_command({"type": "test-get-request"})
    def get_request(opp, connection, msg):
        handle_request(http.current_request.get(), connection, msg)

    websocket_api.async_register_command(opp, executor_get_request)
    websocket_api.async_register_command(opp, async_get_request)
    websocket_api.async_register_command(opp, get_request)

    await websocket_client.send_json(
        {
            "id": 5,
            "type": "test-get-request",
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["success"]
    assert msg["result"] == "/api/websocket"

    await websocket_client.send_json(
        {
            "id": 6,
            "type": "test-get-request-async",
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 6
    assert msg["success"]
    assert msg["result"] == "/api/websocket"

    await websocket_client.send_json(
        {
            "id": 7,
            "type": "test-get-request-executor",
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 7
    assert not msg["success"]
    assert msg["error"]["code"] == "not_found"
