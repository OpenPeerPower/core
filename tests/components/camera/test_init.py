"""The tests for the camera component."""
import asyncio
import base64
import io
from unittest.mock import Mock, PropertyMock, mock_open, patch

import pytest

from openpeerpower.components import camera
from openpeerpower.components.camera.const import DOMAIN, PREF_PRELOAD_STREAM
from openpeerpower.components.camera.prefs import CameraEntityPreferences
from openpeerpower.components.websocket_api.const import TYPE_RESULT
from openpeerpower.config import async_process_op_core_config
from openpeerpower.const import ATTR_ENTITY_ID, EVENT_OPENPEERPOWER_START
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.setup import async_setup_component

from tests.components.camera import common


@pytest.fixture(name="mock_camera")
async def mock_camera_fixture(opp):
    """Initialize a demo camera platform."""
    assert await async_setup_component(
        opp, "camera", {camera.DOMAIN: {"platform": "demo"}}
    )
    await opp.async_block_till_done()

    with patch(
        "openpeerpower.components.demo.camera.Path.read_bytes",
        return_value=b"Test",
    ):
        yield


@pytest.fixture(name="mock_stream")
def mock_stream_fixture(opp):
    """Initialize a demo camera platform with streaming."""
    assert opp.loop.run_until_complete(
        async_setup_component(opp, "stream", {"stream": {}})
    )


@pytest.fixture(name="setup_camera_prefs")
def setup_camera_prefs_fixture(opp):
    """Initialize HTTP API."""
    return common.mock_camera_prefs(opp, "camera.demo_camera")


@pytest.fixture(name="image_mock_url")
async def image_mock_url_fixture(opp):
    """Fixture for get_image tests."""
    await async_setup_component(
        opp, camera.DOMAIN, {camera.DOMAIN: {"platform": "demo"}}
    )
    await opp.async_block_till_done()


async def test_get_image_from_camera(opp, image_mock_url):
    """Grab an image from camera entity."""

    with patch(
        "openpeerpower.components.demo.camera.Path.read_bytes",
        autospec=True,
        return_value=b"Test",
    ) as mock_camera:
        image = await camera.async_get_image(opp, "camera.demo_camera")

    assert mock_camera.called
    assert image.content == b"Test"


async def test_get_stream_source_from_camera(opp, mock_camera):
    """Fetch stream source from camera entity."""

    with patch(
        "openpeerpower.components.camera.Camera.stream_source",
        return_value="rtsp://127.0.0.1/stream",
    ) as mock_camera_stream_source:
        stream_source = await camera.async_get_stream_source(opp, "camera.demo_camera")

    assert mock_camera_stream_source.called
    assert stream_source == "rtsp://127.0.0.1/stream"


async def test_get_image_without_exists_camera(opp, image_mock_url):
    """Try to get image without exists camera."""
    with patch(
        "openpeerpower.helpers.entity_component.EntityComponent.get_entity",
        return_value=None,
    ), pytest.raises(OpenPeerPowerError):
        await camera.async_get_image(opp, "camera.demo_camera")


async def test_get_image_with_timeout(opp, image_mock_url):
    """Try to get image with timeout."""
    with patch(
        "openpeerpower.components.demo.camera.DemoCamera.async_camera_image",
        side_effect=asyncio.TimeoutError,
    ), pytest.raises(OpenPeerPowerError):
        await camera.async_get_image(opp, "camera.demo_camera")


async def test_get_image_fails(opp, image_mock_url):
    """Try to get image with timeout."""
    with patch(
        "openpeerpower.components.demo.camera.DemoCamera.async_camera_image",
        return_value=None,
    ), pytest.raises(OpenPeerPowerError):
        await camera.async_get_image(opp, "camera.demo_camera")


