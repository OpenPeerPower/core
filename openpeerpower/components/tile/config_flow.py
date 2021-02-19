"""Config flow to configure the Tile integration."""
from pytile import async_login
from pytile.errors import TileError
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME
from openpeerpower.helpers import aiohttp_client

from .const import DOMAIN  # pylint: disable=unused-import


class TileFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Tile config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize the config flow."""
        self.data_schema = vol.Schema(
            {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
        )

    async def _show_form(self, errors=None):
        """Show the form to the user."""
        return self.async_show_form(
            step_id="user", data_schema=self.data_schema, errors=errors or {}
        )

    async def async_step_import(self, import_config):
        """Import a config entry from configuration.yaml."""
        return await self.async_step_user(import_config)

    async def async_step_user(self, user_input=None):
        """Handle the start of the config flow."""
        if not user_input:
            return await self._show_form()

        await self.async_set_unique_id(user_input[CONF_USERNAME])
        self._abort_if_unique_id_configured()

        session = aiohttp_client.async_get_clientsession(self.opp)

        try:
            await async_login(
                user_input[CONF_USERNAME], user_input[CONF_PASSWORD], session=session
            )
        except TileError:
            return await self._show_form({"base": "invalid_auth"})

        return self.async_create_entry(title=user_input[CONF_USERNAME], data=user_input)
