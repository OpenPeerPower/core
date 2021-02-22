"""Test different accessory types: Camera."""

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch
from uuid import UUID

from pyhap.accessory_driver import AccessoryDriver
import pytest

from openpeerpower.components import camera, ffmpeg
from openpeerpower.components.homekit.accessories import HomeBridge
from openpeerpower.components.homekit.const import (
    AUDIO_CODEC_COPY,
    CHAR_MOTION_DETECTED,
    CHAR_PROGRAMMABLE_SWITCH_EVENT,
    CONF_AUDIO_CODEC,
    CONF_LINKED_DOORBELL_SENSOR,
    CONF_LINKED_MOTION_SENSOR,
    CONF_STREAM_SOURCE,
    CONF_SUPPORT_AUDIO,
    CONF_VIDEO_CODEC,
    DEVICE_CLASS_MOTION,
    DEVICE_CLASS_OCCUPANCY,
    SERV_DOORBELL,
    SERV_MOTION_SENSOR,
    SERV_STATELESS_PROGRAMMABLE_SWITCH,
    VIDEO_CODEC_COPY,
    VIDEO_CODEC_H264_OMX,
)
from openpeerpower.components.homekit.img_util import TurboJPEGSingleton
from openpeerpower.components.homekit.type_cameras import Camera
from openpeerpower.components.homekit.type_switches import Switch
from openpeerpower.const import ATTR_DEVICE_CLASS, STATE_OFF, STATE_ON
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.setup import async_setup_component

from .common import mock_turbo_jpeg

MOCK_START_STREAM_TLV = "ARUCAQEBEDMD1QMXzEaatnKSQ2pxovYCNAEBAAIJAQECAgECAwEAAwsBAgAFAgLQAgMBHgQXAQFjAgQ768/RAwIrAQQEAAAAPwUCYgUDLAEBAwIMAQEBAgEAAwECBAEUAxYBAW4CBCzq28sDAhgABAQAAKBABgENBAEA"
MOCK_END_POINTS_TLV = "ARAzA9UDF8xGmrZykkNqcaL2AgEAAxoBAQACDTE5Mi4xNjguMjA4LjUDAi7IBAKkxwQlAQEAAhDN0+Y0tZ4jzoO0ske9UsjpAw6D76oVXnoi7DbawIG4CwUlAQEAAhCyGcROB8P7vFRDzNF2xrK1Aw6NdcLugju9yCfkWVSaVAYEDoAsAAcEpxV8AA=="
MOCK_START_STREAM_SESSION_UUID = UUID("3303d503-17cc-469a-b672-92436a71a2f6")

PID_THAT_WILL_NEVER_BE_ALIVE = 2147483647


async def _async_start_streaming.opp, acc):
    """Start streaming a camera."""
    acc.set_selected_stream_configuration(MOCK_START_STREAM_TLV)
    await acc.run()
    await opp.async_block_till_done()


async def _async_setup_endpoints.opp, acc):
    """Set camera endpoints."""
    acc.set_endpoints(MOCK_END_POINTS_TLV)
    await acc.run()
    await opp.async_block_till_done()


async def _async_reconfigure_stream.opp, acc, session_info, stream_config):
    """Reconfigure the stream."""
    await acc.reconfigure_stream(session_info, stream_config)
    await acc.run()
    await opp.async_block_till_done()


async def _async_stop_all_streams.opp, acc):
    """Stop all camera streams."""
    await acc.stop()
    await acc.run()
    await opp.async_block_till_done()


async def _async_stop_stream.opp, acc, session_info):
    """Stop a camera stream."""
    await acc.stop_stream(session_info)
    await acc.run()
    await opp.async_block_till_done()


@pytest.fixture()
def run_driver.opp):
    """Return a custom AccessoryDriver instance for HomeKit accessory init."""
    with patch("pyhap.accessory_driver.Zeroconf"), patch(
        "pyhap.accessory_driver.AccessoryEncoder"
    ), patch("pyhap.accessory_driver.HAPServer"), patch(
        "pyhap.accessory_driver.AccessoryDriver.publish"
    ), patch(
        "pyhap.accessory_driver.AccessoryDriver.persist"
    ):
        yield AccessoryDriver(
            pincode=b"123-45-678", address="127.0.0.1", loop.opp.loop
        )


