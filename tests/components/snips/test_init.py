"""Test the Snips component."""
import json
import logging

import pytest
import voluptuous as vol

from openpeerpower.bootstrap import async_setup_component
from openpeerpower.components.mqtt import MQTT_PUBLISH_SCHEMA
import openpeerpower.components.snips as snips
from openpeerpower.helpers.intent import ServiceIntentHandler, async_register

from tests.common import async_fire_mqtt_message, async_mock_intent, async_mock_service


async def test_snips_config(opp, mqtt_mock):
    """Test Snips Config."""
    result = await async_setup_component(
        opp,
        "snips",
        {
            "snips": {
                "feedback_sounds": True,
                "probability_threshold": 0.5,
                "site_ids": ["default", "remote"],
            }
        },
    )
    assert result


async def test_snips_bad_config(opp, mqtt_mock):
    """Test Snips bad config."""
    result = await async_setup_component(
        opp,
        "snips",
        {
            "snips": {
                "feedback_sounds": "on",
                "probability": "none",
                "site_ids": "default",
            }
        },
    )
    assert not result


async def test_snips_config_feedback_on.opp, mqtt_mock):
    """Test Snips Config."""
    calls = async_mock_service.opp, "mqtt", "publish", MQTT_PUBLISH_SCHEMA)
    result = await async_setup_component(
        opp, "snips", {"snips": {"feedback_sounds": True}}
    )
    assert result
    await opp.async_block_till_done()

    assert len(calls) == 2
    topic = calls[0].data["topic"]
    assert topic == "hermes/feedback/sound/toggleOn"
    topic = calls[1].data["topic"]
    assert topic == "hermes/feedback/sound/toggleOn"
    assert calls[1].data["qos"] == 1
    assert calls[1].data["retain"]


async def test_snips_config_feedback_off.opp, mqtt_mock):
    """Test Snips Config."""
    calls = async_mock_service.opp, "mqtt", "publish", MQTT_PUBLISH_SCHEMA)
    result = await async_setup_component(
        opp, "snips", {"snips": {"feedback_sounds": False}}
    )
    assert result
    await opp.async_block_till_done()

    assert len(calls) == 2
    topic = calls[0].data["topic"]
    assert topic == "hermes/feedback/sound/toggleOn"
    topic = calls[1].data["topic"]
    assert topic == "hermes/feedback/sound/toggleOff"
    assert calls[1].data["qos"] == 0
    assert not calls[1].data["retain"]


async def test_snips_config_no_feedback.opp, mqtt_mock):
    """Test Snips Config."""
    calls = async_mock_service.opp, "snips", "say")
    result = await async_setup_component.opp, "snips", {"snips": {}})
    assert result
    await opp.async_block_till_done()
    assert len(calls) == 0


async def test_snips_intent.opp, mqtt_mock):
    """Test intent via Snips."""
    result = await async_setup_component.opp, "snips", {"snips": {}})
    assert result
    payload = """
    {
        "siteId": "default",
        "sessionId": "1234567890ABCDEF",
        "input": "turn the lights green",
        "intent": {
            "intentName": "Lights",
            "confidenceScore": 1
        },
        "slots": [
            {
                "slotName": "light_color",
                "value": {
                    "kind": "Custom",
                    "value": "green"
                },
                "rawValue": "green"
            }
        ]
    }
    """

    intents = async_mock_intent.opp, "Lights")

    async_fire_mqtt_message.opp, "hermes/intent/Lights", payload)
    await opp.async_block_till_done()
    assert len(intents) == 1
    intent = intents[0]
    assert intent.platform == "snips"
    assert intent.intent_type == "Lights"
    assert intent
    assert intent.slots == {
        "light_color": {"value": "green"},
        "light_color_raw": {"value": "green"},
        "confidenceScore": {"value": 1},
        "site_id": {"value": "default"},
        "session_id": {"value": "1234567890ABCDEF"},
    }
    assert intent.text_input == "turn the lights green"


async def test_snips_service_intent.opp, mqtt_mock):
    """Test ServiceIntentHandler via Snips."""
   .opp.states.async_set("light.kitchen", "off")
    calls = async_mock_service.opp, "light", "turn_on")
    result = await async_setup_component.opp, "snips", {"snips": {}})
    assert result
    payload = """
    {
        "input": "turn the light on",
        "intent": {
            "intentName": "Lights",
            "confidenceScore": 0.85
        },
        "siteId": "default",
        "slots": [
            {
                "slotName": "name",
                "value": {
                    "kind": "Custom",
                    "value": "kitchen"
                },
                "rawValue": "green"
            }
        ]
    }
    """

    async_register(
        opp, ServiceIntentHandler("Lights", "light", "turn_on", "Turned {} on")
    )

    async_fire_mqtt_message.opp, "hermes/intent/Lights", payload)
    await opp.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].domain == "light"
    assert calls[0].service == "turn_on"
    assert calls[0].data["entity_id"] == "light.kitchen"
    assert "confidenceScore" not in calls[0].data
    assert "site_id" not in calls[0].data


