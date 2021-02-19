"""Config flow to configure the EcoNet component."""
from pyeconet import EcoNetApiInterface
from pyeconet.errors import InvalidCredentialsError, PyeconetError
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.const import CONF_EMAIL, CONF_PASSWORD

from .const import DOMAIN  # pylint: disable=unused-import


class EcoNetFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle an EcoNet config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize the config flow."""
        self.data_schema = vol.Schema(
            {
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

    async def async_step_user(self, user_input=None):
        """Handle the start of the config flow."""
        if not user_input:
            return self.async_show_form(
                step_id="user",
                data_schema=self.data_schema,
            )

        await self.async_set_unique_id(user_input[CONF_EMAIL])
        self._abort_if_unique_id_configured()
        errors = {}

        try:
            await EcoNetApiInterface.login(
                user_input[CONF_EMAIL], user_input[CONF_PASSWORD]
            )
        except InvalidCredentialsError:
            errors["base"] = "invalid_auth"
        except PyeconetError:
            errors["base"] = "cannot_connect"

        if errors:
            return self.async_show_form(
                step_id="user",
                data_schema=self.data_schema,
                errors=errors,
            )

        return self.async_create_entry(
            title=user_input[CONF_EMAIL],
            data={
                CONF_EMAIL: user_input[CONF_EMAIL],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
            },
        )
