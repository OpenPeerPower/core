"""Trace support for automation."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from openpeerpower.components.trace import ActionTrace, async_store_trace
from openpeerpower.components.trace.const import CONF_STORED_TRACES
from openpeerpower.core import Context

# mypy: allow-untyped-calls, allow-untyped-defs
# mypy: no-check-untyped-defs, no-warn-return-any


class AutomationTrace(ActionTrace):
    """Container for automation trace."""

    def __init__(
        self,
        item_id: str,
        config: dict[str, Any],
        blueprint_inputs: dict[str, Any],
        context: Context,
    ) -> None:
        """Container for automation trace."""
        key = ("automation", item_id)
        super().__init__(key, config, blueprint_inputs, context)
        self._trigger_description: str | None = None

    def set_trigger_description(self, trigger: str) -> None:
        """Set trigger description."""
        self._trigger_description = trigger

    def as_short_dict(self) -> dict[str, Any]:
        """Return a brief dictionary version of this AutomationTrace."""
        result = super().as_short_dict()
        result["trigger"] = self._trigger_description
        return result


@contextmanager
def trace_automation(
    opp, automation_id, config, blueprint_inputs, context, trace_config
):
    """Trace action execution of automation with automation_id."""
    trace = AutomationTrace(automation_id, config, blueprint_inputs, context)
    async_store_trace(opp, trace, trace_config[CONF_STORED_TRACES])

    try:
        yield trace
    except Exception as ex:
        if automation_id:
            trace.set_error(ex)
        raise ex
    finally:
        if automation_id:
            trace.finished()
