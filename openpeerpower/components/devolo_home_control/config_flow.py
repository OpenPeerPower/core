"""Config flow to configure the devolo home control integration."""
import logging

from devolo_home_control_api.mydevolo import Mydevolo
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME
from openpeerpower.core import callback

from .const import (  # pylint:disable=unused-import
    CONF_MYDEVOLO,
    DEFAULT_MYDEVOLO,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class DevoloHomeControlFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a devolo HomeControl config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    def __init__(self):
        """Initialize devolo Home Control flow."""
        self.data_schema = {
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
        }

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        if self.show_advanced_options:
            self.data_schema = {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_MYDEVOLO, default=DEFAULT_MYDEVOLO): str,
            }
        if user_input is None:
            return self._show_form(user_input)
        user = user_input[CONF_USERNAME]
        password = user_input[CONF_PASSWORD]
        mydevolo = Mydevolo()
        mydevolo.user = user
        mydevolo.password = password
        if self.show_advanced_options:
            mydevolo.url = user_input[CONF_MYDEVOLO]
        else:
            mydevolo.url = DEFAULT_MYDEVOLO
        credentials_valid = await self.opp.async_add_executor_job(
            mydevolo.credentials_valid
        )
        if not credentials_valid:
            return self._show_form({"base": "invalid_auth"})
        _LOGGER.debug("Credentials valid")
        uuid = await self.opp.async_add_executor_job(mydevolo.uuid)
        await self.async_set_unique_id(uuid)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title="devolo Home Control",
            data={
                CONF_PASSWORD: password,
                CONF_USERNAME: user,
                CONF_MYDEVOLO: mydevolo.url,
            },
        )

    @callback
    def _show_form(self, errors=None):
        """Show the form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(self.data_schema),
            errors=errors if errors else {},
        )
