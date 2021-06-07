"""Adds config flow for GIOS."""
from __future__ import annotations

import asyncio
from typing import Any

from aiohttp.client_exceptions import ClientConnectorError
from async_timeout import timeout
from gios import ApiError, Gios, InvalidSensorsData, NoStationError
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.const import CONF_NAME
from openpeerpower.data_entry_flow import FlowResult
from openpeerpower.helpers.aiohttp_client import async_get_clientsession

from .const import API_TIMEOUT, CONF_STATION_ID, DEFAULT_NAME, DOMAIN

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_STATION_ID): int,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
    }
)


class GiosFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for GIOS."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            try:
                await self.async_set_unique_id(
                    str(user_input[CONF_STATION_ID]), raise_on_progress=False
                )
                self._abort_if_unique_id_configured()

                websession = async_get_clientsession(self.opp)

                with timeout(API_TIMEOUT):
                    gios = Gios(user_input[CONF_STATION_ID], websession)
                    await gios.async_update()

                return self.async_create_entry(
                    title=user_input[CONF_STATION_ID],
                    data=user_input,
                )
            except (ApiError, ClientConnectorError, asyncio.TimeoutError):
                errors["base"] = "cannot_connect"
            except NoStationError:
                errors[CONF_STATION_ID] = "wrong_station_id"
            except InvalidSensorsData:
                errors[CONF_STATION_ID] = "invalid_sensors_data"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
