"""Config flow for Shelly integration."""
import asyncio
import logging

import aiohttp
import aioshelly
import async_timeout
import voluptuous as vol

from openpeerpower import config_entries, core
from openpeerpower.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    HTTP_UNAUTHORIZED,
)
from openpeerpower.helpers import aiohttp_client

from .const import AIOSHELLY_DEVICE_TIMEOUT_SEC
from .const import DOMAIN  # pylint:disable=unused-import
from .utils import get_coap_context, get_device_sleep_period

_LOGGER = logging.getLogger(__name__)

HOST_SCHEMA = vol.Schema({vol.Required(CONF_HOST): str})

HTTP_CONNECT_ERRORS = (asyncio.TimeoutError, aiohttp.ClientError)


async def validate_input(opp: core.OpenPeerPower, host, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """

    options = aioshelly.ConnectionOptions(
        host, data.get(CONF_USERNAME), data.get(CONF_PASSWORD)
    )
    coap_context = await get_coap_context(opp)

    async with async_timeout.timeout(AIOSHELLY_DEVICE_TIMEOUT_SEC):
        device = await aioshelly.Device.create(
            aiohttp_client.async_get_clientsession(opp),
            coap_context,
            options,
        )

    device.shutdown()

    # Return info that you want to store in the config entry.
    return {
        "title": device.settings["name"],
        "hostname": device.settings["device"]["hostname"],
        "sleep_period": get_device_sleep_period(device.settings),
        "model": device.settings["device"]["type"],
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Shelly."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH
    host = None
    info = None
    device_info = None

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            try:
                info = await self._async_get_info(host)
            except HTTP_CONNECT_ERRORS:
                errors["base"] = "cannot_connect"
            except aioshelly.FirmwareUnsupported:
                return self.async_abort(reason="unsupported_firmware")
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info["mac"])
                self._abort_if_unique_id_configured({CONF_HOST: host})
                self.host = host
                if info["auth"]:
                    return await self.async_step_credentials()

                try:
                    device_info = await validate_input(self.opp, self.host, {})
                except HTTP_CONNECT_ERRORS:
                    errors["base"] = "cannot_connect"
                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"
                else:
                    return self.async_create_entry(
                        title=device_info["title"] or device_info["hostname"],
                        data={
                            **user_input,
                            "sleep_period": device_info["sleep_period"],
                            "model": device_info["model"],
                        },
                    )

        return self.async_show_form(
            step_id="user", data_schema=HOST_SCHEMA, errors=errors
        )

    async def async_step_credentials(self, user_input=None):
        """Handle the credentials step."""
        errors = {}
        if user_input is not None:
            try:
                device_info = await validate_input(self.opp, self.host, user_input)
            except aiohttp.ClientResponseError as error:
                if error.status == HTTP_UNAUTHORIZED:
                    errors["base"] = "invalid_auth"
                else:
                    errors["base"] = "cannot_connect"
            except HTTP_CONNECT_ERRORS:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=device_info["title"] or device_info["hostname"],
                    data={
                        **user_input,
                        CONF_HOST: self.host,
                        "sleep_period": device_info["sleep_period"],
                        "model": device_info["model"],
                    },
                )
        else:
            user_input = {}

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME, default=user_input.get(CONF_USERNAME)): str,
                vol.Required(CONF_PASSWORD, default=user_input.get(CONF_PASSWORD)): str,
            }
        )

        return self.async_show_form(
            step_id="credentials", data_schema=schema, errors=errors
        )

    async def async_step_zeroconf(self, zeroconf_info):
        """Handle zeroconf discovery."""
        try:
            self.info = info = await self._async_get_info(zeroconf_info["host"])
        except HTTP_CONNECT_ERRORS:
            return self.async_abort(reason="cannot_connect")
        except aioshelly.FirmwareUnsupported:
            return self.async_abort(reason="unsupported_firmware")

        await self.async_set_unique_id(info["mac"])
        self._abort_if_unique_id_configured({CONF_HOST: zeroconf_info["host"]})
        self.host = zeroconf_info["host"]

        if not info["auth"] and info.get("sleep_mode", False):
            try:
                self.device_info = await validate_input(self.opp, self.host, {})
            except HTTP_CONNECT_ERRORS:
                return self.async_abort(reason="cannot_connect")

        self.context["title_placeholders"] = {
            "name": zeroconf_info.get("name", "").split(".")[0]
        }
        return await self.async_step_confirm_discovery()

    async def async_step_confirm_discovery(self, user_input=None):
        """Handle discovery confirm."""
        errors = {}
        if user_input is not None:
            if self.info["auth"]:
                return await self.async_step_credentials()

            if self.device_info:
                return self.async_create_entry(
                    title=self.device_info["title"] or self.device_info["hostname"],
                    data={
                        "host": self.host,
                        "sleep_period": self.device_info["sleep_period"],
                        "model": self.device_info["model"],
                    },
                )

            try:
                device_info = await validate_input(self.opp, self.host, {})
            except HTTP_CONNECT_ERRORS:
                errors["base"] = "cannot_connect"
            except aioshelly.AuthRequired:
                return await self.async_step_credentials()
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=device_info["title"] or device_info["hostname"],
                    data={
                        "host": self.host,
                        "sleep_period": device_info["sleep_period"],
                        "model": device_info["model"],
                    },
                )

        return self.async_show_form(
            step_id="confirm_discovery",
            description_placeholders={
                "model": aioshelly.MODEL_NAMES.get(
                    self.info["type"], self.info["type"]
                ),
                "host": self.host,
            },
            errors=errors,
        )

    async def _async_get_info(self, host):
        """Get info from shelly device."""
        async with async_timeout.timeout(AIOSHELLY_DEVICE_TIMEOUT_SEC):
            return await aioshelly.get_info(
                aiohttp_client.async_get_clientsession(self.opp),
                host,
            )
