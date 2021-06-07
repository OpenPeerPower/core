"""deCONZ fan platform tests."""

from unittest.mock import patch

import pytest

from openpeerpower.components.fan import (
    ATTR_PERCENTAGE,
    ATTR_SPEED,
    DOMAIN as FAN_DOMAIN,
    SERVICE_SET_PERCENTAGE,
    SERVICE_SET_SPEED,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    SPEED_HIGH,
    SPEED_LOW,
    SPEED_MEDIUM,
    SPEED_OFF,
)
from openpeerpower.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON, STATE_UNAVAILABLE

from .test_gateway import (
    DECONZ_WEB_REQUEST,
    mock_deconz_put_request,
    setup_deconz_integration,
)


async def test_no_fans(opp, aioclient_mock):
    """Test that no fan entities are created."""
    await setup_deconz_integration(opp, aioclient_mock)
    assert len(opp.states.async_all()) == 0


async def test_fans(opp, aioclient_mock, mock_deconz_websocket):
    """Test that all supported fan entities are created."""
    data = {
        "lights": {
            "1": {
                "etag": "432f3de28965052961a99e3c5494daf4",
                "hascolor": False,
                "manufacturername": "King Of Fans,  Inc.",
                "modelid": "HDC52EastwindFan",
                "name": "Ceiling fan",
                "state": {
                    "alert": "none",
                    "bri": 254,
                    "on": False,
                    "reachable": True,
                    "speed": 4,
                },
                "swversion": "0000000F",
                "type": "Fan",
                "uniqueid": "00:22:a3:00:00:27:8b:81-01",
            }
        }
    }

    with patch.dict(DECONZ_WEB_REQUEST, data):
        config_entry = await setup_deconz_integration(opp, aioclient_mock)

    assert len(opp.states.async_all()) == 2  # Light and fan
    assert opp.states.get("fan.ceiling_fan").state == STATE_ON
    assert opp.states.get("fan.ceiling_fan").attributes[ATTR_PERCENTAGE] == 100

    # Test states

    event_changed_light = {
        "t": "event",
        "e": "changed",
        "r": "lights",
        "id": "1",
        "state": {"speed": 1},
    }
    await mock_deconz_websocket(data=event_changed_light)
    await opp.async_block_till_done()

    assert opp.states.get("fan.ceiling_fan").state == STATE_ON
    assert opp.states.get("fan.ceiling_fan").attributes[ATTR_PERCENTAGE] == 25

    event_changed_light = {
        "t": "event",
        "e": "changed",
        "r": "lights",
        "id": "1",
        "state": {"speed": 2},
    }
    await mock_deconz_websocket(data=event_changed_light)
    await opp.async_block_till_done()

    assert opp.states.get("fan.ceiling_fan").state == STATE_ON
    assert opp.states.get("fan.ceiling_fan").attributes[ATTR_PERCENTAGE] == 50

    event_changed_light = {
        "t": "event",
        "e": "changed",
        "r": "lights",
        "id": "1",
        "state": {"speed": 3},
    }
    await mock_deconz_websocket(data=event_changed_light)
    await opp.async_block_till_done()

    assert opp.states.get("fan.ceiling_fan").state == STATE_ON
    assert opp.states.get("fan.ceiling_fan").attributes[ATTR_PERCENTAGE] == 75

    event_changed_light = {
        "t": "event",
        "e": "changed",
        "r": "lights",
        "id": "1",
        "state": {"speed": 4},
    }
    await mock_deconz_websocket(data=event_changed_light)
    await opp.async_block_till_done()

    assert opp.states.get("fan.ceiling_fan").state == STATE_ON
    assert opp.states.get("fan.ceiling_fan").attributes[ATTR_PERCENTAGE] == 100

    event_changed_light = {
        "t": "event",
        "e": "changed",
        "r": "lights",
        "id": "1",
        "state": {"speed": 0},
    }
    await mock_deconz_websocket(data=event_changed_light)
    await opp.async_block_till_done()

    assert opp.states.get("fan.ceiling_fan").state == STATE_OFF
    assert opp.states.get("fan.ceiling_fan").attributes[ATTR_PERCENTAGE] == 0

    # Test service calls

    mock_deconz_put_request(aioclient_mock, config_entry.data, "/lights/1/state")

    # Service turn on fan using saved default_on_speed

    await opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "fan.ceiling_fan"},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[1][2] == {"speed": 4}

    # Service turn off fan

    await opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "fan.ceiling_fan"},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[2][2] == {"speed": 0}

    # Service turn on fan to 20%

    await opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "fan.ceiling_fan", ATTR_PERCENTAGE: 20},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[3][2] == {"speed": 1}

    # Service set fan percentage to 20%

    await opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: "fan.ceiling_fan", ATTR_PERCENTAGE: 20},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[4][2] == {"speed": 1}

    # Service set fan percentage to 40%

    await opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: "fan.ceiling_fan", ATTR_PERCENTAGE: 40},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[5][2] == {"speed": 2}

    # Service set fan percentage to 60%

    await opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: "fan.ceiling_fan", ATTR_PERCENTAGE: 60},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[6][2] == {"speed": 3}

    # Service set fan percentage to 80%

    await opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: "fan.ceiling_fan", ATTR_PERCENTAGE: 80},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[7][2] == {"speed": 4}

    # Service set fan percentage to 0% does not equal off

    await opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: "fan.ceiling_fan", ATTR_PERCENTAGE: 0},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[8][2] == {"speed": 1}

    # Events with an unsupported speed does not get converted

    event_changed_light = {
        "t": "event",
        "e": "changed",
        "r": "lights",
        "id": "1",
        "state": {"speed": 5},
    }
    await mock_deconz_websocket(data=event_changed_light)
    await opp.async_block_till_done()

    assert opp.states.get("fan.ceiling_fan").state == STATE_ON
    assert not opp.states.get("fan.ceiling_fan").attributes[ATTR_PERCENTAGE]

    await opp.config_entries.async_unload(config_entry.entry_id)

    states = opp.states.async_all()
    assert len(states) == 2
    for state in states:
        assert state.state == STATE_UNAVAILABLE

    await opp.config_entries.async_remove(config_entry.entry_id)
    await opp.async_block_till_done()
    assert len(opp.states.async_all()) == 0


