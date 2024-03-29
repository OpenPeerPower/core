"""Adds config flow for AccuWeather."""
from __future__ import annotations

import asyncio
from typing import Any

from accuweather import AccuWeather, ApiError, InvalidApiKeyError, RequestsExceededError
from aiohttp import ClientError
from aiohttp.client_exceptions import ClientConnectorError
from async_timeout import timeout
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from openpeerpower.core import callback
from openpeerpower.data_entry_flow import FlowResult
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
import openpeerpower.helpers.config_validation as cv

from .const import CONF_FORECAST, DOMAIN


class AccuWeatherFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for AccuWeather."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        # Under the terms of use of the API, one user can use one free API key. Due to
        # the small number of requests allowed, we only allow one integration instance.
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors = {}

        if user_input is not None:
            websession = async_get_clientsession(self.opp)
            try:
                async with timeout(10):
                    accuweather = AccuWeather(
                        user_input[CONF_API_KEY],
                        websession,
                        latitude=user_input[CONF_LATITUDE],
                        longitude=user_input[CONF_LONGITUDE],
                    )
                    await accuweather.async_get_location()
            except (ApiError, ClientConnectorError, asyncio.TimeoutError, ClientError):
                errors["base"] = "cannot_connect"
            except InvalidApiKeyError:
                errors[CONF_API_KEY] = "invalid_api_key"
            except RequestsExceededError:
                errors[CONF_API_KEY] = "requests_exceeded"
            else:
                await self.async_set_unique_id(
                    accuweather.location_key, raise_on_progress=False
                )

                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                    vol.Optional(
                        CONF_LATITUDE, default=self.opp.config.latitude
                    ): cv.latitude,
                    vol.Optional(
                        CONF_LONGITUDE, default=self.opp.config.longitude
                    ): cv.longitude,
                    vol.Optional(CONF_NAME, default=self.opp.config.location_name): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> AccuWeatherOptionsFlowHandler:
        """Options callback for AccuWeather."""
        return AccuWeatherOptionsFlowHandler(config_entry)


class AccuWeatherOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options for AccuWeather."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize AccuWeather options flow."""
        self.config_entry = entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_FORECAST,
                        default=self.config_entry.options.get(CONF_FORECAST, False),
                    ): bool
                }
            ),
        )
