"""Define a config flow manager for flunearyou."""
from pyflunearyou import Client
from pyflunearyou.errors import FluNearYouError
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.const import CONF_LATITUDE, CONF_LONGITUDE
from openpeerpower.helpers import aiohttp_client, config_validation as cv

from .const import DOMAIN, LOGGER  # pylint: disable=unused-import


class FluNearYouFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle an FluNearYou config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    @property
    def data_schema(self):
        """Return the data schema for integration."""
        return vol.Schema(
            {
                vol.Required(
                    CONF_LATITUDE, default=self.opp.config.latitude
                ): cv.latitude,
                vol.Required(
                    CONF_LONGITUDE, default=self.opp.config.longitude
                ): cv.longitude,
            }
        )

    async def async_step_user(self, user_input=None):
        """Handle the start of the config flow."""
        if not user_input:
            return self.async_show_form(step_id="user", data_schema=self.data_schema)

        unique_id = f"{user_input[CONF_LATITUDE]}, {user_input[CONF_LONGITUDE]}"

        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        websession = aiohttp_client.async_get_clientsession(self.opp)
        client = Client(websession)

        try:
            await client.cdc_reports.status_by_coordinates(
                user_input[CONF_LATITUDE], user_input[CONF_LONGITUDE]
            )
        except FluNearYouError as err:
            LOGGER.error("Error while configuring integration: %s", err)
            return self.async_show_form(step_id="user", errors={"base": "unknown"})

        return self.async_create_entry(title=unique_id, data=user_input)
