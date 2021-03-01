"""Reproduce an Counter state."""
import asyncio
import logging
from typing import Any, Dict, Iterable, Optional

from openpeerpower.const import ATTR_ENTITY_ID
from openpeerpower.core import Context, State
from openpeerpower.helpers.typing import OpenPeerPowerType

from . import (
    ATTR_INITIAL,
    ATTR_MAXIMUM,
    ATTR_MINIMUM,
    ATTR_STEP,
    DOMAIN,
    SERVICE_CONFIGURE,
    VALUE,
)

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

    if not state.state.isdigit():
        _LOGGER.warning(
            "Invalid state specified for %s: %s", state.entity_id, state.state
        )
        return

    # Return if we are already at the right state.
    if (
        cur_state.state == state.state
        and cur_state.attributes.get(ATTR_INITIAL) == state.attributes.get(ATTR_INITIAL)
        and cur_state.attributes.get(ATTR_MAXIMUM) == state.attributes.get(ATTR_MAXIMUM)
        and cur_state.attributes.get(ATTR_MINIMUM) == state.attributes.get(ATTR_MINIMUM)
        and cur_state.attributes.get(ATTR_STEP) == state.attributes.get(ATTR_STEP)
    ):
        return

    service_data = {ATTR_ENTITY_ID: state.entity_id, VALUE: state.state}
    service = SERVICE_CONFIGURE
    if ATTR_INITIAL in state.attributes:
        service_data[ATTR_INITIAL] = state.attributes[ATTR_INITIAL]
    if ATTR_MAXIMUM in state.attributes:
        service_data[ATTR_MAXIMUM] = state.attributes[ATTR_MAXIMUM]
    if ATTR_MINIMUM in state.attributes:
        service_data[ATTR_MINIMUM] = state.attributes[ATTR_MINIMUM]
    if ATTR_STEP in state.attributes:
        service_data[ATTR_STEP] = state.attributes[ATTR_STEP]

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
    """Reproduce Counter states."""
    await asyncio.gather(
        *(
            _async_reproduce_state(
                opp, state, context=context, reproduce_options=reproduce_options
            )
            for state in states
        )
    )
