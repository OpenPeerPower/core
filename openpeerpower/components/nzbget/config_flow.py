"""Config flow for NZBGet."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from openpeerpower.config_entries import ConfigFlow, OptionsFlow
from openpeerpower.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.data_entry_flow import FlowResult
from openpeerpower.helpers.typing import ConfigType

from .const import (
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SSL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)
from .coordinator import NZBGetAPI, NZBGetAPIException

_LOGGER = logging.getLogger(__name__)


def validate_input(opp: OpenPeerPower, data: dict) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    nzbget_api = NZBGetAPI(
        data[CONF_HOST],
        data.get(CONF_USERNAME),
        data.get(CONF_PASSWORD),
        data[CONF_SSL],
        data[CONF_VERIFY_SSL],
        data[CONF_PORT],
    )

    nzbget_api.version()

    return True


class NZBGetConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NZBGet."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return NZBGetOptionsFlowHandler(config_entry)

    async def async_step_import(
        self, user_input: ConfigType | None = None
    ) -> FlowResult:
        """Handle a flow initiated by configuration file."""
        if CONF_SCAN_INTERVAL in user_input:
            user_input[CONF_SCAN_INTERVAL] = user_input[
                CONF_SCAN_INTERVAL
            ].total_seconds()

        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input: ConfigType | None = None) -> FlowResult:
        """Handle a flow initiated by the user."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors = {}

        if user_input is not None:
            if CONF_VERIFY_SSL not in user_input:
                user_input[CONF_VERIFY_SSL] = DEFAULT_VERIFY_SSL

            try:
                await self.opp.async_add_executor_job(
                    validate_input, self.opp, user_input
                )
            except NZBGetAPIException:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                return self.async_abort(reason="unknown")
            else:
                return self.async_create_entry(
                    title=user_input[CONF_HOST],
                    data=user_input,
                )

        data_schema = {
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
            vol.Optional(CONF_USERNAME): str,
            vol.Optional(CONF_PASSWORD): str,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            vol.Optional(CONF_SSL, default=DEFAULT_SSL): bool,
        }

        if self.show_advanced_options:
            data_schema[
                vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL)
            ] = bool

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=errors or {},
        )


class NZBGetOptionsFlowHandler(OptionsFlow):
    """Handle NZBGet client options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: ConfigType | None = None):
        """Manage NZBGet options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = {
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=self.config_entry.options.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                ),
            ): int,
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))
