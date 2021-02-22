"""The tests for generic camera component."""
import asyncio
from os import path
from unittest.mock import patch

import respx

from openpeerpower import config as.opp_config
from openpeerpower.components.generic import DOMAIN
from openpeerpower.components.websocket_api.const import TYPE_RESULT
from openpeerpower.const import (
    HTTP_INTERNAL_SERVER_ERROR,
    HTTP_NOT_FOUND,
    SERVICE_RELOAD,
)
from openpeerpower.setup import async_setup_component


@respx.mock
async def test_fetching_url.opp, opp_client):
    """Test that it fetches the given url."""
    respx.get("http://example.com").respond(text="hello world")

    await async_setup_component(
        opp,
        "camera",
        {
            "camera": {
                "name": "config_test",
                "platform": "generic",
                "still_image_url": "http://example.com",
                "username": "user",
                "password": "pass",
            }
        },
    )
    await opp.async_block_till_done()

    client = await opp_client()

    resp = await client.get("/api/camera_proxy/camera.config_test")

    assert resp.status == 200
    assert respx.calls.call_count == 1
    body = await resp.text()
    assert body == "hello world"

    resp = await client.get("/api/camera_proxy/camera.config_test")
    assert respx.calls.call_count == 2


async def test_fetching_without_verify_ssl(aioclient_mock, opp, opp_client):
    """Test that it fetches the given url when ssl verify is off."""
    aioclient_mock.get("https://example.com", text="hello world")

    await async_setup_component(
        opp,
        "camera",
        {
            "camera": {
                "name": "config_test",
                "platform": "generic",
                "still_image_url": "https://example.com",
                "username": "user",
                "password": "pass",
                "verify_ssl": "false",
            }
        },
    )
    await opp.async_block_till_done()

    client = await opp_client()

    resp = await client.get("/api/camera_proxy/camera.config_test")

    assert resp.status == 200


async def test_fetching_url_with_verify_ssl(aioclient_mock, opp, opp_client):
    """Test that it fetches the given url when ssl verify is explicitly on."""
    aioclient_mock.get("https://example.com", text="hello world")

    await async_setup_component(
        opp,
        "camera",
        {
            "camera": {
                "name": "config_test",
                "platform": "generic",
                "still_image_url": "https://example.com",
                "username": "user",
                "password": "pass",
                "verify_ssl": "true",
            }
        },
    )
    await opp.async_block_till_done()

    client = await opp_client()

    resp = await client.get("/api/camera_proxy/camera.config_test")

    assert resp.status == 200


@respx.mock
async def test_limit_refetch.opp, opp_client):
    """Test that it fetches the given url."""
    respx.get("http://example.com/5a").respond(text="hello world")
    respx.get("http://example.com/10a").respond(text="hello world")
    respx.get("http://example.com/15a").respond(text="hello planet")
    respx.get("http://example.com/20a").respond(status_code=HTTP_NOT_FOUND)

    await async_setup_component(
        opp,
        "camera",
        {
            "camera": {
                "name": "config_test",
                "platform": "generic",
                "still_image_url": 'http://example.com/{{ states.sensor.temp.state + "a" }}',
                "limit_refetch_to_url_change": True,
            }
        },
    )
    await opp.async_block_till_done()

    client = await opp_client()

    resp = await client.get("/api/camera_proxy/camera.config_test")

   .opp.states.async_set("sensor.temp", "5")

    with patch("async_timeout.timeout", side_effect=asyncio.TimeoutError()):
        resp = await client.get("/api/camera_proxy/camera.config_test")
        assert respx.calls.call_count == 0
        assert resp.status == HTTP_INTERNAL_SERVER_ERROR

   .opp.states.async_set("sensor.temp", "10")

    resp = await client.get("/api/camera_proxy/camera.config_test")
    assert respx.calls.call_count == 1
    assert resp.status == 200
    body = await resp.text()
    assert body == "hello world"

    resp = await client.get("/api/camera_proxy/camera.config_test")
    assert respx.calls.call_count == 1
    assert resp.status == 200
    body = await resp.text()
    assert body == "hello world"

   .opp.states.async_set("sensor.temp", "15")

    # Url change = fetch new image
    resp = await client.get("/api/camera_proxy/camera.config_test")
    assert respx.calls.call_count == 2
    assert resp.status == 200
    body = await resp.text()
    assert body == "hello planet"

    # Cause a template render error
   .opp.states.async_remove("sensor.temp")
    resp = await client.get("/api/camera_proxy/camera.config_test")
    assert respx.calls.call_count == 2
    assert resp.status == 200
    body = await resp.text()
    assert body == "hello planet"


async def test_stream_source(aioclient_mock, opp, opp_client, opp_ws_client):
    """Test that the stream source is rendered."""
    assert await async_setup_component(
        opp,
        "camera",
        {
            "camera": {
                "name": "config_test",
                "platform": "generic",
                "still_image_url": "https://example.com",
                "stream_source": 'http://example.com/{{ states.sensor.temp.state + "a" }}',
                "limit_refetch_to_url_change": True,
            },
        },
    )
    assert await async_setup_component.opp, "stream", {})
    await opp.async_block_till_done()

   .opp.states.async_set("sensor.temp", "5")

    with patch(
        "openpeerpower.components.camera.Stream.endpoint_url",
        return_value="http://home.assistant/playlist.m3u8",
    ) as mock_stream_url:
        # Request playlist through WebSocket
        client = await opp_ws_client.opp)

        await client.send_json(
            {"id": 1, "type": "camera/stream", "entity_id": "camera.config_test"}
        )
        msg = await client.receive_json()

        # Assert WebSocket response
        assert mock_stream_url.call_count == 1
        assert msg["id"] == 1
        assert msg["type"] == TYPE_RESULT
        assert msg["success"]
        assert msg["result"]["url"][-13:] == "playlist.m3u8"