async def test_snapshot_service(opp, mock_camera):
    """Test snapshot service."""
    mopen = mock_open()

    with patch("openpeerpower.components.camera.open", mopen, create=True), patch(
        "openpeerpower.components.camera.os.path.exists",
        Mock(spec="os.path.exists", return_value=True),
    ), patch.object.opp.config, "is_allowed_path", return_value=True):
        await opp.services.async_call(
            camera.DOMAIN,
            camera.SERVICE_SNAPSHOT,
            {
                ATTR_ENTITY_ID: "camera.demo_camera",
                camera.ATTR_FILENAME: "/test/snapshot.jpg",
            },
            blocking=True,
        )

        mock_write = mopen().write

        assert len(mock_write.mock_calls) == 1
        assert mock_write.mock_calls[0][1][0] == b"Test"


async def test_websocket_camera_thumbnail(opp, opp_ws_client, mock_camera):
    """Test camera_thumbnail websocket command."""
    await async_setup_component(opp, "camera", {})

    client = await opp_ws_client(opp)
    await client.send_json(
        {"id": 5, "type": "camera_thumbnail", "entity_id": "camera.demo_camera"}
    )

    msg = await client.receive_json()

    assert msg["id"] == 5
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]
    assert msg["result"]["content_type"] == "image/jpeg"
    assert msg["result"]["content"] == base64.b64encode(b"Test").decode("utf-8")


async def test_websocket_stream_no_source(
    opp, opp_ws_client, mock_camera, mock_stream
):
    """Test camera/stream websocket command with camera with no source."""
    await async_setup_component(opp, "camera", {})

    # Request playlist through WebSocket
    client = await opp_ws_client(opp)
    await client.send_json(
        {"id": 6, "type": "camera/stream", "entity_id": "camera.demo_camera"}
    )
    msg = await client.receive_json()

    # Assert WebSocket response
    assert msg["id"] == 6
    assert msg["type"] == TYPE_RESULT
    assert not msg["success"]


async def test_websocket_camera_stream(opp, opp_ws_client, mock_camera, mock_stream):
    """Test camera/stream websocket command."""
    await async_setup_component(opp, "camera", {})

    with patch(
        "openpeerpower.components.camera.Stream.endpoint_url",
        return_value="http://home.assistant/playlist.m3u8",
    ) as mock_stream_view_url, patch(
        "openpeerpower.components.demo.camera.DemoCamera.stream_source",
        return_value="http://example.com",
    ):
        # Request playlist through WebSocket
        client = await opp_ws_client(opp)
        await client.send_json(
            {"id": 6, "type": "camera/stream", "entity_id": "camera.demo_camera"}
        )
        msg = await client.receive_json()

        # Assert WebSocket response
        assert mock_stream_view_url.called
        assert msg["id"] == 6
        assert msg["type"] == TYPE_RESULT
        assert msg["success"]
        assert msg["result"]["url"][-13:] == "playlist.m3u8"


async def test_websocket_get_prefs(opp, opp_ws_client, mock_camera):
    """Test get camera preferences websocket command."""
    await async_setup_component(opp, "camera", {})

    # Request preferences through websocket
    client = await opp_ws_client(opp)
    await client.send_json(
        {"id": 7, "type": "camera/get_prefs", "entity_id": "camera.demo_camera"}
    )
    msg = await client.receive_json()

    # Assert WebSocket response
    assert msg["success"]


async def test_websocket_update_prefs(
    opp, opp_ws_client, mock_camera, setup_camera_prefs
):
    """Test updating preference."""
    await async_setup_component(opp, "camera", {})
    assert setup_camera_prefs[PREF_PRELOAD_STREAM]
    client = await opp_ws_client(opp)
    await client.send_json(
        {
            "id": 8,
            "type": "camera/update_prefs",
            "entity_id": "camera.demo_camera",
            "preload_stream": False,
        }
    )
    response = await client.receive_json()

    assert response["success"]
    assert not setup_camera_prefs[PREF_PRELOAD_STREAM]
    assert (
        response["result"][PREF_PRELOAD_STREAM]
        == setup_camera_prefs[PREF_PRELOAD_STREAM]
    )


