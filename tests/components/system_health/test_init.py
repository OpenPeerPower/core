"""Tests for the system health component init."""
import asyncio
from unittest.mock import AsyncMock, Mock, patch

from aiohttp.client_exceptions import ClientError

from openpeerpower.components import system_health
from openpeerpower.setup import async_setup_component

from tests.common import get_system_health_info, mock_platform


async def gather_system_health_info.opp, opp_ws_client):
    """Gather all info."""
    client = await.opp_ws_client.opp)

    resp = await client.send_json({"id": 6, "type": "system_health/info"})

    # Confirm subscription
    resp = await client.receive_json()
    assert resp["success"]

    data = {}

    # Get initial data
    resp = await client.receive_json()
    assert resp["event"]["type"] == "initial"
    data = resp["event"]["data"]

    while True:
        resp = await client.receive_json()
        event = resp["event"]

        if event["type"] == "finish":
            break

        assert event["type"] == "update"

        if event["success"]:
            data[event["domain"]]["info"][event["key"]] = event["data"]
        else:
            data[event["domain"]]["info"][event["key"]] = event["error"]

    return data


async def test_info_endpoint_return_info.opp, opp_ws_client):
    """Test that the info endpoint works."""
    assert await async_setup_component.opp, "openpeerpower", {})

    with patch(
        "openpeerpower.components.openpeerpower.system_health.system_health_info",
        return_value={"hello": True},
    ):
        assert await async_setup_component.opp, "system_health", {})

    data = await gather_system_health_info.opp, opp_ws_client)

    assert len(data) == 1
    data = data["openpeerpower"]
    assert data == {"info": {"hello": True}}


async def test_info_endpoint_register_callback.opp, opp_ws_client):
    """Test that the info endpoint allows registering callbacks."""

    async def mock_info.opp):
        return {"storage": "YAML"}

   .opp.components.system_health.async_register_info("lovelace", mock_info)
    assert await async_setup_component.opp, "system_health", {})
    data = await gather_system_health_info.opp, opp_ws_client)

    assert len(data) == 1
    data = data["lovelace"]
    assert data == {"info": {"storage": "YAML"}}

    # Test our test helper works
    assert await get_system_health_info.opp, "lovelace") == {"storage": "YAML"}


async def test_info_endpoint_register_callback_timeout.opp, opp_ws_client):
    """Test that the info endpoint timing out."""

    async def mock_info.opp):
        raise asyncio.TimeoutError

   .opp.components.system_health.async_register_info("lovelace", mock_info)
    assert await async_setup_component.opp, "system_health", {})
    data = await gather_system_health_info.opp, opp_ws_client)

    assert len(data) == 1
    data = data["lovelace"]
    assert data == {"info": {"error": {"type": "failed", "error": "timeout"}}}


async def test_info_endpoint_register_callback_exc.opp, opp_ws_client):
    """Test that the info endpoint requires auth."""

    async def mock_info.opp):
        raise Exception("TEST ERROR")

   .opp.components.system_health.async_register_info("lovelace", mock_info)
    assert await async_setup_component.opp, "system_health", {})
    data = await gather_system_health_info.opp, opp_ws_client)

    assert len(data) == 1
    data = data["lovelace"]
    assert data == {"info": {"error": {"type": "failed", "error": "unknown"}}}


async def test_platform_loading.opp, opp_ws_client, aioclient_mock):
    """Test registering via platform."""
    aioclient_mock.get("http://example.com/status", text="")
    aioclient_mock.get("http://example.com/status_fail", exc=ClientError)
   .opp.config.components.add("fake_integration")
    mock_platform(
       .opp,
        "fake_integration.system_health",
        Mock(
            async_register=lambda.opp, register: register.async_register_info(
                AsyncMock(
                    return_value={
                        "hello": "info",
                        "server_reachable": system_health.async_check_can_reach_url(
                           .opp, "http://example.com/status"
                        ),
                        "server_fail_reachable": system_health.async_check_can_reach_url(
                           .opp,
                            "http://example.com/status_fail",
                            more_info="http://more-info-url.com",
                        ),
                        "async_crash": AsyncMock(side_effect=ValueError)(),
                    }
                ),
                "/config/fake_integration",
            )
        ),
    )

    assert await async_setup_component.opp, "system_health", {})
    data = await gather_system_health_info.opp, opp_ws_client)

    assert data["fake_integration"] == {
        "info": {
            "hello": "info",
            "server_reachable": "ok",
            "server_fail_reachable": {
                "type": "failed",
                "error": "unreachable",
                "more_info": "http://more-info-url.com",
            },
            "async_crash": {
                "type": "failed",
                "error": "unknown",
            },
        },
        "manage_url": "/config/fake_integration",
    }
