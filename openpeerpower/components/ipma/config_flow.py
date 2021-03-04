"""Config flow to configure IPMA component."""
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_MODE, CONF_NAME
import openpeerpower.helpers.config_validation as cv

from .const import DOMAIN, HOME_LOCATION_NAME
from .weather import FORECAST_MODE


@config_entries.HANDLERS.register(DOMAIN)
class IpmaFlowHandler(config_entries.ConfigFlow):
    """Config flow for IPMA component."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Init IpmaFlowHandler."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        if user_input is not None:
            if user_input[CONF_NAME] not in self.opp.config_entries.async_entries(
                DOMAIN
            ):
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

            self._errors[CONF_NAME] = "name_exists"

        # default location is set opp configuration
        return await self._show_config_form(
            name=HOME_LOCATION_NAME,
            latitude=self.opp.config.latitude,
            longitude=self.opp.config.longitude,
        )

    async def _show_config_form(self, name=None, latitude=None, longitude=None):
        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default=name): str,
                    vol.Required(CONF_LATITUDE, default=latitude): cv.latitude,
                    vol.Required(CONF_LONGITUDE, default=longitude): cv.longitude,
                    vol.Required(CONF_MODE, default="daily"): vol.In(FORECAST_MODE),
                }
            ),
            errors=self._errors,
        )
