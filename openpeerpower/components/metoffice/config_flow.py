"""Config flow for Met Office integration."""
import logging

import voluptuous as vol

from openpeerpower import config_entries, core, exceptions
from openpeerpower.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from openpeerpower.helpers import config_validation as cv

from .const import DOMAIN  # pylint: disable=unused-import
from .data import MetOfficeData

_LOGGER = logging.getLogger(__name__)


async def validate_input(opp: core.OpenPeerPower, data):
    """Validate that the user input allows us to connect to DataPoint.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    latitude = data[CONF_LATITUDE]
    longitude = data[CONF_LONGITUDE]
    api_key = data[CONF_API_KEY]

    metoffice_data = MetOfficeData(opp, api_key, latitude, longitude)
    await metoffice_data.async_update_site()
    if metoffice_data.site_name is None:
        raise CannotConnect()

    return {"site_name": metoffice_data.site_name}


class MetOfficeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Met Office weather integration."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_LATITUDE]}_{user_input[CONF_LONGITUDE]}"
            )
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.opp, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                user_input[CONF_NAME] = info["site_name"]
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Required(
                    CONF_LATITUDE, default=self.opp.config.latitude
                ): cv.latitude,
                vol.Required(
                    CONF_LONGITUDE, default=self.opp.config.longitude
                ): cv.longitude,
            },
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )


class CannotConnect(exceptions.OpenPeerPowerError):
    """Error to indicate we cannot connect."""