async def test_play_stream_service_no_source(opp, mock_camera, mock_stream):
    """Test camera play_stream service."""
    data = {
        ATTR_ENTITY_ID: "camera.demo_camera",
        camera.ATTR_MEDIA_PLAYER: "media_player.test",
    }
    with pytest.raises(OpenPeerPowerError):
        # Call service
        await opp.services.async_call(
            camera.DOMAIN, camera.SERVICE_PLAY_STREAM, data, blocking=True
        )


async def test_handle_play_stream_service(opp, mock_camera, mock_stream):
    """Test camera play_stream service."""
    await async_process_op_core_config(
        opp,
        {"external_url": "https://example.com"},
    )
    await async_setup_component(opp, "media_player", {})
    with patch(
        "openpeerpower.components.camera.Stream.endpoint_url",
    ) as mock_request_stream, patch(
        "openpeerpower.components.demo.camera.DemoCamera.stream_source",
        return_value="http://example.com",
    ):
        # Call service
        await opp.services.async_call(
            camera.DOMAIN,
            camera.SERVICE_PLAY_STREAM,
            {
                ATTR_ENTITY_ID: "camera.demo_camera",
                camera.ATTR_MEDIA_PLAYER: "media_player.test",
            },
            blocking=True,
        )
        # So long as we request the stream, the rest should be covered
        # by the play_media service tests.
        assert mock_request_stream.called


async def test_no_preload_stream(opp, mock_stream):
    """Test camera preload preference."""
    demo_prefs = CameraEntityPreferences({PREF_PRELOAD_STREAM: False})
    with patch(
        "openpeerpower.components.camera.Stream.endpoint_url",
    ) as mock_request_stream, patch(
        "openpeerpower.components.camera.prefs.CameraPreferences.get",
        return_value=demo_prefs,
    ), patch(
        "openpeerpower.components.demo.camera.DemoCamera.stream_source",
        new_callable=PropertyMock,
    ) as mock_stream_source:
        mock_stream_source.return_value = io.BytesIO()
        await async_setup_component(opp, "camera", {DOMAIN: {"platform": "demo"}})
        opp.bus.async_fire(EVENT_OPENPEERPOWER_START)
        await opp.async_block_till_done()
        assert not mock_request_stream.called


async def test_preload_stream(opp, mock_stream):
    """Test camera preload preference."""
    demo_prefs = CameraEntityPreferences({PREF_PRELOAD_STREAM: True})
    with patch(
        "openpeerpower.components.camera.create_stream"
    ) as mock_create_stream, patch(
        "openpeerpower.components.camera.prefs.CameraPreferences.get",
        return_value=demo_prefs,
    ), patch(
        "openpeerpower.components.demo.camera.DemoCamera.stream_source",
        return_value="http://example.com",
    ):
        assert await async_setup_component(
            opp, "camera", {DOMAIN: {"platform": "demo"}}
        )
        await opp.async_block_till_done()
        opp.bus.async_fire(EVENT_OPENPEERPOWER_START)
        await opp.async_block_till_done()
        assert mock_create_stream.called


async def test_record_service_invalid_path(opp, mock_camera):
    """Test record service with invalid path."""
    with patch.object(
        opp.config, "is_allowed_path", return_value=False
    ), pytest.raises(OpenPeerPowerError):
        # Call service
        await opp.services.async_call(
            camera.DOMAIN,
            camera.SERVICE_RECORD,
            {
                ATTR_ENTITY_ID: "camera.demo_camera",
                camera.CONF_FILENAME: "/my/invalid/path",
            },
            blocking=True,
        )


async def test_record_service(opp, mock_camera, mock_stream):
    """Test record service."""
    with patch(
        "openpeerpower.components.demo.camera.DemoCamera.stream_source",
        return_value="http://example.com",
    ), patch(
        "openpeerpower.components.stream.Stream.async_record",
        autospec=True,
    ) as mock_record:
        # Call service
        await opp.services.async_call(
            camera.DOMAIN,
            camera.SERVICE_RECORD,
            {ATTR_ENTITY_ID: "camera.demo_camera", camera.CONF_FILENAME: "/my/path"},
            blocking=True,
        )
        # So long as we call stream.record, the rest should be covered
        # by those tests.
        assert mock_record.called
