"""The tests for the Ring light platform."""
from openpeerpower.components.light import DOMAIN as LIGHT_DOMAIN
from openpeerpower.helpers import entity_registry as er

from .common import setup_platform

from tests.common import load_fixture


async def test_entity_registry(opp, requests_mock):
    """Tests that the devices are registered in the entity registry."""
    await setup_platform(opp, LIGHT_DOMAIN)
    entity_registry = er.async_get(opp)

    entry = entity_registry.async_get("light.front_light")
    assert entry.unique_id == 765432

    entry = entity_registry.async_get("light.internal_light")
    assert entry.unique_id == 345678


async def test_light_off_reports_correctly(opp, requests_mock):
    """Tests that the initial state of a device that should be off is correct."""
    await setup_platform(opp, LIGHT_DOMAIN)

    state = opp.states.get("light.front_light")
    assert state.state == "off"
    assert state.attributes.get("friendly_name") == "Front light"


async def test_light_on_reports_correctly(opp, requests_mock):
    """Tests that the initial state of a device that should be on is correct."""
    await setup_platform(opp, LIGHT_DOMAIN)

    state = opp.states.get("light.internal_light")
    assert state.state == "on"
    assert state.attributes.get("friendly_name") == "Internal light"


async def test_light_can_be_turned_on(opp, requests_mock):
    """Tests the light turns on correctly."""
    await setup_platform(opp, LIGHT_DOMAIN)

    # Mocks the response for turning a light on
    requests_mock.put(
        "https://api.ring.com/clients_api/doorbots/765432/floodlight_light_on",
        text=load_fixture("ring_doorbot_siren_on_response.json"),
    )

    state = opp.states.get("light.front_light")
    assert state.state == "off"

    await opp.services.async_call(
        "light", "turn_on", {"entity_id": "light.front_light"}, blocking=True
    )
    await opp.async_block_till_done()

    state = opp.states.get("light.front_light")
    assert state.state == "on"


async def test_updates_work(opp, requests_mock):
    """Tests the update service works correctly."""
    await setup_platform(opp, LIGHT_DOMAIN)
    state = opp.states.get("light.front_light")
    assert state.state == "off"
    # Changes the return to indicate that the light is now on.
    requests_mock.get(
        "https://api.ring.com/clients_api/ring_devices",
        text=load_fixture("ring_devices_updated.json"),
    )

    await opp.services.async_call("ring", "update", {}, blocking=True)

    await opp.async_block_till_done()

    state = opp.states.get("light.front_light")
    assert state.state == "on"
