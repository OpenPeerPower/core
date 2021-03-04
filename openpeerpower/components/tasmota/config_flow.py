"""Config flow for Tasmota."""
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.components.mqtt import valid_subscribe_topic

from .const import CONF_DISCOVERY_PREFIX, DEFAULT_PREFIX, DOMAIN


class FlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    def __init__(self):
        """Initialize flow."""
        self._prefix = DEFAULT_PREFIX

    async def async_step_mqtt(self, discovery_info=None):
        """Handle a flow initialized by MQTT discovery."""
        if self._async_in_progress() or self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        await self.async_set_unique_id(DOMAIN)

        # Validate the topic, will throw if it fails
        prefix = discovery_info.subscribed_topic
        if prefix.endswith("/#"):
            prefix = prefix[:-2]
        try:
            valid_subscribe_topic(f"{prefix}/#")
        except vol.Invalid:
            return self.async_abort(reason="invalid_discovery_info")

        self._prefix = prefix

        return await self.async_step_confirm()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if self.show_advanced_options:
            return await self.async_step_config()
        return await self.async_step_confirm()

    async def async_step_config(self, user_input=None):
        """Confirm the setup."""
        errors = {}
        data = {CONF_DISCOVERY_PREFIX: self._prefix}

        if user_input is not None:
            bad_prefix = False
            prefix = user_input[CONF_DISCOVERY_PREFIX]
            if prefix.endswith("/#"):
                prefix = prefix[:-2]
            try:
                valid_subscribe_topic(f"{prefix}/#")
            except vol.Invalid:
                errors["base"] = "invalid_discovery_topic"
                bad_prefix = True
            else:
                data[CONF_DISCOVERY_PREFIX] = prefix
            if not bad_prefix:
                return self.async_create_entry(title="Tasmota", data=data)

        fields = {}
        fields[vol.Optional(CONF_DISCOVERY_PREFIX, default=self._prefix)] = str

        return self.async_show_form(
            step_id="config", data_schema=vol.Schema(fields), errors=errors
        )

    async def async_step_confirm(self, user_input=None):
        """Confirm the setup."""

        data = {CONF_DISCOVERY_PREFIX: self._prefix}

        if user_input is not None:
            return self.async_create_entry(title="Tasmota", data=data)

        return self.async_show_form(step_id="confirm")
