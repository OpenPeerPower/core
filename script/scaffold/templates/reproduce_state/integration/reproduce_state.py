"""Reproduce an NEW_NAME state."""
import asyncio
import logging
from typing import Any, Dict, Iterable, Optional

from openpeerpower.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from openpeerpower.core import Context, State
from openpeerpower.helpers.typing import OpenPeerPowerType

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

# TODO add valid states here
VALID_STATES = {STATE_ON, STATE_OFF}


async def _async_reproduce_state(
    opp: OpenPeerPowerType,
    state: State,
    *,
    context: Optional[Context] = None,
    reproduce_options: Optional[Dict[str, Any]] = None,
) -> None:
    """Reproduce a single state."""
    cur_state = opp.states.get(state.entity_id)

    if cur_state is None:
        _LOGGER.warning("Unable to find entity %s", state.entity_id)
        return

    if state.state not in VALID_STATES:
        _LOGGER.warning(
            "Invalid state specified for %s: %s", state.entity_id, state.state
        )
        return

    # Return if we are already at the right state.
    if (
        cur_state.state == state.state
        and
        # TODO this is an example attribute
        cur_state.attributes.get("color") == state.attributes.get("color")
    ):
        return

    service_data = {ATTR_ENTITY_ID: state.entity_id}

    # TODO determine the services to call to achieve desired state
    if state.state == STATE_ON:
        service = SERVICE_TURN_ON
        if "color" in state.attributes:
            service_data["color"] = state.attributes["color"]

    elif state.state == STATE_OFF:
        service = SERVICE_TURN_OFF

    await opp.services.async_call(
        DOMAIN, service, service_data, context=context, blocking=True
    )


async def async_reproduce_states(
    opp: OpenPeerPowerType,
    states: Iterable[State],
    *,
    context: Optional[Context] = None,
    reproduce_options: Optional[Dict[str, Any]] = None,
) -> None:
    """Reproduce NEW_NAME states."""
    # TODO pick one and remove other one

    # Reproduce states in parallel.
    await asyncio.gather(
        *(
            _async_reproduce_state(
                opp, state, context=context, reproduce_options=reproduce_options
            )
            for state in states
        )
    )

    # Alternative: Reproduce states in sequence
    # for state in states:
    #     await _async_reproduce_state.opp, state, context=context, reproduce_options=reproduce_options)
