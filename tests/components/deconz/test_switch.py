"""deCONZ switch platform tests."""

from unittest.mock import patch

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


async def test_no_switches(opp, aioclient_mock):
    """Test that no switch entities are created."""
    await setup_deconz_integration(opp, aioclient_mock)
    assert len(opp.states.async_all()) == 0


async def test_power_plugs(opp, aioclient_mock, mock_deconz_websocket):
    """Test that all supported switch entities are created."""
    data = {
        "lights": {
            "1": {
                "name": "On off switch",
                "type": "On/Off plug-in unit",
                "state": {"on": True, "reachable": True},
                "uniqueid": "00:00:00:00:00:00:00:00-00",
            },
            "2": {
                "name": "Smart plug",
                "type": "Smart plug",
                "state": {"on": False, "reachable": True},
                "uniqueid": "00:00:00:00:00:00:00:01-00",
            },
            "3": {
                "name": "Unsupported switch",
                "type": "Not a switch",
                "state": {"reachable": True},
                "uniqueid": "00:00:00:00:00:00:00:03-00",
            },
            "4": {
                "name": "On off relay",
                "state": {"on": True, "reachable": True},
                "type": "On/Off light",
                "uniqueid": "00:00:00:00:00:00:00:04-00",
            },
        }
    }
    with patch.dict(DECONZ_WEB_REQUEST, data):
        config_entry = await setup_deconz_integration(opp, aioclient_mock)

    assert len(opp.states.async_all()) == 4
    assert opp.states.get("switch.on_off_switch").state == STATE_ON
    assert opp.states.get("switch.smart_plug").state == STATE_OFF
    assert opp.states.get("switch.on_off_relay").state == STATE_ON
    assert opp.states.get("switch.unsupported_switch") is None

    event_changed_light = {
        "t": "event",
        "e": "changed",
        "r": "lights",
        "id": "1",
        "state": {"on": False},
    }
    await mock_deconz_websocket(data=event_changed_light)
    await opp.async_block_till_done()

    assert opp.states.get("switch.on_off_switch").state == STATE_OFF

    # Verify service calls

    mock_deconz_put_request(aioclient_mock, config_entry.data, "/lights/1/state")

    # Service turn on power plug

    await opp.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.on_off_switch"},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[1][2] == {"on": True}

    # Service turn off power plug

    await opp.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.on_off_switch"},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[2][2] == {"on": False}

    await opp.config_entries.async_unload(config_entry.entry_id)

    states = opp.states.async_all()
    assert len(states) == 4
    for state in states:
        assert state.state == STATE_UNAVAILABLE

    await opp.config_entries.async_remove(config_entry.entry_id)
    await opp.async_block_till_done()
    assert len(opp.states.async_all()) == 0


async def test_sirens(opp, aioclient_mock, mock_deconz_websocket):
    """Test that siren entities are created."""
    data = {
        "lights": {
            "1": {
                "name": "Warning device",
                "type": "Warning device",
                "state": {"alert": "lselect", "reachable": True},
                "uniqueid": "00:00:00:00:00:00:00:00-00",
            },
            "2": {
                "name": "Unsupported switch",
                "type": "Not a switch",
                "state": {"reachable": True},
                "uniqueid": "00:00:00:00:00:00:00:01-00",
            },
        }
    }
    with patch.dict(DECONZ_WEB_REQUEST, data):
        config_entry = await setup_deconz_integration(opp, aioclient_mock)

    assert len(opp.states.async_all()) == 2
    assert opp.states.get("switch.warning_device").state == STATE_ON
    assert not opp.states.get("switch.unsupported_switch")

    event_changed_light = {
        "t": "event",
        "e": "changed",
        "r": "lights",
        "id": "1",
        "state": {"alert": None},
    }
    await mock_deconz_websocket(data=event_changed_light)
    await opp.async_block_till_done()

    assert opp.states.get("switch.warning_device").state == STATE_OFF

    # Verify service calls

    mock_deconz_put_request(aioclient_mock, config_entry.data, "/lights/1/state")

    # Service turn on siren

    await opp.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.warning_device"},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[1][2] == {"alert": "lselect"}

    # Service turn off siren

    await opp.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.warning_device"},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[2][2] == {"alert": "none"}

    await opp.config_entries.async_unload(config_entry.entry_id)

    states = opp.states.async_all()
    assert len(states) == 2
    for state in states:
        assert state.state == STATE_UNAVAILABLE

    await opp.config_entries.async_remove(config_entry.entry_id)
    await opp.async_block_till_done()
    assert len(opp.states.async_all()) == 0
