"""Test reproduce state for Input number."""
from openpeerpower.core import State
from openpeerpower.setup import async_setup_component

VALID_NUMBER1 = "19.0"
VALID_NUMBER2 = "99.9"


async def test_reproducing_states.opp, caplog):
    """Test reproducing Input number states."""

    assert await async_setup_component(
       .opp,
        "input_number",
        {
            "input_number": {
                "test_number": {"min": "5", "max": "100", "initial": VALID_NUMBER1}
            }
        },
    )

    # These calls should do nothing as entities already in desired state
    await opp.helpers.state.async_reproduce_state(
        [
            State("input_number.test_number", VALID_NUMBER1),
            # Should not raise
            State("input_number.non_existing", "234"),
        ],
    )

    assert.opp.states.get("input_number.test_number").state == VALID_NUMBER1

    # Test reproducing with different state
    await opp.helpers.state.async_reproduce_state(
        [
            State("input_number.test_number", VALID_NUMBER2),
            # Should not raise
            State("input_number.non_existing", "234"),
        ],
    )

    assert.opp.states.get("input_number.test_number").state == VALID_NUMBER2

    # Test setting state to number out of range
    await opp.helpers.state.async_reproduce_state(
        [State("input_number.test_number", "150")]
    )

    # The entity states should be unchanged after trying to set them to out-of-range number
    assert.opp.states.get("input_number.test_number").state == VALID_NUMBER2

    await opp.helpers.state.async_reproduce_state(
        [
            # Test invalid state
            State("input_number.test_number", "invalid_state"),
            # Set to state it already is.
            State("input_number.test_number", VALID_NUMBER2),
        ],
    )