def _get_exits_after_startup_mock_ffmpeg():
    """Return a ffmpeg that will have an invalid pid."""
    ffmpeg = MagicMock()
    type(ffmpeg.process).pid = PropertyMock(return_value=PID_THAT_WILL_NEVER_BE_ALIVE)
    ffmpeg.open = AsyncMock(return_value=True)
    ffmpeg.close = AsyncMock(return_value=True)
    ffmpeg.kill = AsyncMock(return_value=True)
    ffmpeg.get_reader = AsyncMock()
    return ffmpeg


def _get_working_mock_ffmpeg():
    """Return a working ffmpeg."""
    ffmpeg = MagicMock()
    ffmpeg.open = AsyncMock(return_value=True)
    ffmpeg.close = AsyncMock(return_value=True)
    ffmpeg.kill = AsyncMock(return_value=True)
    ffmpeg.get_reader = AsyncMock()
    return ffmpeg


def _get_failing_mock_ffmpeg():
    """Return an ffmpeg that fails to shutdown."""
    ffmpeg = MagicMock()
    type(ffmpeg.process).pid = PropertyMock(return_value=PID_THAT_WILL_NEVER_BE_ALIVE)
    ffmpeg.open = AsyncMock(return_value=False)
    ffmpeg.close = AsyncMock(side_effect=OSError)
    ffmpeg.kill = AsyncMock(side_effect=OSError)
    ffmpeg.get_reader = AsyncMock()
    return ffmpeg


async def test_camera_stream_source_configured.opp, run_driver, events):
    """Test a camera that can stream with a configured source."""
    await async_setup_component.opp, ffmpeg.DOMAIN, {ffmpeg.DOMAIN: {}})
    await async_setup_component(
       .opp, camera.DOMAIN, {camera.DOMAIN: {"platform": "demo"}}
    )
    await opp.async_block_till_done()

    entity_id = "camera.demo_camera"

   .opp.states.async_set(entity_id, None)
    await opp.async_block_till_done()
    acc = Camera(
       .opp,
        run_driver,
        "Camera",
        entity_id,
        2,
        {CONF_STREAM_SOURCE: "/dev/null", CONF_SUPPORT_AUDIO: True},
    )
    not_camera_acc = Switch(
       .opp,
        run_driver,
        "Switch",
        entity_id,
        4,
        {},
    )
    bridge = HomeBridge(.opp", run_driver, "Test Bridge")
    bridge.add_accessory(acc)
    bridge.add_accessory(not_camera_acc)

    await acc.run()

    assert acc.aid == 2
    assert acc.category == 17  # Camera

    await _async_setup_endpoints.opp, acc)
    working_ffmpeg = _get_working_mock_ffmpeg()
    session_info = acc.sessions[MOCK_START_STREAM_SESSION_UUID]

    with patch(
        "openpeerpower.components.demo.camera.DemoCamera.stream_source",
        return_value=None,
    ), patch(
        "openpeerpower.components.homekit.type_cameras.HAFFmpeg",
        return_value=working_ffmpeg,
    ):
        await _async_start_streaming.opp, acc)
        await _async_stop_all_streams.opp, acc)

    expected_output = (
        "-map 0:v:0 -an -c:v libx264 -profile:v high -tune zerolatency -pix_fmt "
        "yuv420p -r 30 -b:v 299k -bufsize 1196k -maxrate 299k -payload_type 99 -ssrc {v_ssrc} -f "
        "rtp -srtp_out_suite AES_CM_128_HMAC_SHA1_80 -srtp_out_params "
        "zdPmNLWeI86DtLJHvVLI6YPvqhVeeiLsNtrAgbgL "
        "srtp://192.168.208.5:51246?rtcpport=51246&localrtcpport=51246&pkt_size=1316 -map 0:a:0 "
        "-vn -c:a libopus -application lowdelay -ac 1 -ar 24k -b:a 24k -bufsize 96k -payload_type "
        "110 -ssrc {a_ssrc} -f rtp -srtp_out_suite AES_CM_128_HMAC_SHA1_80 -srtp_out_params "
        "shnETgfD+7xUQ8zRdsaytY11wu6CO73IJ+RZVJpU "
        "srtp://192.168.208.5:51108?rtcpport=51108&localrtcpport=51108&pkt_size=188"
    )

    working_ffmpeg.open.assert_called_with(
        cmd=[],
        input_source="-i /dev/null",
        output=expected_output.format(**session_info),
        stdout_pipe=False,
        extra_cmd="-hide_banner -nostats",
        stderr_pipe=True,
    )

    await _async_setup_endpoints.opp, acc)
    working_ffmpeg = _get_working_mock_ffmpeg()
    session_info = acc.sessions[MOCK_START_STREAM_SESSION_UUID]

    with patch(
        "openpeerpower.components.demo.camera.DemoCamera.stream_source",
        return_value="rtsp://example.local",
    ), patch(
        "openpeerpower.components.homekit.type_cameras.HAFFmpeg",
        return_value=working_ffmpeg,
    ):
        await _async_start_streaming.opp, acc)
        await _async_stop_all_streams.opp, acc)
        # Calling a second time should not throw
        await _async_stop_all_streams.opp, acc)

    turbo_jpeg = mock_turbo_jpeg(
        first_width=16, first_height=12, second_width=300, second_height=200
    )
    with patch("turbojpeg.TurboJPEG", return_value=turbo_jpeg):
        TurboJPEGSingleton()
        assert await acc.async_get_snapshot(
            {"aid": 2, "image-width": 300, "image-height": 200}
        )
        # Verify the bridge only forwards async_get_snapshot for
        # cameras and valid accessory ids
        assert await bridge.async_get_snapshot(
            {"aid": 2, "image-width": 300, "image-height": 200}
        )

    with pytest.raises(ValueError):
        assert await bridge.async_get_snapshot(
            {"aid": 3, "image-width": 300, "image-height": 200}
        )

    with pytest.raises(ValueError):
        assert await bridge.async_get_snapshot(
            {"aid": 4, "image-width": 300, "image-height": 200}
        )


