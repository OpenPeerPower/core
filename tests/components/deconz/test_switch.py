"""deCONZ switch platform tests."""

from copy import deepcopy

from openpeerpower.components.deconz.gateway import get_gateway_from_config_entry
from openpeerpower.components.switch import (
    DOMAIN as SWITCH_DOMAIN,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from openpeerpower.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON, STATE_UNAVAILABLE

from .test_gateway import (
    DECONZ_WEB_REQUEST,
    mock_deconz_put_request,
    setup_deconz_integration,
)

POWER_PLUGS = {
    "1": {
        "id": "On off switch id",
        "name": "On off switch",
        "type": "On/Off plug-in unit",
        "state": {"on": True, "reachable": True},
        "uniqueid": "00:00:00:00:00:00:00:00-00",
    },
    "2": {
        "id": "Smart plug id",
        "name": "Smart plug",
        "type": "Smart plug",
        "state": {"on": False, "reachable": True},
        "uniqueid": "00:00:00:00:00:00:00:01-00",
    },
    "3": {
        "id": "Unsupported switch id",
        "name": "Unsupported switch",
        "type": "Not a switch",
        "state": {"reachable": True},
        "uniqueid": "00:00:00:00:00:00:00:03-00",
    },
    "4": {
        "id": "On off relay id",
        "name": "On off relay",
        "state": {"on": True, "reachable": True},
        "type": "On/Off light",
        "uniqueid": "00:00:00:00:00:00:00:04-00",
    },
}

SIRENS = {
    "1": {
        "id": "Warning device id",
        "name": "Warning device",
        "type": "Warning device",
        "state": {"alert": "lselect", "reachable": True},
        "uniqueid": "00:00:00:00:00:00:00:00-00",
    },
    "2": {
        "id": "Unsupported switch id",
        "name": "Unsupported switch",
        "type": "Not a switch",
        "state": {"reachable": True},
        "uniqueid": "00:00:00:00:00:00:00:01-00",
    },
}


async def test_no_switches.opp, aioclient_mock):
    """Test that no switch entities are created."""
    await setup_deconz_integration.opp, aioclient_mock)
    assert len.opp.states.async_all()) == 0


async def test_power_plugs.opp, aioclient_mock):
    """Test that all supported switch entities are created."""
    data = deepcopy(DECONZ_WEB_REQUEST)
    data["lights"] = deepcopy(POWER_PLUGS)
    config_entry = await setup_deconz_integration(
       .opp, aioclient_mock, get_state_response=data
    )
    gateway = get_gateway_from_config_entry.opp, config_entry)

    assert len.opp.states.async_all()) == 4
    assert.opp.states.get("switch.on_off_switch").state == STATE_ON
    assert.opp.states.get("switch.smart_plug").state == STATE_OFF
    assert.opp.states.get("switch.on_off_relay").state == STATE_ON
    assert.opp.states.get("switch.unsupported_switch") is None

    state_changed_event = {
        "t": "event",
        "e": "changed",
        "r": "lights",
        "id": "1",
        "state": {"on": False},
    }
    gateway.api.event_handler(state_changed_event)

    assert.opp.states.get("switch.on_off_switch").state == STATE_OFF

    # Verify service calls

    mock_deconz_put_request(aioclient_mock, config_entry.data, "/lights/1/state")

    # Service turn on power plug

    await.opp.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.on_off_switch"},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[1][2] == {"on": True}

    # Service turn off power plug

    await.opp.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.on_off_switch"},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[2][2] == {"on": False}

    await.opp.config_entries.async_unload(config_entry.entry_id)

    states = opp.states.async_all()
    assert len.opp.states.async_all()) == 4
    for state in states:
        assert state.state == STATE_UNAVAILABLE

    await.opp.config_entries.async_remove(config_entry.entry_id)
    await.opp.async_block_till_done()
    assert len.opp.states.async_all()) == 0


async def test_sirens.opp, aioclient_mock):
    """Test that siren entities are created."""
    data = deepcopy(DECONZ_WEB_REQUEST)
    data["lights"] = deepcopy(SIRENS)
    config_entry = await setup_deconz_integration(
       .opp, aioclient_mock, get_state_response=data
    )
    gateway = get_gateway_from_config_entry.opp, config_entry)

    assert len.opp.states.async_all()) == 2
    assert.opp.states.get("switch.warning_device").state == STATE_ON
    assert.opp.states.get("switch.unsupported_switch") is None

    state_changed_event = {
        "t": "event",
        "e": "changed",
        "r": "lights",
        "id": "1",
        "state": {"alert": None},
    }
    gateway.api.event_handler(state_changed_event)

    assert.opp.states.get("switch.warning_device").state == STATE_OFF

    # Verify service calls

    mock_deconz_put_request(aioclient_mock, config_entry.data, "/lights/1/state")

    # Service turn on siren

    await.opp.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.warning_device"},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[1][2] == {"alert": "lselect"}

    # Service turn off siren

    await.opp.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.warning_device"},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[2][2] == {"alert": "none"}

    await.opp.config_entries.async_unload(config_entry.entry_id)

    states = opp.states.async_all()
    assert len.opp.states.async_all()) == 2
    for state in states:
        assert state.state == STATE_UNAVAILABLE

    await.opp.config_entries.async_remove(config_entry.entry_id)
    await.opp.async_block_till_done()
    assert len.opp.states.async_all()) == 0
