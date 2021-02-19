"""Test reproduce state for input boolean."""
from openpeerpowerr.core import State
from openpeerpowerr.setup import async_setup_component


async def test_reproducing_states.opp):
    """Test reproducing input_boolean states."""
    assert await async_setup_component(
       .opp,
        "input_boolean",
        {
            "input_boolean": {
                "initial_on": {"initial": True},
                "initial_off": {"initial": False},
            }
        },
    )
    await.opp.helpers.state.async_reproduce_state(
        [
            State("input_boolean.initial_on", "off"),
            State("input_boolean.initial_off", "on"),
            # Should not raise
            State("input_boolean.non_existing", "on"),
        ],
    )
    assert.opp.states.get("input_boolean.initial_off").state == "on"
    assert.opp.states.get("input_boolean.initial_on").state == "off"

    await.opp.helpers.state.async_reproduce_state(
        [
            # Test invalid state
            State("input_boolean.initial_on", "invalid_state"),
            # Set to state it already is.
            State("input_boolean.initial_off", "on"),
        ],
    )

    assert.opp.states.get("input_boolean.initial_on").state == "off"
    assert.opp.states.get("input_boolean.initial_off").state == "on"
