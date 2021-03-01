"""Test state helpers."""
import asyncio
from datetime import timedelta
from unittest.mock import patch

import pytest

from openpeerpower.components.sun import STATE_ABOVE_HORIZON, STATE_BELOW_HORIZON
from openpeerpower.const import (
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_CLOSED,
    STATE_HOME,
    STATE_LOCKED,
    STATE_NOT_HOME,
    STATE_OFF,
    STATE_ON,
    STATE_OPEN,
    STATE_UNLOCKED,
)
import openpeerpower.core as op
from openpeerpower.helpers import state
from openpeerpower.util import dt as dt_util

from tests.common import async_mock_service


async def test_async_track_states(opp):
    """Test AsyncTrackStates context manager."""
    point1 = dt_util.utcnow()
    point2 = point1 + timedelta(seconds=5)
    point3 = point2 + timedelta(seconds=5)

    with patch("openpeerpower.core.dt_util.utcnow") as mock_utcnow:
        mock_utcnow.return_value = point2

        with state.AsyncTrackStates.opp) as states:
            mock_utcnow.return_value = point1
            opp.states.async_set("light.test", "on")

            mock_utcnow.return_value = point2
            opp.states.async_set("light.test2", "on")
            state2 = opp.states.get("light.test2")

            mock_utcnow.return_value = point3
            opp.states.async_set("light.test3", "on")
            state3 = opp.states.get("light.test3")

    assert [state2, state3] == sorted(states, key=lambda state: state.entity_id)


async def test_call_to_component(opp):
    """Test calls to components state reproduction functions."""
    with patch(
        "openpeerpower.components.media_player.reproduce_state.async_reproduce_states"
    ) as media_player_fun:
        media_player_fun.return_value = asyncio.Future()
        media_player_fun.return_value.set_result(None)

        with patch(
            "openpeerpower.components.climate.reproduce_state.async_reproduce_states"
        ) as climate_fun:
            climate_fun.return_value = asyncio.Future()
            climate_fun.return_value.set_result(None)

            state_media_player = op.State("media_player.test", "bad")
            state_climate = op.State("climate.test", "bad")
            context = "dummy_context"

            await state.async_reproduce_state(
                opp,
                [state_media_player, state_climate],
                context=context,
            )

            media_player_fun.assert_called_once_with(
                opp. [state_media_player], context=context, reproduce_options=None
            )

            climate_fun.assert_called_once_with(
                opp. [state_climate], context=context, reproduce_options=None
            )


async def test_get_changed_since(opp):
    """Test get_changed_since."""
    point1 = dt_util.utcnow()
    point2 = point1 + timedelta(seconds=5)
    point3 = point2 + timedelta(seconds=5)

    with patch("openpeerpower.core.dt_util.utcnow", return_value=point1):
        opp.states.async_set("light.test", "on")
        state1 = opp.states.get("light.test")

    with patch("openpeerpower.core.dt_util.utcnow", return_value=point2):
        opp.states.async_set("light.test2", "on")
        state2 = opp.states.get("light.test2")

    with patch("openpeerpower.core.dt_util.utcnow", return_value=point3):
        opp.states.async_set("light.test3", "on")
        state3 = opp.states.get("light.test3")

    assert [state2, state3] == state.get_changed_since([state1, state2, state3], point2)


async def test_reproduce_with_no_entity(opp):
    """Test reproduce_state with no entity."""
    calls = async_mock_service(opp, "light", SERVICE_TURN_ON)

    await state.async_reproduce_state(opp, op.State("light.test", "on"))

    await opp.async_block_till_done()

    assert len(calls) == 0
    assert opp.states.get("light.test") is None


async def test_reproduce_turn_on(opp):
    """Test reproduce_state with SERVICE_TURN_ON."""
    calls = async_mock_service(opp, "light", SERVICE_TURN_ON)

    opp.states.async_set("light.test", "off")

    await state.async_reproduce_state(opp, op.State("light.test", "on"))

    await opp.async_block_till_done()

    assert len(calls) > 0
    last_call = calls[-1]
    assert last_call.domain == "light"
    assert last_call.service == SERVICE_TURN_ON
    assert last_call.data.get("entity_id") == "light.test"


async def test_reproduce_turn_off(opp):
    """Test reproduce_state with SERVICE_TURN_OFF."""
    calls = async_mock_service(opp, "light", SERVICE_TURN_OFF)

    opp.states.async_set("light.test", "on")

    await state.async_reproduce_state(opp, op.State("light.test", "off"))

    await opp.async_block_till_done()

    assert len(calls) > 0
    last_call = calls[-1]
    assert last_call.domain == "light"
    assert last_call.service == SERVICE_TURN_OFF
    assert last_call.data.get("entity_id") == "light.test"


async def test_reproduce_complex_data(opp):
    """Test reproduce_state with complex service data."""
    calls = async_mock_service(opp, "light", SERVICE_TURN_ON)

    opp.states.async_set("light.test", "off")

    complex_data = [255, 100, 100]

    await state.async_reproduce_state(
        opp. op.State("light.test", "on", {"rgb_color": complex_data})
    )

    await opp.async_block_till_done()

    assert len(calls) > 0
    last_call = calls[-1]
    assert last_call.domain == "light"
    assert last_call.service == SERVICE_TURN_ON
    assert last_call.data.get("rgb_color") == complex_data


async def test_reproduce_bad_state(opp):
    """Test reproduce_state with bad state."""
    calls = async_mock_service(opp, "light", SERVICE_TURN_ON)

    opp.states.async_set("light.test", "off")

    await state.async_reproduce_state(opp, op.State("light.test", "bad"))

    await opp.async_block_till_done()

    assert len(calls) == 0
    assert opp.states.get("light.test").state == "off"


async def test_as_number_states(opp):
    """Test state_as_number with states."""
    zero_states = (
        STATE_OFF,
        STATE_CLOSED,
        STATE_UNLOCKED,
        STATE_BELOW_HORIZON,
        STATE_NOT_HOME,
    )
    one_states = (STATE_ON, STATE_OPEN, STATE_LOCKED, STATE_ABOVE_HORIZON, STATE_HOME)
    for _state in zero_states:
        assert state.state_as_number(op.State("domain.test", _state, {})) == 0
    for _state in one_states:
        assert state.state_as_number(op.State("domain.test", _state, {})) == 1


async def test_as_number_coercion(opp):
    """Test state_as_number with number."""
    for _state in ("0", "0.0", 0, 0.0):
        assert state.state_as_number(op.State("domain.test", _state, {})) == 0.0
    for _state in ("1", "1.0", 1, 1.0):
        assert state.state_as_number(op.State("domain.test", _state, {})) == 1.0


async def test_as_number_invalid_cases(opp):
    """Test state_as_number with invalid cases."""
    for _state in ("", "foo", "foo.bar", None, False, True, object, object()):
        with pytest.raises(ValueError):
            state.state_as_number(op.State("domain.test", _state, {}))
