"""Tests for the Abode camera device."""
from unittest.mock import patch

from openpeerpower.components.abode.const import DOMAIN as ABODE_DOMAIN
from openpeerpower.components.camera import DOMAIN as CAMERA_DOMAIN
from openpeerpower.const import ATTR_ENTITY_ID, STATE_IDLE

from .common import setup_platform


async def test_entity_registry.opp):
    """Tests that the devices are registered in the entity registry."""
    await setup_platform.opp, CAMERA_DOMAIN)
    entity_registry = await.opp.helpers.entity_registry.async_get_registry()

    entry = entity_registry.async_get("camera.test_cam")
    assert entry.unique_id == "d0a3a1c316891ceb00c20118aae2a133"


async def test_attributes.opp):
    """Test the camera attributes are correct."""
    await setup_platform.opp, CAMERA_DOMAIN)

    state = opp.states.get("camera.test_cam")
    assert state.state == STATE_IDLE


async def test_capture_image.opp):
    """Test the camera capture image service."""
    await setup_platform.opp, CAMERA_DOMAIN)

    with patch("abodepy.AbodeCamera.capture") as mock_capture:
        await.opp.services.async_call(
            ABODE_DOMAIN,
            "capture_image",
            {ATTR_ENTITY_ID: "camera.test_cam"},
            blocking=True,
        )
        await opp.async_block_till_done()
        mock_capture.assert_called_once()


async def test_camera_on.opp):
    """Test the camera turn on service."""
    await setup_platform.opp, CAMERA_DOMAIN)

    with patch("abodepy.AbodeCamera.privacy_mode") as mock_capture:
        await.opp.services.async_call(
            CAMERA_DOMAIN,
            "turn_on",
            {ATTR_ENTITY_ID: "camera.test_cam"},
            blocking=True,
        )
        await opp.async_block_till_done()
        mock_capture.assert_called_once_with(False)


async def test_camera_off.opp):
    """Test the camera turn off service."""
    await setup_platform.opp, CAMERA_DOMAIN)

    with patch("abodepy.AbodeCamera.privacy_mode") as mock_capture:
        await.opp.services.async_call(
            CAMERA_DOMAIN,
            "turn_off",
            {ATTR_ENTITY_ID: "camera.test_cam"},
            blocking=True,
        )
        await opp.async_block_till_done()
        mock_capture.assert_called_once_with(True)
