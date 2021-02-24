"""Config flow for Ruckus Unleashed integration."""
import logging

from pyruckus import Ruckus
from pyruckus.exceptions import AuthenticationError
import voluptuous as vol

from openpeerpower import config_entries, core, exceptions
from openpeerpower.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from .const import (  # pylint:disable=unused-import
    API_SERIAL,
    API_SYSTEM_OVERVIEW,
    DOMAIN,
)

_LOGGER = logging.getLogger(__package__)

DATA_SCHEMA = vol.Schema({"host": str, "username": str, "password": str})


def validate_input(opp: core.OpenPeerPower, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """

    try:
        ruckus = Ruckus(data[CONF_HOST], data[CONF_USERNAME], data[CONF_PASSWORD])
    except AuthenticationError as error:
        raise InvalidAuth from error
    except ConnectionError as error:
        raise CannotConnect from error

    mesh_name = ruckus.mesh_name()

    system_info = ruckus.system_info()
    try:
        host_serial = system_info[API_SYSTEM_OVERVIEW][API_SERIAL]
    except KeyError as error:
        raise CannotConnect from error

    return {
        "title": mesh_name,
        "serial": host_serial,
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ruckus Unleashed."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                info = await self.opp.async_add_executor_job(
                    validate_input, self.opp, user_input
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info["serial"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.OpenPeerPowerError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.OpenPeerPowerError):
    """Error to indicate there is invalid auth."""
