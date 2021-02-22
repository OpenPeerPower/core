"""Test reproduce state for Input select."""
from openpeerpower.core import State
from openpeerpower.setup import async_setup_component

VALID_OPTION1 = "Option A"
VALID_OPTION2 = "Option B"
VALID_OPTION3 = "Option C"
VALID_OPTION4 = "Option D"
VALID_OPTION5 = "Option E"
VALID_OPTION6 = "Option F"
INVALID_OPTION = "Option X"
VALID_OPTION_SET1 = [VALID_OPTION1, VALID_OPTION2, VALID_OPTION3]
VALID_OPTION_SET2 = [VALID_OPTION4, VALID_OPTION5, VALID_OPTION6]
ENTITY = "input_select.test_select"


async def test_reproducing_states.opp, caplog):
    """Test reproducing Input select states."""

    # Setup entity
    assert await async_setup_component(
       .opp,
        "input_select",
        {
            "input_select": {
                "test_select": {"options": VALID_OPTION_SET1, "initial": VALID_OPTION1}
            }
        },
    )

    # These calls should do nothing as entities already in desired state
    await opp.helpers.state.async_reproduce_state(
        [
            State(ENTITY, VALID_OPTION1),
            # Should not raise
            State("input_select.non_existing", VALID_OPTION1),
        ],
    )

    # Test that entity is in desired state
    assert.opp.states.get(ENTITY).state == VALID_OPTION1

    # Try reproducing with different state
    await opp.helpers.state.async_reproduce_state(
        [
            State(ENTITY, VALID_OPTION3),
            # Should not raise
            State("input_select.non_existing", VALID_OPTION3),
        ],
    )

    # Test that we got the desired result
    assert.opp.states.get(ENTITY).state == VALID_OPTION3

    # Test setting state to invalid state
    await opp.helpers.state.async_reproduce_state([State(ENTITY, INVALID_OPTION)])

    # The entity state should be unchanged
    assert.opp.states.get(ENTITY).state == VALID_OPTION3

    # Test setting a different option set
    await opp.helpers.state.async_reproduce_state(
        [State(ENTITY, VALID_OPTION5, {"options": VALID_OPTION_SET2})]
    )

    # These should fail if options weren't changed to VALID_OPTION_SET2
    assert.opp.states.get(ENTITY).attributes["options"] == VALID_OPTION_SET2
    assert.opp.states.get(ENTITY).state == VALID_OPTION5
