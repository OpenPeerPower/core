"""The camera tests for the august platform."""

from unittest.mock import patch

from openpeerpower.const import STATE_IDLE

from tests.components.august.mocks import (
    _create_august_with_devices,
    _mock_doorbell_from_fixture,
)


async def test_create_doorbell(opp, aiohttp_client):
    """Test creation of a doorbell."""
    doorbell_one = await _mock_doorbell_from_fixture(opp, "get_doorbell.json")

    with patch.object(
        doorbell_one, "async_get_doorbell_image", create=False, return_value="image"
    ):
        await _create_august_with_devices(opp, [doorbell_one])

        camera_k98gidt45gul_name_camera = opp.states.get(
            "camera.k98gidt45gul_name_camera"
        )
        assert camera_k98gidt45gul_name_camera.state == STATE_IDLE

        url = opp.states.get("camera.k98gidt45gul_name_camera").attributes[
            "entity_picture"
        ]

        client = await aiohttp_client(opp.http.app)
        resp = await client.get(url)
        assert resp.status == 200
        body = await resp.text()
        assert body == "image"