async def test_camera_stream_source_configured_with_failing_ffmpeg(
   .opp, run_driver, events
):
    """Test a camera that can stream with a configured source with ffmpeg failing."""
    await async_setup_component.opp, ffmpeg.DOMAIN, {ffmpeg.DOMAIN: {}})
    await async_setup_component(
       .opp, camera.DOMAIN, {camera.DOMAIN: {"platform": "demo"}}
    )
    await opp.async_block_till_done()

    entity_id = "camera.demo_camera"

   .opp.states.async_set(entity_id, None)
    await opp.async_block_till_done()
    acc = Camera(
       .opp,
        run_driver,
        "Camera",
        entity_id,
        2,
        {CONF_STREAM_SOURCE: "/dev/null", CONF_SUPPORT_AUDIO: True},
    )
    not_camera_acc = Switch(
       .opp,
        run_driver,
        "Switch",
        entity_id,
        4,
        {},
    )
    bridge = HomeBridge(.opp", run_driver, "Test Bridge")
    bridge.add_accessory(acc)
    bridge.add_accessory(not_camera_acc)

    await acc.run()

    assert acc.aid == 2
    assert acc.category == 17  # Camera

    await _async_setup_endpoints.opp, acc)

    with patch(
        "openpeerpower.components.demo.camera.DemoCamera.stream_source",
        return_value="rtsp://example.local",
    ), patch(
        "openpeerpower.components.homekit.type_cameras.HAFFmpeg",
        return_value=_get_failing_mock_ffmpeg(),
    ):
        await _async_start_streaming.opp, acc)
        await _async_stop_all_streams.opp, acc)
        # Calling a second time should not throw
        await _async_stop_all_streams.opp, acc)


