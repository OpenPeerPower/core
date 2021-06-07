"""The SSDP integration."""
from __future__ import annotations

from collections.abc import Coroutine
from typing import Any, TypedDict

from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.data_entry_flow import FlowResult


class SSDPFlow(TypedDict):
    """A queued ssdp discovery flow."""

    domain: str
    context: dict[str, Any]
    data: dict


class FlowDispatcher:
    """Dispatch discovery flows."""

    def __init__(self, opp: OpenPeerPower) -> None:
        """Init the discovery dispatcher."""
        self.opp = opp
        self.pending_flows: list[SSDPFlow] = []
        self.started = False

    @callback
    def async_start(self, *_: Any) -> None:
        """Start processing pending flows."""
        self.started = True
        self.opp.loop.call_soon(self._async_process_pending_flows)

    def _async_process_pending_flows(self) -> None:
        for flow in self.pending_flows:
            self.opp.async_create_task(self._init_flow(flow))
        self.pending_flows = []

    def create(self, flow: SSDPFlow) -> None:
        """Create and add or queue a flow."""
        if self.started:
            self.opp.async_create_task(self._init_flow(flow))
        else:
            self.pending_flows.append(flow)

    def _init_flow(self, flow: SSDPFlow) -> Coroutine[None, None, FlowResult]:
        """Create a flow."""
        return self.opp.config_entries.flow.async_init(
            flow["domain"], context=flow["context"], data=flow["data"]
        )
