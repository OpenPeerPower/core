"""Test reproduce state for Alert."""
from openpeerpower.core import State

from tests.common import async_mock_service


async def test_reproducing_states.opp, caplog):
    """Test reproducing Alert states."""
   .opp.states.async_set("alert.entity_off", "off", {})
   .opp.states.async_set("alert.entity_on", "on", {})

    turn_on_calls = async_mock_service.opp, "alert", "turn_on")
    turn_off_calls = async_mock_service.opp, "alert", "turn_off")

    # These calls should do nothing as entities already in desired state
    await.opp.helpers.state.async_reproduce_state(
        [State("alert.entity_off", "off"), State("alert.entity_on", "on")]
    )

    assert len(turn_on_calls) == 0
    assert len(turn_off_calls) == 0

    # Test invalid state is handled
    await.opp.helpers.state.async_reproduce_state(
        [State("alert.entity_off", "not_supported")]
    )

    assert "not_supported" in caplog.text
    assert len(turn_on_calls) == 0
    assert len(turn_off_calls) == 0

    # Make sure correct services are called
    await.opp.helpers.state.async_reproduce_state(
        [
            State("alert.entity_on", "off"),
            State("alert.entity_off", "on"),
            # Should not raise
            State("alert.non_existing", "on"),
        ]
    )

    assert len(turn_on_calls) == 1
    assert turn_on_calls[0].domain == "alert"
    assert turn_on_calls[0].data == {
        "entity_id": "alert.entity_off",
    }

    assert len(turn_off_calls) == 1
    assert turn_off_calls[0].domain == "alert"
    assert turn_off_calls[0].data == {"entity_id": "alert.entity_on"}
