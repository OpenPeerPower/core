"""Config flow for Yeelight integration."""
import logging

import voluptuous as vol
import yeelight

from openpeerpower import config_entries, exceptions
from openpeerpower.components.dhcp import IP_ADDRESS
from openpeerpower.const import CONF_DEVICE, CONF_HOST, CONF_ID, CONF_NAME
from openpeerpower.core import callback
import openpeerpower.helpers.config_validation as cv

from . import (
    CONF_MODE_MUSIC,
    CONF_MODEL,
    CONF_NIGHTLIGHT_SWITCH,
    CONF_NIGHTLIGHT_SWITCH_TYPE,
    CONF_SAVE_ON_CHANGE,
    CONF_TRANSITION,
    DOMAIN,
    NIGHTLIGHT_SWITCH_TYPE_LIGHT,
    _async_unique_name,
)

MODEL_UNKNOWN = "unknown"

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Yeelight."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow."""
        return OptionsFlowHandler(config_entry)

    def __init__(self):
        """Initialize the config flow."""
        self._discovered_devices = {}
        self._discovered_model = None
        self._discovered_ip = None

    async def async_step_homekit(self, discovery_info):
        """Handle discovery from homekit."""
        self._discovered_ip = discovery_info["host"]
        return await self._async_handle_discovery()

    async def async_step_dhcp(self, discovery_info):
        """Handle discovery from dhcp."""
        self._discovered_ip = discovery_info[IP_ADDRESS]
        return await self._async_handle_discovery()

    async def _async_handle_discovery(self):
        """Handle any discovery."""
        self.context[CONF_HOST] = self._discovered_ip
        for progress in self._async_in_progress():
            if progress.get("context", {}).get(CONF_HOST) == self._discovered_ip:
                return self.async_abort(reason="already_in_progress")

        try:
            self._discovered_model = await self._async_try_connect(self._discovered_ip)
        except CannotConnect:
            return self.async_abort(reason="cannot_connect")

        if not self.unique_id:
            return self.async_abort(reason="cannot_connect")

        self._abort_if_unique_id_configured(
            updates={CONF_HOST: self._discovered_ip}, reload_on_update=False
        )
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(self, user_input=None):
        """Confirm discovery."""
        if user_input is not None:
            return self.async_create_entry(
                title=f"{self._discovered_model} {self.unique_id}",
                data={CONF_ID: self.unique_id, CONF_HOST: self._discovered_ip},
            )

        self._set_confirm_only()
        placeholders = {"model": self._discovered_model, "host": self._discovered_ip}
        self.context["title_placeholders"] = placeholders
        return self.async_show_form(
            step_id="discovery_confirm", description_placeholders=placeholders
        )

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            if not user_input.get(CONF_HOST):
                return await self.async_step_pick_device()
            try:
                model = await self._async_try_connect(user_input[CONF_HOST])
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"{model} {self.unique_id}", data=user_input
                )

        user_input = user_input or {}
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Optional(CONF_HOST, default=user_input.get(CONF_HOST, "")): str}
            ),
            errors=errors,
        )

    async def async_step_pick_device(self, user_input=None):
        """Handle the step to pick discovered device."""
        if user_input is not None:
            unique_id = user_input[CONF_DEVICE]
            capabilities = self._discovered_devices[unique_id]
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=_async_unique_name(capabilities), data={CONF_ID: unique_id}
            )

        configured_devices = {
            entry.data[CONF_ID]
            for entry in self._async_current_entries()
            if entry.data[CONF_ID]
        }
        devices_name = {}
        # Run 3 times as packets can get lost
        for _ in range(3):
            devices = await self.opp.async_add_executor_job(yeelight.discover_bulbs)
            for device in devices:
                capabilities = device["capabilities"]
                unique_id = capabilities["id"]
                if unique_id in configured_devices:
                    continue  # ignore configured devices
                model = capabilities["model"]
                host = device["ip"]
                name = f"{host} {model} {unique_id}"
                self._discovered_devices[unique_id] = capabilities
                devices_name[unique_id] = name

        # Check if there is at least one device
        if not devices_name:
            return self.async_abort(reason="no_devices_found")
        return self.async_show_form(
            step_id="pick_device",
            data_schema=vol.Schema({vol.Required(CONF_DEVICE): vol.In(devices_name)}),
        )

    async def async_step_import(self, user_input=None):
        """Handle import step."""
        host = user_input[CONF_HOST]
        try:
            await self._async_try_connect(host)
        except CannotConnect:
            _LOGGER.error("Failed to import %s: cannot connect", host)
            return self.async_abort(reason="cannot_connect")
        if CONF_NIGHTLIGHT_SWITCH_TYPE in user_input:
            user_input[CONF_NIGHTLIGHT_SWITCH] = (
                user_input.pop(CONF_NIGHTLIGHT_SWITCH_TYPE)
                == NIGHTLIGHT_SWITCH_TYPE_LIGHT
            )
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

    async def _async_try_connect(self, host):
        """Set up with options."""
        self._async_abort_entries_match({CONF_HOST: host})

        bulb = yeelight.Bulb(host)
        try:
            capabilities = await self.opp.async_add_executor_job(bulb.get_capabilities)
            if capabilities is None:  # timeout
                _LOGGER.debug("Failed to get capabilities from %s: timeout", host)
            else:
                _LOGGER.debug("Get capabilities: %s", capabilities)
                await self.async_set_unique_id(capabilities["id"])
                return capabilities["model"]
        except OSError as err:
            _LOGGER.debug("Failed to get capabilities from %s: %s", host, err)
            # Ignore the error since get_capabilities uses UDP discovery packet
            # which does not work in all network environments

        # Fallback to get properties
        try:
            await self.opp.async_add_executor_job(bulb.get_properties)
        except yeelight.BulbException as err:
            _LOGGER.error("Failed to get properties from %s: %s", host, err)
            raise CannotConnect from err
        _LOGGER.debug("Get properties: %s", bulb.last_properties)
        return MODEL_UNKNOWN


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a option flow for Yeelight."""

    def __init__(self, config_entry):
        """Initialize the option flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            options = {**self._config_entry.options}
            options.update(user_input)
            return self.async_create_entry(title="", data=options)

        options = self._config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_MODEL, default=options[CONF_MODEL]): str,
                    vol.Required(
                        CONF_TRANSITION, default=options[CONF_TRANSITION]
                    ): cv.positive_int,
                    vol.Required(
                        CONF_MODE_MUSIC, default=options[CONF_MODE_MUSIC]
                    ): bool,
                    vol.Required(
                        CONF_SAVE_ON_CHANGE, default=options[CONF_SAVE_ON_CHANGE]
                    ): bool,
                    vol.Required(
                        CONF_NIGHTLIGHT_SWITCH, default=options[CONF_NIGHTLIGHT_SWITCH]
                    ): bool,
                }
            ),
        )


class CannotConnect(exceptions.OpenPeerPowerError):
    """Error to indicate we cannot connect."""
