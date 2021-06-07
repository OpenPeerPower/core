"""Reproduce an input boolean state."""
from __future__ import annotations

import asyncio
from collections.abc import Iterable
import logging
from typing import Any

from openpeerpower.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from openpeerpower.core import Context, OpenPeerPower, State

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def _async_reproduce_states(
    opp: OpenPeerPower,
    state: State,
    *,
    context: Context | None = None,
    reproduce_options: dict[str, Any] | None = None,
) -> None:
    """Reproduce input boolean states."""
    cur_state = opp.states.get(state.entity_id)

    if cur_state is None:
        _LOGGER.warning("Unable to find entity %s", state.entity_id)
        return

    if state.state not in (STATE_ON, STATE_OFF):
        _LOGGER.warning(
            "Invalid state specified for %s: %s", state.entity_id, state.state
        )
        return

    if cur_state.state == state.state:
        return

    service = SERVICE_TURN_ON if state.state == STATE_ON else SERVICE_TURN_OFF

    await opp.services.async_call(
        DOMAIN,
        service,
        {ATTR_ENTITY_ID: state.entity_id},
        context=context,
        blocking=True,
    )


async def async_reproduce_states(
    opp: OpenPeerPower,
    states: Iterable[State],
    *,
    context: Context | None = None,
    reproduce_options: dict[str, Any] | None = None,
) -> None:
    """Reproduce component states."""
    await asyncio.gather(
        *(
            _async_reproduce_states(
                opp, state, context=context, reproduce_options=reproduce_options
            )
            for state in states
        )
    )
