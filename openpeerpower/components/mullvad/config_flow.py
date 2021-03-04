"""Config flow for Mullvad VPN integration."""
import logging

from mullvad_api import MullvadAPI, MullvadAPIError

from openpeerpower import config_entries

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mullvad VPN."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if self.opp.config_entries.async_entries(DOMAIN):
            return self.async_abort(reason="already_configured")

        errors = {}
        if user_input is not None:
            try:
                await self.opp.async_add_executor_job(MullvadAPI)
            except MullvadAPIError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title="Mullvad VPN", data=user_input)

        return self.async_show_form(step_id="user", errors=errors)
