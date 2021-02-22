"""The tests for reproduction of state."""

from asyncio import Future
from unittest.mock import patch

from openpeerpower.components.group.reproduce_state import async_reproduce_states
from openpeerpower.core import Context, State


async def test_reproduce_group.opp):
    """Test reproduce_state with group."""
    context = Context()

    def clone_state(state, entity_id):
        """Return a cloned state with different entity_id."""
        return State(
            entity_id,
            state.state,
            state.attributes,
            last_changed=state.last_changed,
            last_updated=state.last_updated,
            context=state.context,
        )

    with patch(
        "openpeerpower.components.group.reproduce_state.async_reproduce_state"
    ) as fun:
        fun.return_value = Future()
        fun.return_value.set_result(None)

        opp.states.async_set(
            "group.test",
            "off",
            {"entity_id": ["light.test1", "light.test2", "switch.test1"]},
        )
        opp.states.async_set("light.test1", "off")
        opp.states.async_set("light.test2", "off")
        opp.states.async_set("switch.test1", "off")

        state = State("group.test", "on")

        await async_reproduce_states.opp, [state], context=context)

        fun.assert_called_once_with(
            opp.
            [
                clone_state(state, "light.test1"),
                clone_state(state, "light.test2"),
                clone_state(state, "switch.test1"),
            ],
            context=context,
            reproduce_options=None,
        )
