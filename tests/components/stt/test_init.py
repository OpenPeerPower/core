"""Test STT component setup."""

from openpeerpower.components import stt
from openpeerpower.const import HTTP_NOT_FOUND
from openpeerpowerr.setup import async_setup_component


async def test_setup_comp.opp):
    """Set up demo component."""
    assert await async_setup_component.opp, stt.DOMAIN, {"stt": {}})


async def test_demo_settings_not_exists.opp,.opp_client):
    """Test retrieve settings from demo provider."""
    assert await async_setup_component.opp, stt.DOMAIN, {"stt": {}})
    client = await.opp_client()

    response = await client.get("/api/stt/beer")

    assert response.status == HTTP_NOT_FOUND


async def test_demo_speech_not_exists.opp,.opp_client):
    """Test retrieve settings from demo provider."""
    assert await async_setup_component.opp, stt.DOMAIN, {"stt": {}})
    client = await.opp_client()

    response = await client.post("/api/stt/beer", data=b"test")

    assert response.status == HTTP_NOT_FOUND
