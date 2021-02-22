"""Tests for Intent component."""
import pytest

from openpeerpower.components.cover import SERVICE_OPEN_COVER
from openpeerpower.const import SERVICE_TOGGLE, SERVICE_TURN_OFF, SERVICE_TURN_ON
from openpeerpower.helpers import intent
from openpeerpower.setup import async_setup_component

from tests.common import async_mock_service


async def test_http_handle_intent.opp, opp_client, opp_admin_user):
    """Test handle intent via HTTP API."""

    class TestIntentHandler(intent.IntentHandler):
        """Test Intent Handler."""

        intent_type = "OrderBeer"

        async def async_handle(self, intent):
            """Handle the intent."""
            assert intent.context.user_id ==.opp_admin_user.id
            response = intent.create_response()
            response.async_set_speech(
                "I've ordered a {}!".format(intent.slots["type"]["value"])
            )
            response.async_set_card(
                "Beer ordered", "You chose a {}.".format(intent.slots["type"]["value"])
            )
            return response

    intent.async_register.opp, TestIntentHandler())

    result = await async_setup_component.opp, "intent", {})
    assert result

    client = await.opp_client()
    resp = await client.post(
        "/api/intent/handle", json={"name": "OrderBeer", "data": {"type": "Belgian"}}
    )

    assert resp.status == 200
    data = await resp.json()

    assert data == {
        "card": {
            "simple": {"content": "You chose a Belgian.", "title": "Beer ordered"}
        },
        "speech": {"plain": {"extra_data": None, "speech": "I've ordered a Belgian!"}},
    }


async def test_cover_intents_loading.opp):
    """Test Cover Intents Loading."""
    assert await async_setup_component.opp, "intent", {})

    with pytest.raises(intent.UnknownIntent):
        await intent.async_handle(
           .opp, "test", "HassOpenCover", {"name": {"value": "garage door"}}
        )

    assert await async_setup_component.opp, "cover", {})

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


async def test_turn_on_intent.opp):
    """Test HassTurnOn intent."""
    result = await async_setup_component.opp, "openpeerpower", {})
    result = await async_setup_component.opp, "intent", {})
    assert result

   .opp.states.async_set("light.test_light", "off")
    calls = async_mock_service.opp, "light", SERVICE_TURN_ON)

    response = await intent.async_handle(
       .opp, "test", "HassTurnOn", {"name": {"value": "test light"}}
    )
    await.opp.async_block_till_done()

    assert response.speech["plain"]["speech"] == "Turned test light on"
    assert len(calls) == 1
    call = calls[0]
    assert call.domain == "light"
    assert call.service == "turn_on"
    assert call.data == {"entity_id": ["light.test_light"]}


async def test_turn_off_intent.opp):
    """Test HassTurnOff intent."""
    result = await async_setup_component.opp, "openpeerpower", {})
    result = await async_setup_component.opp, "intent", {})
    assert result

   .opp.states.async_set("light.test_light", "on")
    calls = async_mock_service.opp, "light", SERVICE_TURN_OFF)

    response = await intent.async_handle(
       .opp, "test", "HassTurnOff", {"name": {"value": "test light"}}
    )
    await.opp.async_block_till_done()

    assert response.speech["plain"]["speech"] == "Turned test light off"
    assert len(calls) == 1
    call = calls[0]
    assert call.domain == "light"
    assert call.service == "turn_off"
    assert call.data == {"entity_id": ["light.test_light"]}


async def test_toggle_intent.opp):
    """Test HassToggle intent."""
    result = await async_setup_component.opp, "openpeerpower", {})
    result = await async_setup_component.opp, "intent", {})
    assert result

   .opp.states.async_set("light.test_light", "off")
    calls = async_mock_service.opp, "light", SERVICE_TOGGLE)

    response = await intent.async_handle(
       .opp, "test", "HassToggle", {"name": {"value": "test light"}}
    )
    await.opp.async_block_till_done()

    assert response.speech["plain"]["speech"] == "Toggled test light"
    assert len(calls) == 1
    call = calls[0]
    assert call.domain == "light"
    assert call.service == "toggle"
    assert call.data == {"entity_id": ["light.test_light"]}


async def test_turn_on_multiple_intent.opp):
    """Test HassTurnOn intent with multiple similar entities.

    This tests that matching finds the proper entity among similar names.
    """
    result = await async_setup_component.opp, "openpeerpower", {})
    result = await async_setup_component.opp, "intent", {})
    assert result

   .opp.states.async_set("light.test_light", "off")
   .opp.states.async_set("light.test_lights_2", "off")
   .opp.states.async_set("light.test_lighter", "off")
    calls = async_mock_service.opp, "light", SERVICE_TURN_ON)

    response = await intent.async_handle(
       .opp, "test", "HassTurnOn", {"name": {"value": "test lights"}}
    )
    await.opp.async_block_till_done()

    assert response.speech["plain"]["speech"] == "Turned test lights 2 on"
    assert len(calls) == 1
    call = calls[0]
    assert call.domain == "light"
    assert call.service == "turn_on"
    assert call.data == {"entity_id": ["light.test_lights_2"]}
