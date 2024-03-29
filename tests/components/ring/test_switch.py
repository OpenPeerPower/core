"""The tests for the Ring switch platform."""
from openpeerpower.components.switch import DOMAIN as SWITCH_DOMAIN
from openpeerpower.helpers import entity_registry as er

from .common import setup_platform

from tests.common import load_fixture


async def test_entity_registry(opp, requests_mock):
    """Tests that the devices are registered in the entity registry."""
    await setup_platform(opp, SWITCH_DOMAIN)
    entity_registry = er.async_get(opp)

    entry = entity_registry.async_get("switch.front_siren")
    assert entry.unique_id == "765432-siren"

    entry = entity_registry.async_get("switch.internal_siren")
    assert entry.unique_id == "345678-siren"


async def test_siren_off_reports_correctly(opp, requests_mock):
    """Tests that the initial state of a device that should be off is correct."""
    await setup_platform(opp, SWITCH_DOMAIN)

    state = opp.states.get("switch.front_siren")
    assert state.state == "off"
    assert state.attributes.get("friendly_name") == "Front siren"


async def test_siren_on_reports_correctly(opp, requests_mock):
    """Tests that the initial state of a device that should be on is correct."""
    await setup_platform(opp, SWITCH_DOMAIN)

    state = opp.states.get("switch.internal_siren")
    assert state.state == "on"
    assert state.attributes.get("friendly_name") == "Internal siren"
    assert state.attributes.get("icon") == "mdi:alarm-bell"


async def test_siren_can_be_turned_on(opp, requests_mock):
    """Tests the siren turns on correctly."""
    await setup_platform(opp, SWITCH_DOMAIN)

    # Mocks the response for turning a siren on
    requests_mock.put(
        "https://api.ring.com/clients_api/doorbots/765432/siren_on",
        text=load_fixture("ring_doorbot_siren_on_response.json"),
    )

    state = opp.states.get("switch.front_siren")
    assert state.state == "off"

    await opp.services.async_call(
        "switch", "turn_on", {"entity_id": "switch.front_siren"}, blocking=True
    )

    await opp.async_block_till_done()
    state = opp.states.get("switch.front_siren")
    assert state.state == "on"


async def test_updates_work(opp, requests_mock):
    """Tests the update service works correctly."""
    await setup_platform(opp, SWITCH_DOMAIN)
    state = opp.states.get("switch.front_siren")
    assert state.state == "off"
    # Changes the return to indicate that the siren is now on.
    requests_mock.get(
        "https://api.ring.com/clients_api/ring_devices",
        text=load_fixture("ring_devices_updated.json"),
    )

    await opp.services.async_call("ring", "update", {}, blocking=True)

    await opp.async_block_till_done()

    state = opp.states.get("switch.front_siren")
    assert state.state == "on"
