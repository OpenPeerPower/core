"""Test Alexa entity representation."""
from unittest.mock import patch

from openpeerpower.components.alexa import smart_home
from openpeerpower.const import __version__

from . import DEFAULT_CONFIG, get_new_request


async def test_unsupported_domain.opp):
    """Discovery ignores entities of unknown domains."""
    request = get_new_request("Alexa.Discovery", "Discover")

   .opp.states.async_set("woz.boop", "on", {"friendly_name": "Boop Woz"})

    msg = await smart_home.async_handle_message.opp, DEFAULT_CONFIG, request)

    assert "event" in msg
    msg = msg["event"]

    assert not msg["payload"]["endpoints"]


async def test_serialize_discovery.opp):
    """Test we handle an interface raising unexpectedly during serialize discovery."""
    request = get_new_request("Alexa.Discovery", "Discover")

   .opp.states.async_set("switch.bla", "on", {"friendly_name": "Boop Woz"})

    msg = await smart_home.async_handle_message.opp, DEFAULT_CONFIG, request)

    assert "event" in msg
    msg = msg["event"]
    endpoint = msg["payload"]["endpoints"][0]

    assert endpoint["additionalAttributes"] == {
        "manufacturer": "Open Peer Power",
        "model": "switch",
        "softwareVersion": __version__,
        "customIdentifier": "mock-user-id-switch.bla",
    }


async def test_serialize_discovery_recovers.opp, caplog):
    """Test we handle an interface raising unexpectedly during serialize discovery."""
    request = get_new_request("Alexa.Discovery", "Discover")

   .opp.states.async_set("switch.bla", "on", {"friendly_name": "Boop Woz"})

    with patch(
        "openpeerpower.components.alexa.capabilities.AlexaPowerController.serialize_discovery",
        side_effect=TypeError,
    ):
        msg = await smart_home.async_handle_message.opp, DEFAULT_CONFIG, request)

    assert "event" in msg
    msg = msg["event"]

    interfaces = {
        ifc["interface"] for ifc in msg["payload"]["endpoints"][0]["capabilities"]
    }

    assert "Alexa.PowerController" not in interfaces
    assert (
        f"Error serializing Alexa.PowerController discovery for .opp.states.get('switch.bla')}"
        in caplog.text
    )