async def test_camera_stream_source_found.opp, run_driver, events):
    """Test a camera that can stream and we get the source from the entity."""
    await async_setup_component.opp, ffmpeg.DOMAIN, {ffmpeg.DOMAIN: {}})
    await async_setup_component(
       .opp, camera.DOMAIN, {camera.DOMAIN: {"platform": "demo"}}
    )
    await opp.async_block_till_done()

    entity_id = "camera.demo_camera"

   .opp.states.async_set(entity_id, None)
    await opp.async_block_till_done()
    acc = Camera(
       .opp,
        run_driver,
        "Camera",
        entity_id,
        2,
        {},
    )
    await acc.run()

    assert acc.aid == 2
    assert acc.category == 17  # Camera

    await _async_setup_endpoints.opp, acc)

    with patch(
        "openpeerpower.components.demo.camera.DemoCamera.stream_source",
        return_value="rtsp://example.local",
    ), patch(
        "openpeerpower.components.homekit.type_cameras.HAFFmpeg",
        return_value=_get_working_mock_ffmpeg(),
    ):
        await _async_start_streaming.opp, acc)
        await _async_stop_all_streams.opp, acc)

    await _async_setup_endpoints.opp, acc)

    with patch(
        "openpeerpower.components.demo.camera.DemoCamera.stream_source",
        return_value="rtsp://example.local",
    ), patch(
        "openpeerpower.components.homekit.type_cameras.HAFFmpeg",
        return_value=_get_working_mock_ffmpeg(),
    ):
        await _async_start_streaming.opp, acc)
        await _async_stop_all_streams.opp, acc)


async def test_camera_stream_source_fails.opp, run_driver, events):
    """Test a camera that can stream and we cannot get the source from the entity."""
    await async_setup_component.opp, ffmpeg.DOMAIN, {ffmpeg.DOMAIN: {}})
    await async_setup_component(
       .opp, camera.DOMAIN, {camera.DOMAIN: {"platform": "demo"}}
    )
    await opp.async_block_till_done()

    entity_id = "camera.demo_camera"

   .opp.states.async_set(entity_id, None)
    await opp.async_block_till_done()
    acc = Camera(
       .opp,
        run_driver,
        "Camera",
        entity_id,
        2,
        {},
    )
    await acc.run()

    assert acc.aid == 2
    assert acc.category == 17  # Camera

    await _async_setup_endpoints.opp, acc)

    with patch(
        "openpeerpower.components.demo.camera.DemoCamera.stream_source",
        side_effect=OSError,
    ), patch(
        "openpeerpower.components.homekit.type_cameras.HAFFmpeg",
        return_value=_get_working_mock_ffmpeg(),
    ):
        await _async_start_streaming.opp, acc)
        await _async_stop_all_streams.opp, acc)


async def test_camera_with_no_stream.opp, run_driver, events):
    """Test a camera that cannot stream."""
    await async_setup_component.opp, ffmpeg.DOMAIN, {ffmpeg.DOMAIN: {}})
    await async_setup_component.opp, camera.DOMAIN, {camera.DOMAIN: {}})

    entity_id = "camera.demo_camera"

   .opp.states.async_set(entity_id, None)
    await opp.async_block_till_done()
    acc = Camera(
       .opp,
        run_driver,
        "Camera",
        entity_id,
        2,
        {},
    )
    await acc.run()

    assert acc.aid == 2
    assert acc.category == 17  # Camera

    await _async_setup_endpoints.opp, acc)
    await _async_start_streaming.opp, acc)
    await _async_stop_all_streams.opp, acc)

    with pytest.raises(OpenPeerPowerError):
        assert await acc.async_get_snapshot(
            {"aid": 2, "image-width": 300, "image-height": 200}
        )


