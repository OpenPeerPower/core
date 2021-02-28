"""The tests for local file camera component."""
from unittest.mock import patch

import pytest

from openpeerpower.components.camera import (
    DOMAIN as CAMERA_DOMAIN,
    SERVICE_DISABLE_MOTION,
    SERVICE_ENABLE_MOTION,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_IDLE,
    STATE_STREAMING,
    async_get_image,
)
from openpeerpower.components.demo import DOMAIN
from openpeerpower.const import ATTR_ENTITY_ID
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.setup import async_setup_component

ENTITY_CAMERA = "camera.demo_camera"


@pytest.fixture(autouse=True)
async def demo_camera(opp):
    """Initialize a demo camera platform."""
    assert await async_setup_component(
        opp. CAMERA_DOMAIN, {CAMERA_DOMAIN: {"platform": DOMAIN}}
    )
    await opp.async_block_till_done()


async def test_init_state_is_streaming(opp):
    """Demo camera initialize as streaming."""
    state = opp.states.get(ENTITY_CAMERA)
    assert state.state == STATE_STREAMING

    with patch(
        "openpeerpower.components.demo.camera.Path.read_bytes", return_value=b"ON"
    ) as mock_read_bytes:
        image = await async_get_image(opp, ENTITY_CAMERA)
        assert mock_read_bytes.call_count == 1
        assert image.content == b"ON"


async def test_turn_on_state_back_to_streaming(opp):
    """After turn on state back to streaming."""
    state = opp.states.get(ENTITY_CAMERA)
    assert state.state == STATE_STREAMING

    await opp.services.async_call(
        CAMERA_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_CAMERA}, blocking=True
    )

    state = opp.states.get(ENTITY_CAMERA)
    assert state.state == STATE_IDLE

    await opp.services.async_call(
        CAMERA_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_CAMERA}, blocking=True
    )

    state = opp.states.get(ENTITY_CAMERA)
    assert state.state == STATE_STREAMING


async def test_turn_off_image(opp):
    """After turn off, Demo camera raise error."""
    await opp.services.async_call(
        CAMERA_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_CAMERA}, blocking=True
    )

    with pytest.raises(OpenPeerPowerError) as error:
        await async_get_image(opp, ENTITY_CAMERA)
        assert error.args[0] == "Camera is off"


async def test_turn_off_invalid_camera(opp):
    """Turn off non-exist camera should quietly fail."""
    state = opp.states.get(ENTITY_CAMERA)
    assert state.state == STATE_STREAMING

    await opp.services.async_call(
        CAMERA_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "camera.invalid_camera"},
        blocking=True,
    )

    state = opp.states.get(ENTITY_CAMERA)
    assert state.state == STATE_STREAMING


async def test_motion_detection(opp):
    """Test motion detection services."""

    # Fetch state and check motion detection attribute
    state = opp.states.get(ENTITY_CAMERA)
    assert not state.attributes.get("motion_detection")

    # Call service to turn on motion detection
    await opp.services.async_call(
        CAMERA_DOMAIN,
        SERVICE_ENABLE_MOTION,
        {ATTR_ENTITY_ID: ENTITY_CAMERA},
        blocking=True,
    )

    # Check if state has been updated.
    state = opp.states.get(ENTITY_CAMERA)
    assert state.attributes.get("motion_detection")

    # Call service to turn off motion detection
    await opp.services.async_call(
        CAMERA_DOMAIN,
        SERVICE_DISABLE_MOTION,
        {ATTR_ENTITY_ID: ENTITY_CAMERA},
        blocking=True,
    )

    # Check if state has been updated.
    state = opp.states.get(ENTITY_CAMERA)
    assert not state.attributes.get("motion_detection")
