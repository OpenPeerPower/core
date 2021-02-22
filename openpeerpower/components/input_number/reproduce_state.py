"""Reproduce an Input number state."""
import asyncio
import logging
from typing import Any, Dict, Iterable, Optional

import voluptuous as vol

from openpeerpower.const import ATTR_ENTITY_ID
from openpeerpower.core import Context, State
from openpeerpower.helpers.typing import OpenPeerPowerType

from . import ATTR_VALUE, DOMAIN, SERVICE_SET_VALUE

_LOGGER = logging.getLogger(__name__)


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

    try:
        float(state.state)
    except ValueError:
        _LOGGER.warning(
            "Invalid state specified for %s: %s", state.entity_id, state.state
        )
        return

    # Return if we are already at the right state.
    if cur_state.state == state.state:
        return

    service = SERVICE_SET_VALUE
    service_data = {ATTR_ENTITY_ID: state.entity_id, ATTR_VALUE: state.state}

    try:
        await opp.services.async_call(
            DOMAIN, service, service_data, context=context, blocking=True
        )
    except vol.Invalid as err:
        # If value out of range.
        _LOGGER.warning("Unable to reproduce state for %s: %s", state.entity_id, err)


async def async_reproduce_states(
    opp: OpenPeerPowerType,
    states: Iterable[State],
    *,
    context: Optional[Context] = None,
    reproduce_options: Optional[Dict[str, Any]] = None,
) -> None:
    """Reproduce Input number states."""
    # Reproduce states in parallel.
    await asyncio.gather(
        *(
            _async_reproduce_state(
                opp, state, context=context, reproduce_options=reproduce_options
            )
            for state in states
        )
    )