async def test_camera_stream_source_configured_and_copy_codec.opp, run_driver, events):
    """Test a camera that can stream with a configured source."""
    await async_setup_component.opp, ffmpeg.DOMAIN, {ffmpeg.DOMAIN: {}})
    await async_setup_component(
       .opp, camera.DOMAIN, {camera.DOMAIN: {"platform": "demo"}}
    )
    await opp.async_block_till_done()

    entity_id = "camera.demo_camera"

   .opp.states.async_set(entity_id, None)
    await opp.async_block_till_done()
    acc = Camera(
       .opp,
        run_driver,
        "Camera",
        entity_id,
        2,
        {
            CONF_STREAM_SOURCE: "/dev/null",
            CONF_SUPPORT_AUDIO: True,
            CONF_VIDEO_CODEC: VIDEO_CODEC_COPY,
            CONF_AUDIO_CODEC: AUDIO_CODEC_COPY,
        },
    )
    bridge = HomeBridge(.opp", run_driver, "Test Bridge")
    bridge.add_accessory(acc)

    await acc.run()

    assert acc.aid == 2
    assert acc.category == 17  # Camera

    await _async_setup_endpoints.opp, acc)
    session_info = acc.sessions[MOCK_START_STREAM_SESSION_UUID]

    working_ffmpeg = _get_working_mock_ffmpeg()

    with patch(
        "openpeerpower.components.demo.camera.DemoCamera.stream_source",
        return_value=None,
    ), patch(
        "openpeerpower.components.homekit.type_cameras.HAFFmpeg",
        return_value=working_ffmpeg,
    ):
        await _async_start_streaming.opp, acc)
        await _async_reconfigure_stream.opp, acc, session_info, {})
        await _async_stop_stream.opp, acc, session_info)
        await _async_stop_all_streams.opp, acc)

    expected_output = (
        "-map 0:v:0 -an -c:v copy -tune zerolatency -pix_fmt yuv420p -r 30 -b:v 299k "
        "-bufsize 1196k -maxrate 299k -payload_type 99 -ssrc {v_ssrc} -f rtp -srtp_out_suite "
        "AES_CM_128_HMAC_SHA1_80 -srtp_out_params zdPmNLWeI86DtLJHvVLI6YPvqhVeeiLsNtrAgbgL "
        "srtp://192.168.208.5:51246?rtcpport=51246&localrtcpport=51246&pkt_size=1316 -map 0:a:0 "
        "-vn -c:a copy -ac 1 -ar 24k -b:a 24k -bufsize 96k -payload_type 110 -ssrc {a_ssrc} "
        "-f rtp -srtp_out_suite AES_CM_128_HMAC_SHA1_80 -srtp_out_params "
        "shnETgfD+7xUQ8zRdsaytY11wu6CO73IJ+RZVJpU "
        "srtp://192.168.208.5:51108?rtcpport=51108&localrtcpport=51108&pkt_size=188"
    )

    working_ffmpeg.open.assert_called_with(
        cmd=[],
        input_source="-i /dev/null",
        output=expected_output.format(**session_info),
        stdout_pipe=False,
        extra_cmd="-hide_banner -nostats",
        stderr_pipe=True,
    )


async def test_camera_streaming_fails_after_starting_ffmpeg.opp, run_driver, events):
    """Test a camera that can stream with a configured source."""
    await async_setup_component.opp, ffmpeg.DOMAIN, {ffmpeg.DOMAIN: {}})
    await async_setup_component(
       .opp, camera.DOMAIN, {camera.DOMAIN: {"platform": "demo"}}
    )
    await opp.async_block_till_done()

    entity_id = "camera.demo_camera"

   .opp.states.async_set(entity_id, None)
    await opp.async_block_till_done()
    acc = Camera(
       .opp,
        run_driver,
        "Camera",
        entity_id,
        2,
        {
            CONF_STREAM_SOURCE: "/dev/null",
            CONF_SUPPORT_AUDIO: True,
            CONF_VIDEO_CODEC: VIDEO_CODEC_H264_OMX,
            CONF_AUDIO_CODEC: AUDIO_CODEC_COPY,
        },
    )
    bridge = HomeBridge(.opp", run_driver, "Test Bridge")
    bridge.add_accessory(acc)

    await acc.run()

    assert acc.aid == 2
    assert acc.category == 17  # Camera

    await _async_setup_endpoints.opp, acc)
    session_info = acc.sessions[MOCK_START_STREAM_SESSION_UUID]

    ffmpeg_with_invalid_pid = _get_exits_after_startup_mock_ffmpeg()

    with patch(
        "openpeerpower.components.demo.camera.DemoCamera.stream_source",
        return_value=None,
    ), patch(
        "openpeerpower.components.homekit.type_cameras.HAFFmpeg",
        return_value=ffmpeg_with_invalid_pid,
    ):
        await _async_start_streaming.opp, acc)
        await _async_reconfigure_stream.opp, acc, session_info, {})
        # Should not throw
        await _async_stop_stream.opp, acc, {"id": "does_not_exist"})
        await _async_stop_all_streams.opp, acc)

    expected_output = (
        "-map 0:v:0 -an -c:v h264_omx -profile:v high -tune zerolatency -pix_fmt yuv420p -r 30 -b:v 299k "
        "-bufsize 1196k -maxrate 299k -payload_type 99 -ssrc {v_ssrc} -f rtp -srtp_out_suite "
        "AES_CM_128_HMAC_SHA1_80 -srtp_out_params zdPmNLWeI86DtLJHvVLI6YPvqhVeeiLsNtrAgbgL "
        "srtp://192.168.208.5:51246?rtcpport=51246&localrtcpport=51246&pkt_size=1316 -map 0:a:0 "
        "-vn -c:a copy -ac 1 -ar 24k -b:a 24k -bufsize 96k -payload_type 110 -ssrc {a_ssrc} "
        "-f rtp -srtp_out_suite AES_CM_128_HMAC_SHA1_80 -srtp_out_params "
        "shnETgfD+7xUQ8zRdsaytY11wu6CO73IJ+RZVJpU "
        "srtp://192.168.208.5:51108?rtcpport=51108&localrtcpport=51108&pkt_size=188"
    )

    ffmpeg_with_invalid_pid.open.assert_called_with(
        cmd=[],
        input_source="-i /dev/null",
        output=expected_output.format(**session_info),
        stdout_pipe=False,
        extra_cmd="-hide_banner -nostats",
        stderr_pipe=True,
    )


