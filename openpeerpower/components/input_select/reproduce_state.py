"""Reproduce an Input select state."""
from __future__ import annotations

import asyncio
from collections.abc import Iterable
import logging
from types import MappingProxyType
from typing import Any

from openpeerpower.const import ATTR_ENTITY_ID
from openpeerpower.core import Context, OpenPeerPower, State

from . import (
    ATTR_OPTION,
    ATTR_OPTIONS,
    DOMAIN,
    SERVICE_SELECT_OPTION,
    SERVICE_SET_OPTIONS,
)

ATTR_GROUP = [ATTR_OPTION, ATTR_OPTIONS]

_LOGGER = logging.getLogger(__name__)


async def _async_reproduce_state(
    opp: OpenPeerPower,
    state: State,
    *,
    context: Context | None = None,
    reproduce_options: dict[str, Any] | None = None,
) -> None:
    """Reproduce a single state."""
    cur_state = opp.states.get(state.entity_id)

    # Return if we can't find entity
    if cur_state is None:
        _LOGGER.warning("Unable to find entity %s", state.entity_id)
        return

    # Return if we are already at the right state.
    if cur_state.state == state.state and all(
        check_attr_equal(cur_state.attributes, state.attributes, attr)
        for attr in ATTR_GROUP
    ):
        return

    # Set service data
    service_data = {ATTR_ENTITY_ID: state.entity_id}

    # If options are specified, call SERVICE_SET_OPTIONS
    if ATTR_OPTIONS in state.attributes:
        service = SERVICE_SET_OPTIONS
        service_data[ATTR_OPTIONS] = state.attributes[ATTR_OPTIONS]

        await opp.services.async_call(
            DOMAIN, service, service_data, context=context, blocking=True
        )

        # Remove ATTR_OPTIONS from service_data so we can reuse service_data in next call
        del service_data[ATTR_OPTIONS]

    # Call SERVICE_SELECT_OPTION
    service = SERVICE_SELECT_OPTION
    service_data[ATTR_OPTION] = state.state

    await opp.services.async_call(
        DOMAIN, service, service_data, context=context, blocking=True
    )


async def async_reproduce_states(
    opp: OpenPeerPower,
    states: Iterable[State],
    *,
    context: Context | None = None,
    reproduce_options: dict[str, Any] | None = None,
) -> None:
    """Reproduce Input select states."""
    # Reproduce states in parallel.
    await asyncio.gather(
        *(
            _async_reproduce_state(
                opp, state, context=context, reproduce_options=reproduce_options
            )
            for state in states
        )
    )


def check_attr_equal(
    attr1: MappingProxyType, attr2: MappingProxyType, attr_str: str
) -> bool:
    """Return true if the given attributes are equal."""
    return attr1.get(attr_str) == attr2.get(attr_str)
