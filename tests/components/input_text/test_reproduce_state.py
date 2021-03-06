"""Test reproduce state for Input text."""
from openpeerpower.core import State
from openpeerpower.setup import async_setup_component

VALID_TEXT1 = "Test text"
VALID_TEXT2 = "LoremIpsum"
INVALID_TEXT1 = "This text is too long!"
INVALID_TEXT2 = "Short"


async def test_reproducing_states(opp, caplog):
    """Test reproducing Input text states."""

    # Setup entity for testing
    assert await async_setup_component(
        opp,
        "input_text",
        {
            "input_text": {
                "test_text": {"min": "6", "max": "10", "initial": VALID_TEXT1}
            }
        },
    )

    # These calls should do nothing as entities already in desired state
    await opp.helpers.state.async_reproduce_state(
        [
            State("input_text.test_text", VALID_TEXT1),
            # Should not raise
            State("input_text.non_existing", VALID_TEXT1),
        ],
    )

    # Test that entity is in desired state
    assert opp.states.get("input_text.test_text").state == VALID_TEXT1

    # Try reproducing with different state
    await opp.helpers.state.async_reproduce_state(
        [
            State("input_text.test_text", VALID_TEXT2),
            # Should not raise
            State("input_text.non_existing", VALID_TEXT2),
        ],
    )

    # Test that the state was changed
    assert opp.states.get("input_text.test_text").state == VALID_TEXT2

    # Test setting state to invalid state (length too long)
    await opp.helpers.state.async_reproduce_state(
        [State("input_text.test_text", INVALID_TEXT1)]
    )

    # The entity state should be unchanged
    assert opp.states.get("input_text.test_text").state == VALID_TEXT2

    # Test setting state to invalid state (length too short)
    await opp.helpers.state.async_reproduce_state(
        [State("input_text.test_text", INVALID_TEXT2)]
    )

    # The entity state should be unchanged
    assert opp.states.get("input_text.test_text").state == VALID_TEXT2