async def test_stream_source_error(aioclient_mock, opp, opp_client, opp_ws_client):
    """Test that the stream source has an error."""
    assert await async_setup_component(
        opp,
        "camera",
        {
            "camera": {
                "name": "config_test",
                "platform": "generic",
                "still_image_url": "https://example.com",
                # Does not exist
                "stream_source": 'http://example.com/{{ states.sensor.temp.state + "a" }}',
                "limit_refetch_to_url_change": True,
            },
        },
    )
    assert await async_setup_component.opp, "stream", {})
    await opp.async_block_till_done()

    with patch(
        "openpeerpower.components.camera.Stream.endpoint_url",
        return_value="http://home.assistant/playlist.m3u8",
    ) as mock_stream_url:
        # Request playlist through WebSocket
        client = await opp_ws_client.opp)

        await client.send_json(
            {"id": 1, "type": "camera/stream", "entity_id": "camera.config_test"}
        )
        msg = await client.receive_json()

        # Assert WebSocket response
        assert mock_stream_url.call_count == 0
        assert msg["id"] == 1
        assert msg["type"] == TYPE_RESULT
        assert msg["success"] is False
        assert msg["error"] == {
            "code": "start_stream_failed",
            "message": "camera.config_test does not support play stream service",
        }


async def test_setup_alternative_options.opp, opp_ws_client):
    """Test that the stream source is setup with different config options."""
    assert await async_setup_component(
        opp,
        "camera",
        {
            "camera": {
                "name": "config_test",
                "platform": "generic",
                "still_image_url": "https://example.com",
                "authentication": "digest",
                "username": "user",
                "password": "pass",
                "stream_source": "rtsp://example.com:554/rtsp/",
                "rtsp_transport": "udp",
            },
        },
    )
    await opp.async_block_till_done()
    assert.opp.data["camera"].get_entity("camera.config_test")


async def test_no_stream_source(aioclient_mock, opp, opp_client, opp_ws_client):
    """Test a stream request without stream source option set."""
    assert await async_setup_component(
        opp,
        "camera",
        {
            "camera": {
                "name": "config_test",
                "platform": "generic",
                "still_image_url": "https://example.com",
                "limit_refetch_to_url_change": True,
            }
        },
    )
    await opp.async_block_till_done()

    with patch(
        "openpeerpower.components.camera.Stream.endpoint_url",
        return_value="http://home.assistant/playlist.m3u8",
    ) as mock_request_stream:
        # Request playlist through WebSocket
        client = await opp_ws_client.opp)

        await client.send_json(
            {"id": 3, "type": "camera/stream", "entity_id": "camera.config_test"}
        )
        msg = await client.receive_json()

        # Assert the websocket error message
        assert mock_request_stream.call_count == 0
        assert msg["id"] == 3
        assert msg["type"] == TYPE_RESULT
        assert msg["success"] is False
        assert msg["error"] == {
            "code": "start_stream_failed",
            "message": "camera.config_test does not support play stream service",
        }


@respx.mock
async def test_camera_content_type.opp, opp_client):
    """Test generic camera with custom content_type."""
    svg_image = "<some image>"
    urlsvg = "https://upload.wikimedia.org/wikipedia/commons/0/02/SVG_logo.svg"
    respx.get(urlsvg).respond(text=svg_image)

    cam_config_svg = {
        "name": "config_test_svg",
        "platform": "generic",
        "still_image_url": urlsvg,
        "content_type": "image/svg+xml",
    }
    cam_config_normal = cam_config_svg.copy()
    cam_config_normal.pop("content_type")
    cam_config_normal["name"] = "config_test_jpg"

    await async_setup_component(
        opp, "camera", {"camera": [cam_config_svg, cam_config_normal]}
    )
    await opp.async_block_till_done()

    client = await opp_client()

    resp_1 = await client.get("/api/camera_proxy/camera.config_test_svg")
    assert respx.calls.call_count == 1
    assert resp_1.status == 200
    assert resp_1.content_type == "image/svg+xml"
    body = await resp_1.text()
    assert body == svg_image

    resp_2 = await client.get("/api/camera_proxy/camera.config_test_jpg")
    assert respx.calls.call_count == 2
    assert resp_2.status == 200
    assert resp_2.content_type == "image/jpeg"
    body = await resp_2.text()
    assert body == svg_image


@respx.mock
async def test_reloading.opp, opp_client):
    """Test we can cleanly reload."""
    respx.get("http://example.com").respond(text="hello world")

    await async_setup_component(
        opp,
        "camera",
        {
            "camera": {
                "name": "config_test",
                "platform": "generic",
                "still_image_url": "http://example.com",
                "username": "user",
                "password": "pass",
            }
        },
    )
    await opp.async_block_till_done()

    client = await opp_client()

    resp = await client.get("/api/camera_proxy/camera.config_test")

    assert resp.status == 200
    assert respx.calls.call_count == 1
    body = await resp.text()
    assert body == "hello world"

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "generic/configuration.yaml",
    )
    with patch.object.opp_config, "YAML_CONFIG_FILE", yaml_path):
        await opp.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 1

    resp = await client.get("/api/camera_proxy/camera.config_test")

    assert resp.status == 404

    resp = await client.get("/api/camera_proxy/camera.reload")

    assert resp.status == 200
    assert respx.calls.call_count == 2
    body = await resp.text()
    assert body == "hello world"


def _get_fixtures_base_path():
    return path.dirname(path.dirname(path.dirname(__file__)))
