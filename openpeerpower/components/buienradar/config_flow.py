"""Config flow for buienradar integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_LATITUDE, CONF_LONGITUDE
from openpeerpower.core import callback
from openpeerpower.data_entry_flow import FlowResult
import openpeerpower.helpers.config_validation as cv

from .const import (
    CONF_COUNTRY,
    CONF_DELTA,
    CONF_TIMEFRAME,
    DEFAULT_COUNTRY,
    DEFAULT_DELTA,
    DEFAULT_TIMEFRAME,
    DOMAIN,
    SUPPORTED_COUNTRY_CODES,
)

_LOGGER = logging.getLogger(__name__)


class BuienradarFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for buienradar."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> BuienradarOptionFlowHandler:
        """Get the options flow for this handler."""
        return BuienradarOptionFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            lat = user_input.get(CONF_LATITUDE)
            lon = user_input.get(CONF_LONGITUDE)

            await self.async_set_unique_id(f"{lat}-{lon}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=f"{lat},{lon}", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_LATITUDE, default=self.opp.config.latitude
                ): cv.latitude,
                vol.Required(
                    CONF_LONGITUDE, default=self.opp.config.longitude
                ): cv.longitude,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors={},
        )

    async def async_step_import(self, import_input: dict[str, Any]) -> FlowResult:
        """Import a config entry."""
        latitude = import_input[CONF_LATITUDE]
        longitude = import_input[CONF_LONGITUDE]

        await self.async_set_unique_id(f"{latitude}-{longitude}")
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"{latitude},{longitude}", data=import_input
        )


class BuienradarOptionFlowHandler(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_COUNTRY,
                        default=self.config_entry.options.get(
                            CONF_COUNTRY,
                            self.config_entry.data.get(CONF_COUNTRY, DEFAULT_COUNTRY),
                        ),
                    ): vol.In(SUPPORTED_COUNTRY_CODES),
                    vol.Optional(
                        CONF_DELTA,
                        default=self.config_entry.options.get(
                            CONF_DELTA,
                            self.config_entry.data.get(CONF_DELTA, DEFAULT_DELTA),
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0)),
                    vol.Optional(
                        CONF_TIMEFRAME,
                        default=self.config_entry.options.get(
                            CONF_TIMEFRAME,
                            self.config_entry.data.get(
                                CONF_TIMEFRAME, DEFAULT_TIMEFRAME
                            ),
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=120)),
                }
            ),
        )
