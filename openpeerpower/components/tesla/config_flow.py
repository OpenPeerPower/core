"""Tesla Config Flow."""
import logging

from teslajsonpy import Controller as TeslaAPI, TeslaException
import voluptuous as vol

from openpeerpower import config_entries, core, exceptions
from openpeerpower.const import (
    CONF_ACCESS_TOKEN,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_TOKEN,
    CONF_USERNAME,
    HTTP_UNAUTHORIZED,
)
from openpeerpower.core import callback
from openpeerpower.helpers import aiohttp_client, config_validation as cv

from .const import (
    CONF_WAKE_ON_START,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_WAKE_ON_START,
    MIN_SCAN_INTERVAL,
)
from .const import DOMAIN  # pylint:disable=unused-import

_LOGGER = logging.getLogger(__name__)


class TeslaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tesla."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize the tesla flow."""
        self.username = None

    async def async_step_import(self, import_config):
        """Import a config entry from configuration.yaml."""
        return await self.async_step_user(import_config)

    async def async_step_user(self, user_input=None):
        """Handle the start of the config flow."""
        errors = {}

        if user_input is not None:
            existing_entry = self._async_entry_for_username(user_input[CONF_USERNAME])
            if (
                existing_entry
                and existing_entry.data[CONF_PASSWORD] == user_input[CONF_PASSWORD]
            ):
                return self.async_abort(reason="already_configured")

            try:
                info = await validate_input(self.opp, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"

            if not errors:
                if existing_entry:
                    self.opp.config_entries.async_update_entry(
                        existing_entry, data=info
                    )
                    await self.opp.config_entries.async_reload(existing_entry.entry_id)
                    return self.async_abort(reason="reauth_successful")

                return self.async_create_entry(
                    title=user_input[CONF_USERNAME], data=info
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self._async_schema(),
            errors=errors,
            description_placeholders={},
        )

    async def async_step_reauth(self, data):
        """Handle configuration by re-auth."""
        self.username = data[CONF_USERNAME]
        return await self.async_step_user()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    @callback
    def _async_schema(self):
        """Fetch schema with defaults."""
        return vol.Schema(
            {
                vol.Required(CONF_USERNAME, default=self.username): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

    @callback
    def _async_entry_for_username(self, username):
        """Find an existing entry for a username."""
        for entry in self._async_current_entries():
            if entry.data.get(CONF_USERNAME) == username:
                return entry
        return None


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a option flow for Tesla."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): vol.All(cv.positive_int, vol.Clamp(min=MIN_SCAN_INTERVAL)),
                vol.Optional(
                    CONF_WAKE_ON_START,
                    default=self.config_entry.options.get(
                        CONF_WAKE_ON_START, DEFAULT_WAKE_ON_START
                    ),
                ): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=data_schema)


async def validate_input(opp: core.OpenPeerPower, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """

    config = {}
    websession = aiohttp_client.async_get_clientsession(opp)
    try:
        controller = TeslaAPI(
            websession,
            email=data[CONF_USERNAME],
            password=data[CONF_PASSWORD],
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        (config[CONF_TOKEN], config[CONF_ACCESS_TOKEN]) = await controller.connect(
            test_login=True
        )
        config[CONF_USERNAME] = data[CONF_USERNAME]
        config[CONF_PASSWORD] = data[CONF_PASSWORD]
    except TeslaException as ex:
        if ex.code == HTTP_UNAUTHORIZED:
            _LOGGER.error("Invalid credentials: %s", ex)
            raise InvalidAuth() from ex
        _LOGGER.error("Unable to communicate with Tesla API: %s", ex)
        raise CannotConnect() from ex
    _LOGGER.debug("Credentials successfully connected to the Tesla API")
    return config


class CannotConnect(exceptions.OpenPeerPowerError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.OpenPeerPowerError):
    """Error to indicate there is invalid auth."""
