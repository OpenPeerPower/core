"""Trace support for script."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from openpeerpower.components.trace import ActionTrace, async_store_trace
from openpeerpower.components.trace.const import CONF_STORED_TRACES
from openpeerpower.core import Context, OpenPeerPower


class ScriptTrace(ActionTrace):
    """Container for automation trace."""

    def __init__(
        self,
        item_id: str,
        config: dict[str, Any],
        blueprint_inputs: dict[str, Any],
        context: Context,
    ) -> None:
        """Container for automation trace."""
        key = ("script", item_id)
        super().__init__(key, config, blueprint_inputs, context)


@contextmanager
def trace_script(
    opp: OpenPeerPower,
    item_id: str,
    config: dict[str, Any],
    blueprint_inputs: dict[str, Any],
    context: Context,
    trace_config: dict[str, Any],
) -> Iterator[ScriptTrace]:
    """Trace execution of a script."""
    trace = ScriptTrace(item_id, config, blueprint_inputs, context)
    async_store_trace(opp, trace, trace_config[CONF_STORED_TRACES])

    try:
        yield trace
    except Exception as ex:
        if item_id:
            trace.set_error(ex)
        raise ex
    finally:
        if item_id:
            trace.finished()