async def test_camera_with_linked_motion_sensor.opp, run_driver, events):
    """Test a camera with a linked motion sensor can update."""
    await async_setup_component.opp, ffmpeg.DOMAIN, {ffmpeg.DOMAIN: {}})
    await async_setup_component(
       .opp, camera.DOMAIN, {camera.DOMAIN: {"platform": "demo"}}
    )
    await opp.async_block_till_done()
    motion_entity_id = "binary_sensor.motion"

   .opp.states.async_set(
        motion_entity_id, STATE_ON, {ATTR_DEVICE_CLASS: DEVICE_CLASS_MOTION}
    )
    await opp.async_block_till_done()
    entity_id = "camera.demo_camera"

   .opp.states.async_set(entity_id, None)
    await opp.async_block_till_done()
    acc = Camera(
       .opp,
        run_driver,
        "Camera",
        entity_id,
        2,
        {
            CONF_STREAM_SOURCE: "/dev/null",
            CONF_SUPPORT_AUDIO: True,
            CONF_VIDEO_CODEC: VIDEO_CODEC_H264_OMX,
            CONF_AUDIO_CODEC: AUDIO_CODEC_COPY,
            CONF_LINKED_MOTION_SENSOR: motion_entity_id,
        },
    )
    bridge = HomeBridge(.opp", run_driver, "Test Bridge")
    bridge.add_accessory(acc)

    await acc.run()

    assert acc.aid == 2
    assert acc.category == 17  # Camera

    service = acc.get_service(SERV_MOTION_SENSOR)
    assert service
    char = service.get_characteristic(CHAR_MOTION_DETECTED)
    assert char

    assert char.value is True

   .opp.states.async_set(
        motion_entity_id, STATE_OFF, {ATTR_DEVICE_CLASS: DEVICE_CLASS_MOTION}
    )
    await opp.async_block_till_done()
    assert char.value is False

    char.set_value(True)
   .opp.states.async_set(
        motion_entity_id, STATE_ON, {ATTR_DEVICE_CLASS: DEVICE_CLASS_MOTION}
    )
    await opp.async_block_till_done()
    assert char.value is True

    # Ensure we do not throw when the linked
    # motion sensor is removed
   .opp.states.async_remove(motion_entity_id)
    await opp.async_block_till_done()
    await acc.run()
    await opp.async_block_till_done()
    assert char.value is True


async def test_camera_with_a_missing_linked_motion_sensor.opp, run_driver, events):
    """Test a camera with a configured linked motion sensor that is missing."""
    await async_setup_component.opp, ffmpeg.DOMAIN, {ffmpeg.DOMAIN: {}})
    await async_setup_component(
       .opp, camera.DOMAIN, {camera.DOMAIN: {"platform": "demo"}}
    )
    await opp.async_block_till_done()
    motion_entity_id = "binary_sensor.motion"
    entity_id = "camera.demo_camera"
   .opp.states.async_set(entity_id, None)
    await opp.async_block_till_done()
    acc = Camera(
       .opp,
        run_driver,
        "Camera",
        entity_id,
        2,
        {CONF_LINKED_MOTION_SENSOR: motion_entity_id},
    )
    bridge = HomeBridge(.opp", run_driver, "Test Bridge")
    bridge.add_accessory(acc)

    await acc.run()

    assert acc.aid == 2
    assert acc.category == 17  # Camera

    assert not acc.get_service(SERV_MOTION_SENSOR)


async def test_camera_with_linked_doorbell_sensor.opp, run_driver, events):
    """Test a camera with a linked doorbell sensor can update."""
    await async_setup_component.opp, ffmpeg.DOMAIN, {ffmpeg.DOMAIN: {}})
    await async_setup_component(
       .opp, camera.DOMAIN, {camera.DOMAIN: {"platform": "demo"}}
    )
    await opp.async_block_till_done()
    doorbell_entity_id = "binary_sensor.doorbell"

   .opp.states.async_set(
        doorbell_entity_id, STATE_ON, {ATTR_DEVICE_CLASS: DEVICE_CLASS_OCCUPANCY}
    )
    await opp.async_block_till_done()
    entity_id = "camera.demo_camera"

   .opp.states.async_set(entity_id, None)
    await opp.async_block_till_done()
    acc = Camera(
       .opp,
        run_driver,
        "Camera",
        entity_id,
        2,
        {
            CONF_STREAM_SOURCE: "/dev/null",
            CONF_SUPPORT_AUDIO: True,
            CONF_VIDEO_CODEC: VIDEO_CODEC_H264_OMX,
            CONF_AUDIO_CODEC: AUDIO_CODEC_COPY,
            CONF_LINKED_DOORBELL_SENSOR: doorbell_entity_id,
        },
    )
    bridge = HomeBridge(.opp", run_driver, "Test Bridge")
    bridge.add_accessory(acc)

    await acc.run()

    assert acc.aid == 2
    assert acc.category == 17  # Camera

    service = acc.get_service(SERV_DOORBELL)
    assert service
    char = service.get_characteristic(CHAR_PROGRAMMABLE_SWITCH_EVENT)
    assert char

    assert char.value == 0

    service2 = acc.get_service(SERV_STATELESS_PROGRAMMABLE_SWITCH)
    assert service2
    char2 = service.get_characteristic(CHAR_PROGRAMMABLE_SWITCH_EVENT)
    assert char2

    assert char2.value == 0

   .opp.states.async_set(
        doorbell_entity_id, STATE_OFF, {ATTR_DEVICE_CLASS: DEVICE_CLASS_OCCUPANCY}
    )
    await opp.async_block_till_done()
    assert char.value == 0
    assert char2.value == 0

    char.set_value(True)
    char2.set_value(True)
   .opp.states.async_set(
        doorbell_entity_id, STATE_ON, {ATTR_DEVICE_CLASS: DEVICE_CLASS_OCCUPANCY}
    )
    await opp.async_block_till_done()
    assert char.value == 0
    assert char2.value == 0

    # Ensure we do not throw when the linked
    # doorbell sensor is removed
   .opp.states.async_remove(doorbell_entity_id)
    await opp.async_block_till_done()
    await acc.run()
    await opp.async_block_till_done()
    assert char.value == 0
    assert char2.value == 0


async def test_camera_with_a_missing_linked_doorbell_sensor.opp, run_driver, events):
    """Test a camera with a configured linked doorbell sensor that is missing."""
    await async_setup_component.opp, ffmpeg.DOMAIN, {ffmpeg.DOMAIN: {}})
    await async_setup_component(
       .opp, camera.DOMAIN, {camera.DOMAIN: {"platform": "demo"}}
    )
    await opp.async_block_till_done()
    doorbell_entity_id = "binary_sensor.doorbell"
    entity_id = "camera.demo_camera"
   .opp.states.async_set(entity_id, None)
    await opp.async_block_till_done()
    acc = Camera(
       .opp,
        run_driver,
        "Camera",
        entity_id,
        2,
        {CONF_LINKED_DOORBELL_SENSOR: doorbell_entity_id},
    )
    bridge = HomeBridge(.opp", run_driver, "Test Bridge")
    bridge.add_accessory(acc)

    await acc.run()

    assert acc.aid == 2
    assert acc.category == 17  # Camera

    assert not acc.get_service(SERV_DOORBELL)
    assert not acc.get_service(SERV_STATELESS_PROGRAMMABLE_SWITCH)
