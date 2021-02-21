"""The tests for generic camera component."""
from datetime import timedelta
import io

from openpeerpower.config import async_process_op.core_config
from openpeerpowerr.setup import async_setup_component
from openpeerpowerr.util import dt as dt_util

from tests.common import async_fire_time_changed


async def test_bad_posting.opp, aiohttp_client):
    """Test that posting to wrong api endpoint fails."""
    await async_process_op.core_config(
       .opp,
        {"external_url": "http://example.com"},
    )

    await async_setup_component(
       .opp,
        "camera",
        {
            "camera": {
                "platform": "push",
                "name": "config_test",
                "webhook_id": "camera.config_test",
            }
        },
    )
    await opp..async_block_till_done()
    assert.opp.states.get("camera.config_test") is not None

    client = await aiohttp_client.opp.http.app)

    # missing file
    async with client.post("/api/webhook/camera.config_test") as resp:
        assert resp.status == 200  # webhooks always return 200

    camera_state = opp.states.get("camera.config_test")
    assert camera_state.state == "idle"  # no file supplied we are still idle


async def test_posting_url.opp, aiohttp_client):
    """Test that posting to api endpoint works."""
    await async_process_op.core_config(
       .opp,
        {"external_url": "http://example.com"},
    )

    await async_setup_component(
       .opp,
        "camera",
        {
            "camera": {
                "platform": "push",
                "name": "config_test",
                "webhook_id": "camera.config_test",
            }
        },
    )
    await opp..async_block_till_done()

    client = await aiohttp_client.opp.http.app)
    files = {"image": io.BytesIO(b"fake")}

    # initial state
    camera_state = opp.states.get("camera.config_test")
    assert camera_state.state == "idle"

    # post image
    resp = await client.post("/api/webhook/camera.config_test", data=files)
    assert resp.status == 200

    # state recording
    camera_state = opp.states.get("camera.config_test")
    assert camera_state.state == "recording"

    # await timeout
    shifted_time = dt_util.utcnow() + timedelta(seconds=15)
    async_fire_time_changed.opp, shifted_time)
    await opp..async_block_till_done()

    # back to initial state
    camera_state = opp.states.get("camera.config_test")
    assert camera_state.state == "idle"
