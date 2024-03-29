"""Config flow for PoolSense integration."""
import logging

from poolsense import PoolSense
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.const import CONF_EMAIL, CONF_PASSWORD
from openpeerpower.helpers import aiohttp_client

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class PoolSenseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PoolSense."""

    VERSION = 1

    def __init__(self):
        """Initialize PoolSense config flow."""

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_EMAIL])
            self._abort_if_unique_id_configured()

            _LOGGER.debug(
                "Configuring user: %s - Password hidden", user_input[CONF_EMAIL]
            )

            poolsense = PoolSense(
                aiohttp_client.async_get_clientsession(self.opp),
                user_input[CONF_EMAIL],
                user_input[CONF_PASSWORD],
            )
            api_key_valid = await poolsense.test_poolsense_credentials()

            if not api_key_valid:
                errors["base"] = "invalid_auth"

            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_EMAIL],
                    data={
                        CONF_EMAIL: user_input[CONF_EMAIL],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_EMAIL): str, vol.Required(CONF_PASSWORD): str}
            ),
            errors=errors,
        )