async def test_fans_legacy_speed_modes(opp, aioclient_mock, mock_deconz_websocket):
    """Test that all supported fan entities are created.

    Legacy fan support.
    """
    data = {
        "lights": {
            "1": {
                "etag": "432f3de28965052961a99e3c5494daf4",
                "hascolor": False,
                "manufacturername": "King Of Fans,  Inc.",
                "modelid": "HDC52EastwindFan",
                "name": "Ceiling fan",
                "state": {
                    "alert": "none",
                    "bri": 254,
                    "on": False,
                    "reachable": True,
                    "speed": 4,
                },
                "swversion": "0000000F",
                "type": "Fan",
                "uniqueid": "00:22:a3:00:00:27:8b:81-01",
            }
        }
    }

    with patch.dict(DECONZ_WEB_REQUEST, data):
        config_entry = await setup_deconz_integration(opp, aioclient_mock)

    assert len(opp.states.async_all()) == 2  # Light and fan
    assert opp.states.get("fan.ceiling_fan").state == STATE_ON
    assert opp.states.get("fan.ceiling_fan").attributes[ATTR_SPEED] == SPEED_HIGH

    # Test states

    event_changed_light = {
        "t": "event",
        "e": "changed",
        "r": "lights",
        "id": "1",
        "state": {"speed": 1},
    }
    await mock_deconz_websocket(data=event_changed_light)
    await opp.async_block_till_done()

    assert opp.states.get("fan.ceiling_fan").state == STATE_ON
    assert opp.states.get("fan.ceiling_fan").attributes[ATTR_PERCENTAGE] == 25
    assert opp.states.get("fan.ceiling_fan").attributes[ATTR_SPEED] == SPEED_LOW

    event_changed_light = {
        "t": "event",
        "e": "changed",
        "r": "lights",
        "id": "1",
        "state": {"speed": 2},
    }
    await mock_deconz_websocket(data=event_changed_light)
    await opp.async_block_till_done()

    assert opp.states.get("fan.ceiling_fan").state == STATE_ON
    assert opp.states.get("fan.ceiling_fan").attributes[ATTR_PERCENTAGE] == 50
    assert opp.states.get("fan.ceiling_fan").attributes[ATTR_SPEED] == SPEED_MEDIUM

    event_changed_light = {
        "t": "event",
        "e": "changed",
        "r": "lights",
        "id": "1",
        "state": {"speed": 3},
    }
    await mock_deconz_websocket(data=event_changed_light)
    await opp.async_block_till_done()

    assert opp.states.get("fan.ceiling_fan").state == STATE_ON
    assert opp.states.get("fan.ceiling_fan").attributes[ATTR_PERCENTAGE] == 75
    assert opp.states.get("fan.ceiling_fan").attributes[ATTR_SPEED] == SPEED_MEDIUM

    event_changed_light = {
        "t": "event",
        "e": "changed",
        "r": "lights",
        "id": "1",
        "state": {"speed": 4},
    }
    await mock_deconz_websocket(data=event_changed_light)
    await opp.async_block_till_done()

    assert opp.states.get("fan.ceiling_fan").state == STATE_ON
    assert opp.states.get("fan.ceiling_fan").attributes[ATTR_PERCENTAGE] == 100
    assert opp.states.get("fan.ceiling_fan").attributes[ATTR_SPEED] == SPEED_HIGH

    event_changed_light = {
        "t": "event",
        "e": "changed",
        "r": "lights",
        "id": "1",
        "state": {"speed": 0},
    }
    await mock_deconz_websocket(data=event_changed_light)
    await opp.async_block_till_done()

    assert opp.states.get("fan.ceiling_fan").state == STATE_OFF
    assert opp.states.get("fan.ceiling_fan").attributes[ATTR_PERCENTAGE] == 0
    assert opp.states.get("fan.ceiling_fan").attributes[ATTR_SPEED] == SPEED_OFF

    # Test service calls

    mock_deconz_put_request(aioclient_mock, config_entry.data, "/lights/1/state")

    # Service turn on fan using saved default_on_speed

    await opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "fan.ceiling_fan"},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[1][2] == {"speed": 4}

    # Service turn on fan with speed_off
    # async_turn_on_compat use speed_to_percentage which will return 0

    await opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "fan.ceiling_fan", ATTR_SPEED: SPEED_OFF},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[2][2] == {"speed": 1}

    # Service turn on fan with bad speed
    # async_turn_on_compat use speed_to_percentage which will convert to SPEED_MEDIUM -> 2

    await opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "fan.ceiling_fan", ATTR_SPEED: "bad"},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[3][2] == {"speed": 2}

    # Service turn on fan to low speed

    await opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "fan.ceiling_fan", ATTR_SPEED: SPEED_LOW},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[4][2] == {"speed": 1}

    # Service turn on fan to medium speed

    await opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "fan.ceiling_fan", ATTR_SPEED: SPEED_MEDIUM},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[5][2] == {"speed": 2}

    # Service turn on fan to high speed

    await opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "fan.ceiling_fan", ATTR_SPEED: SPEED_HIGH},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[6][2] == {"speed": 4}

    # Service set fan speed to low

    await opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_SPEED,
        {ATTR_ENTITY_ID: "fan.ceiling_fan", ATTR_SPEED: SPEED_LOW},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[7][2] == {"speed": 1}

    # Service set fan speed to medium

    await opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_SPEED,
        {ATTR_ENTITY_ID: "fan.ceiling_fan", ATTR_SPEED: SPEED_MEDIUM},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[8][2] == {"speed": 2}

    # Service set fan speed to high

    await opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_SPEED,
        {ATTR_ENTITY_ID: "fan.ceiling_fan", ATTR_SPEED: SPEED_HIGH},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[9][2] == {"speed": 4}

    # Service set fan speed to off

    await opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_SPEED,
        {ATTR_ENTITY_ID: "fan.ceiling_fan", ATTR_SPEED: SPEED_OFF},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[10][2] == {"speed": 0}

    # Service set fan speed to unsupported value

    with pytest.raises(ValueError):
        await opp.services.async_call(
            FAN_DOMAIN,
            SERVICE_SET_SPEED,
            {ATTR_ENTITY_ID: "fan.ceiling_fan", ATTR_SPEED: "bad value"},
            blocking=True,
        )

    # Events with an unsupported speed gets converted to default speed "medium"

    event_changed_light = {
        "t": "event",
        "e": "changed",
        "r": "lights",
        "id": "1",
        "state": {"speed": 3},
    }
    await mock_deconz_websocket(data=event_changed_light)
    await opp.async_block_till_done()

    assert opp.states.get("fan.ceiling_fan").state == STATE_ON
    assert opp.states.get("fan.ceiling_fan").attributes[ATTR_SPEED] == SPEED_MEDIUM

    await opp.config_entries.async_unload(config_entry.entry_id)

    states = opp.states.async_all()
    assert len(states) == 2
    for state in states:
        assert state.state == STATE_UNAVAILABLE

    await opp.config_entries.async_remove(config_entry.entry_id)
    await opp.async_block_till_done()
    assert len(opp.states.async_all()) == 0
