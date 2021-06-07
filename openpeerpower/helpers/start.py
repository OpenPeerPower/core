"""Helpers to help during startup."""
from collections.abc import Awaitable
from typing import Callable

from openpeerpower.const import EVENT_OPENPEERPOWER_START
from openpeerpower.core import Event, OpenPeerPower, callback


@callback
def async_at_start(
    opp: OpenPeerPower, at_start_cb: Callable[[OpenPeerPower], Awaitable]
) -> None:
    """Execute something when Open Peer Power is started.

    Will execute it now if Open Peer Power is already started.
    """
    if opp.is_running:
        opp.async_create_task(at_start_cb(opp))
        return

    async def _matched_event(event: Event) -> None:
        """Call the callback when Open Peer Power started."""
        await at_start_cb(opp)

    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_START, _matched_event)
