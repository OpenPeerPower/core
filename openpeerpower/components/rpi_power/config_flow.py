"""Config flow for Raspberry Pi Power Supply Checker."""
from __future__ import annotations

from typing import Any

from rpi_bad_power import new_under_voltage

from openpeerpower.core import OpenPeerPower
from openpeerpower.data_entry_flow import FlowResult
from openpeerpower.helpers.config_entry_flow import DiscoveryFlowHandler

from .const import DOMAIN


async def _async_supported(opp: OpenPeerPower) -> bool:
    """Return if the system supports under voltage detection."""
    under_voltage = await opp.async_add_executor_job(new_under_voltage)
    return under_voltage is not None


class RPiPowerFlow(DiscoveryFlowHandler, domain=DOMAIN):
    """Discovery flow handler."""

    VERSION = 1

    def __init__(self) -> None:
        """Set up config flow."""
        super().__init__(
            DOMAIN,
            "Raspberry Pi Power Supply Checker",
            _async_supported,
        )

    async def async_step_onboarding(
        self, data: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by onboarding."""
        has_devices = await self._discovery_function(self.opp)

        if not has_devices:
            return self.async_abort(reason="no_devices_found")
        return self.async_create_entry(title=self._title, data={})
