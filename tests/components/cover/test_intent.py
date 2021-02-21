"""The tests for the cover platform."""

from openpeerpower.components.cover import (
    SERVICE_CLOSE_COVER,
    SERVICE_OPEN_COVER,
    intent as cover_intent,
)
from openpeerpower.helpers import intent

from tests.common import async_mock_service


async def test_open_cover_intent.opp):
    """Test HassOpenCover intent."""
    await cover_intent.async_setup_intents.opp)

   .opp.states.async_set("cover.garage_door", "closed")
    calls = async_mock_service.opp, "cover", SERVICE_OPEN_COVER)

    response = await intent.async_handle(
       .opp, "test", "HassOpenCover", {"name": {"value": "garage door"}}
    )
    await.opp.async_block_till_done()

    assert response.speech["plain"]["speech"] == "Opened garage door"
    assert len(calls) == 1
    call = calls[0]
    assert call.domain == "cover"
    assert call.service == "open_cover"
    assert call.data == {"entity_id": "cover.garage_door"}


async def test_close_cover_intent.opp):
    """Test HassCloseCover intent."""
    await cover_intent.async_setup_intents.opp)

   .opp.states.async_set("cover.garage_door", "open")
    calls = async_mock_service.opp, "cover", SERVICE_CLOSE_COVER)

    response = await intent.async_handle(
       .opp, "test", "HassCloseCover", {"name": {"value": "garage door"}}
    )
    await.opp.async_block_till_done()

    assert response.speech["plain"]["speech"] == "Closed garage door"
    assert len(calls) == 1
    call = calls[0]
    assert call.domain == "cover"
    assert call.service == "close_cover"
    assert call.data == {"entity_id": "cover.garage_door"}
