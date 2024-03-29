"""Test reproduce state for NEW_NAME."""
import pytest

from openpeerpower.core import OpenPeerPower, State

from tests.common import async_mock_service


async def test_reproducing_states(
    opp: OpenPeerPower, caplog: pytest.LogCaptureFixture
) -> None:
    """Test reproducing NEW_NAME states."""
    opp.states.async_set("NEW_DOMAIN.entity_off", "off", {})
    opp.states.async_set("NEW_DOMAIN.entity_on", "on", {"color": "red"})

    turn_on_calls = async_mock_service(opp, "NEW_DOMAIN", "turn_on")
    turn_off_calls = async_mock_service(opp, "NEW_DOMAIN", "turn_off")

    # These calls should do nothing as entities already in desired state
    await opp.helpers.state.async_reproduce_state(
        [
            State("NEW_DOMAIN.entity_off", "off"),
            State("NEW_DOMAIN.entity_on", "on", {"color": "red"}),
        ],
        blocking=True,
    )

    assert len(turn_on_calls) == 0
    assert len(turn_off_calls) == 0

    # Test invalid state is handled
    await opp.helpers.state.async_reproduce_state(
        [State("NEW_DOMAIN.entity_off", "not_supported")], blocking=True
    )

    assert "not_supported" in caplog.text
    assert len(turn_on_calls) == 0
    assert len(turn_off_calls) == 0

    # Make sure correct services are called
    await opp.helpers.state.async_reproduce_state(
        [
            State("NEW_DOMAIN.entity_on", "off"),
            State("NEW_DOMAIN.entity_off", "on", {"color": "red"}),
            # Should not raise
            State("NEW_DOMAIN.non_existing", "on"),
        ],
        blocking=True,
    )

    assert len(turn_on_calls) == 1
    assert turn_on_calls[0].domain == "NEW_DOMAIN"
    assert turn_on_calls[0].data == {
        "entity_id": "NEW_DOMAIN.entity_off",
        "color": "red",
    }

    assert len(turn_off_calls) == 1
    assert turn_off_calls[0].domain == "NEW_DOMAIN"
    assert turn_off_calls[0].data == {"entity_id": "NEW_DOMAIN.entity_on"}
