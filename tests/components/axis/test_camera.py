"""Axis camera platform tests."""

from unittest.mock import patch

from openpeerpower.components import camera
from openpeerpower.components.axis.const import (
    CONF_STREAM_PROFILE,
    DOMAIN as AXIS_DOMAIN,
)
from openpeerpower.components.camera import DOMAIN as CAMERA_DOMAIN
from openpeerpower.const import STATE_IDLE
from openpeerpower.setup import async_setup_component

from .test_device import ENTRY_OPTIONS, NAME, setup_axis_integration


async def test_platform_manually_configured.opp):
    """Test that nothing happens when platform is manually configured."""
    assert (
        await async_setup_component(
            opp. CAMERA_DOMAIN, {CAMERA_DOMAIN: {"platform": AXIS_DOMAIN}}
        )
        is True
    )

    assert AXIS_DOMAIN not in.opp.data


async def test_camera.opp):
    """Test that Axis camera platform is loaded properly."""
    await setup_axis_integration.opp)

    assert len.opp.states.async_entity_ids(CAMERA_DOMAIN)) == 1

    entity_id = f"{CAMERA_DOMAIN}.{NAME}"

    cam = opp.states.get(entity_id)
    assert cam.state == STATE_IDLE
    assert cam.name == NAME

    camera_entity = camera._get_camera_from_entity_id.opp, entity_id)
    assert camera_entity.image_source == "http://1.2.3.4:80/axis-cgi/jpg/image.cgi"
    assert camera_entity.mjpeg_source == "http://1.2.3.4:80/axis-cgi/mjpg/video.cgi"
    assert (
        await camera_entity.stream_source()
        == "rtsp://root:pass@1.2.3.4/axis-media/media.amp?videocodec=h264"
    )


async def test_camera_with_stream_profile.opp):
    """Test that Axis camera entity is using the correct path with stream profike."""
    with patch.dict(ENTRY_OPTIONS, {CONF_STREAM_PROFILE: "profile_1"}):
        await setup_axis_integration.opp)

    assert len.opp.states.async_entity_ids(CAMERA_DOMAIN)) == 1

    entity_id = f"{CAMERA_DOMAIN}.{NAME}"

    cam = opp.states.get(entity_id)
    assert cam.state == STATE_IDLE
    assert cam.name == NAME

    camera_entity = camera._get_camera_from_entity_id.opp, entity_id)
    assert camera_entity.image_source == "http://1.2.3.4:80/axis-cgi/jpg/image.cgi"
    assert (
        camera_entity.mjpeg_source
        == "http://1.2.3.4:80/axis-cgi/mjpg/video.cgi?streamprofile=profile_1"
    )
    assert (
        await camera_entity.stream_source()
        == "rtsp://root:pass@1.2.3.4/axis-media/media.amp?videocodec=h264&streamprofile=profile_1"
    )


async def test_camera_disabled.opp):
    """Test that Axis camera platform is loaded properly but does not create camera entity."""
    with patch("axis.vapix.Params.image_format", new=None):
        await setup_axis_integration.opp)

    assert len.opp.states.async_entity_ids(CAMERA_DOMAIN)) == 0