async def test_snips_intent_with_duration.opp, mqtt_mock):
    """Test intent with Snips duration."""
    result = await async_setup_component.opp, "snips", {"snips": {}})
    assert result
    payload = """
    {
      "input": "set a timer of five minutes",
      "intent": {
        "intentName": "SetTimer",
        "confidenceScore": 1
      },
      "slots": [
        {
          "rawValue": "five minutes",
          "value": {
            "kind": "Duration",
            "years": 0,
            "quarters": 0,
            "months": 0,
            "weeks": 0,
            "days": 0,
            "hours": 0,
            "minutes": 5,
            "seconds": 0,
            "precision": "Exact"
          },
          "range": {
            "start": 15,
            "end": 27
          },
          "entity": "snips/duration",
          "slotName": "timer_duration"
        }
      ]
    }
    """
    intents = async_mock_intent.opp, "SetTimer")

    async_fire_mqtt_message.opp, "hermes/intent/SetTimer", payload)
    await opp.async_block_till_done()
    assert len(intents) == 1
    intent = intents[0]
    assert intent.platform == "snips"
    assert intent.intent_type == "SetTimer"
    assert intent.slots == {
        "confidenceScore": {"value": 1},
        "site_id": {"value": None},
        "session_id": {"value": None},
        "timer_duration": {"value": 300},
        "timer_duration_raw": {"value": "five minutes"},
    }


async def test_intent_speech_response.opp, mqtt_mock):
    """Test intent speech response via Snips."""
    calls = async_mock_service.opp, "mqtt", "publish", MQTT_PUBLISH_SCHEMA)
    result = await async_setup_component.opp, "snips", {"snips": {}})
    assert result
    result = await async_setup_component(
        opp,
        "intent_script",
        {
            "intent_script": {
                "spokenIntent": {
                    "speech": {"type": "plain", "text": "I am speaking to you"}
                }
            }
        },
    )
    assert result
    payload = """
    {
        "input": "speak to me",
        "sessionId": "abcdef0123456789",
        "intent": {
            "intentName": "spokenIntent",
            "confidenceScore": 1
        },
        "slots": []
    }
    """
    async_fire_mqtt_message.opp, "hermes/intent/spokenIntent", payload)
    await opp.async_block_till_done()

    assert len(calls) == 1
    payload = json.loads(calls[0].data["payload"])
    topic = calls[0].data["topic"]
    assert payload["sessionId"] == "abcdef0123456789"
    assert payload["text"] == "I am speaking to you"
    assert topic == "hermes/dialogueManager/endSession"


async def test_unknown_intent.opp, caplog, mqtt_mock):
    """Test unknown intent."""
    caplog.set_level(logging.WARNING)
    result = await async_setup_component.opp, "snips", {"snips": {}})
    assert result
    payload = """
    {
        "input": "I don't know what I am supposed to do",
        "sessionId": "abcdef1234567890",
        "intent": {
            "intentName": "unknownIntent",
            "confidenceScore": 1
        },
        "slots": []
    }
    """
    async_fire_mqtt_message.opp, "hermes/intent/unknownIntent", payload)
    await opp.async_block_till_done()
    assert "Received unknown intent unknownIntent" in caplog.text


async def test_snips_intent_user.opp, mqtt_mock):
    """Test intentName format user_XXX__intentName."""
    result = await async_setup_component.opp, "snips", {"snips": {}})
    assert result
    payload = """
    {
        "input": "what to do",
        "intent": {
            "intentName": "user_ABCDEF123__Lights",
            "confidenceScore": 1
        },
        "slots": []
    }
    """
    intents = async_mock_intent.opp, "Lights")
    async_fire_mqtt_message.opp, "hermes/intent/user_ABCDEF123__Lights", payload)
    await opp.async_block_till_done()

    assert len(intents) == 1
    intent = intents[0]
    assert intent.platform == "snips"
    assert intent.intent_type == "Lights"


async def test_snips_intent_username.opp, mqtt_mock):
    """Test intentName format username:intentName."""
    result = await async_setup_component.opp, "snips", {"snips": {}})
    assert result
    payload = """
    {
        "input": "what to do",
        "intent": {
            "intentName": "username:Lights",
            "confidenceScore": 1
        },
        "slots": []
    }
    """
    intents = async_mock_intent.opp, "Lights")
    async_fire_mqtt_message.opp, "hermes/intent/username:Lights", payload)
    await opp.async_block_till_done()

    assert len(intents) == 1
    intent = intents[0]
    assert intent.platform == "snips"
    assert intent.intent_type == "Lights"


