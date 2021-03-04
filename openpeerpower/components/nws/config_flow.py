"""Config flow for National Weather Service (NWS) integration."""
import logging

import aiohttp
from pynws import SimpleNWS
import voluptuous as vol

from openpeerpower import config_entries, core, exceptions
from openpeerpower.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.aiohttp_client import async_get_clientsession

from . import base_unique_id
from .const import CONF_STATION, DOMAIN  # pylint:disable=unused-import

_LOGGER = logging.getLogger(__name__)


async def validate_input(opp: core.OpenPeerPower, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    latitude = data[CONF_LATITUDE]
    longitude = data[CONF_LONGITUDE]
    api_key = data[CONF_API_KEY]
    station = data.get(CONF_STATION)

    client_session = async_get_clientsession(opp)
    ha_api_key = f"{api_key} openpeerpower"
    nws = SimpleNWS(latitude, longitude, ha_api_key, client_session)

    try:
        await nws.set_station(station)
    except aiohttp.ClientError as err:
        _LOGGER.error("Could not connect: %s", err)
        raise CannotConnect from err

    return {"title": nws.station}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for National Weather Service (NWS)."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(
                base_unique_id(user_input[CONF_LATITUDE], user_input[CONF_LONGITUDE])
            )
            self._abort_if_unique_id_configured()
            try:
                info = await validate_input(self.opp, user_input)
                user_input[CONF_STATION] = info["title"]
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Required(
                    CONF_LATITUDE, default=self.opp.config.latitude
                ): cv.latitude,
                vol.Required(
                    CONF_LONGITUDE, default=self.opp.config.longitude
                ): cv.longitude,
                vol.Optional(CONF_STATION): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )


class CannotConnect(exceptions.OpenPeerPowerError):
    """Error to indicate we cannot connect."""
