"""Config flow for Litter-Robot integration."""
import logging

from pylitterbot.exceptions import LitterRobotException, LitterRobotLoginException
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME

from .const import DOMAIN  # pylint:disable=unused-import
from .hub import LitterRobotHub

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Litter-Robot."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            for entry in self._async_current_entries():
                if entry.data[CONF_USERNAME] == user_input[CONF_USERNAME]:
                    return self.async_abort(reason="already_configured")

            hub = LitterRobotHub(self.opp, user_input)
            try:
                await hub.login()
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME], data=user_input
                )
            except LitterRobotLoginException:
                errors["base"] = "invalid_auth"
            except LitterRobotException:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