async def test_snips_low_probability.opp, caplog, mqtt_mock):
    """Test intent via Snips."""
    caplog.set_level(logging.WARNING)
    result = await async_setup_component(
        opp, "snips", {"snips": {"probability_threshold": 0.5}}
    )
    assert result
    payload = """
    {
        "input": "I am not sure what to say",
        "intent": {
            "intentName": "LightsMaybe",
            "confidenceScore": 0.49
        },
        "slots": []
    }
    """

    async_mock_intent.opp, "LightsMaybe")
    async_fire_mqtt_message.opp, "hermes/intent/LightsMaybe", payload)
    await opp.async_block_till_done()
    assert "Intent below probaility threshold 0.49 < 0.5" in caplog.text


async def test_intent_special_slots.opp, mqtt_mock):
    """Test intent special slot values via Snips."""
    calls = async_mock_service.opp, "light", "turn_on")
    result = await async_setup_component.opp, "snips", {"snips": {}})
    assert result
    result = await async_setup_component(
        opp,
        "intent_script",
        {
            "intent_script": {
                "Lights": {
                    "action": {
                        "service": "light.turn_on",
                        "data_template": {
                            "confidenceScore": "{{ confidenceScore }}",
                            "site_id": "{{ site_id }}",
                        },
                    }
                }
            }
        },
    )
    assert result
    payload = """
    {
        "input": "turn the light on",
        "intent": {
            "intentName": "Lights",
            "confidenceScore": 0.85
        },
        "siteId": "default",
        "slots": []
    }
    """
    async_fire_mqtt_message.opp, "hermes/intent/Lights", payload)
    await opp.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].domain == "light"
    assert calls[0].service == "turn_on"
    assert calls[0].data["confidenceScore"] == 0.85
    assert calls[0].data["site_id"] == "default"


async def test_snips_say.opp):
    """Test snips say with invalid config."""
    calls = async_mock_service.opp, "snips", "say", snips.SERVICE_SCHEMA_SAY)
    data = {"text": "Hello"}
    await opp.services.async_call("snips", "say", data)
    await opp.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].domain == "snips"
    assert calls[0].service == "say"
    assert calls[0].data["text"] == "Hello"


async def test_snips_say_action.opp):
    """Test snips say_action with invalid config."""
    calls = async_mock_service(
        opp, "snips", "say_action", snips.SERVICE_SCHEMA_SAY_ACTION
    )

    data = {"text": "Hello", "intent_filter": ["myIntent"]}
    await opp.services.async_call("snips", "say_action", data)
    await opp.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].domain == "snips"
    assert calls[0].service == "say_action"
    assert calls[0].data["text"] == "Hello"
    assert calls[0].data["intent_filter"] == ["myIntent"]


async def test_snips_say_invalid_config(opp):
    """Test snips say with invalid config."""
    calls = async_mock_service.opp, "snips", "say", snips.SERVICE_SCHEMA_SAY)

    data = {"text": "Hello", "badKey": "boo"}
    with pytest.raises(vol.Invalid):
        await opp.services.async_call("snips", "say", data)
    await opp.async_block_till_done()

    assert len(calls) == 0


async def test_snips_say_action_invalid.opp):
    """Test snips say_action with invalid config."""
    calls = async_mock_service(
        opp, "snips", "say_action", snips.SERVICE_SCHEMA_SAY_ACTION
    )

    data = {"text": "Hello", "can_be_enqueued": "notabool"}

    with pytest.raises(vol.Invalid):
        await opp.services.async_call("snips", "say_action", data)
    await opp.async_block_till_done()

    assert len(calls) == 0


async def test_snips_feedback_on.opp):
    """Test snips say with invalid config."""
    calls = async_mock_service(
        opp, "snips", "feedback_on", snips.SERVICE_SCHEMA_FEEDBACK
    )

    data = {"site_id": "remote"}
    await opp.services.async_call("snips", "feedback_on", data)
    await opp.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].domain == "snips"
    assert calls[0].service == "feedback_on"
    assert calls[0].data["site_id"] == "remote"


async def test_snips_feedback_off.opp):
    """Test snips say with invalid config."""
    calls = async_mock_service(
        opp, "snips", "feedback_off", snips.SERVICE_SCHEMA_FEEDBACK
    )

    data = {"site_id": "remote"}
    await opp.services.async_call("snips", "feedback_off", data)
    await opp.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].domain == "snips"
    assert calls[0].service == "feedback_off"
    assert calls[0].data["site_id"] == "remote"


async def test_snips_feedback_config(opp):
    """Test snips say with invalid config."""
    calls = async_mock_service(
        opp, "snips", "feedback_on", snips.SERVICE_SCHEMA_FEEDBACK
    )

    data = {"site_id": "remote", "test": "test"}
    with pytest.raises(vol.Invalid):
        await opp.services.async_call("snips", "feedback_on", data)
    await opp.async_block_till_done()

    assert len(calls) == 0
