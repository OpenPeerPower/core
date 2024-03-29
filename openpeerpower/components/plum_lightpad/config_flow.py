"""Config flow for Plum Lightpad."""
from __future__ import annotations

import logging

from aiohttp import ContentTypeError
from requests.exceptions import ConnectTimeout, HTTPError
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME
from openpeerpower.data_entry_flow import FlowResult
from openpeerpower.helpers.typing import ConfigType

from .const import DOMAIN
from .utils import load_plum

_LOGGER = logging.getLogger(__name__)


class PlumLightpadConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Plum Lightpad integration."""

    VERSION = 1

    def _show_form(self, errors=None):
        schema = {
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema),
            errors=errors or {},
        )

    async def async_step_user(self, user_input: ConfigType | None = None) -> FlowResult:
        """Handle a flow initialized by the user or redirected to by import."""
        if not user_input:
            return self._show_form()

        username = user_input[CONF_USERNAME]
        password = user_input[CONF_PASSWORD]

        # load Plum just so we know username/password work
        try:
            await load_plum(username, password, self.opp)
        except (ContentTypeError, ConnectTimeout, HTTPError) as ex:
            _LOGGER.error("Unable to connect/authenticate to Plum cloud: %s", str(ex))
            return self._show_form({"base": "cannot_connect"})

        await self.async_set_unique_id(username)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=username, data={CONF_USERNAME: username, CONF_PASSWORD: password}
        )

    async def async_step_import(self, import_config: ConfigType | None) -> FlowResult:
        """Import a config entry from configuration.yaml."""
        return await self.async_step_user(import_config)
