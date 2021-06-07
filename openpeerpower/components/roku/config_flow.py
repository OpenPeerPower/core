"""Config flow for Roku."""
from __future__ import annotations

import logging
from urllib.parse import urlparse

from rokuecp import Roku, RokuError
import voluptuous as vol

from openpeerpower.components.ssdp import (
    ATTR_SSDP_LOCATION,
    ATTR_UPNP_FRIENDLY_NAME,
    ATTR_UPNP_SERIAL,
)
from openpeerpower.config_entries import ConfigFlow
from openpeerpower.const import CONF_HOST, CONF_NAME
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.data_entry_flow import FlowResult
from openpeerpower.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

DATA_SCHEMA = vol.Schema({vol.Required(CONF_HOST): str})

ERROR_CANNOT_CONNECT = "cannot_connect"
ERROR_UNKNOWN = "unknown"

_LOGGER = logging.getLogger(__name__)


async def validate_input(opp: OpenPeerPower, data: dict) -> dict:
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    session = async_get_clientsession(opp)
    roku = Roku(data[CONF_HOST], session=session)
    device = await roku.update()

    return {
        "title": device.info.name,
        "serial_number": device.info.serial_number,
    }


class RokuConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a Roku config flow."""

    VERSION = 1

    def __init__(self):
        """Set up the instance."""
        self.discovery_info = {}

    @callback
    def _show_form(self, errors: dict | None = None) -> FlowResult:
        """Show the form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors or {},
        )

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle a flow initialized by the user."""
        if not user_input:
            return self._show_form()

        errors = {}

        try:
            info = await validate_input(self.opp, user_input)
        except RokuError:
            _LOGGER.debug("Roku Error", exc_info=True)
            errors["base"] = ERROR_CANNOT_CONNECT
            return self._show_form(errors)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unknown error trying to connect")
            return self.async_abort(reason=ERROR_UNKNOWN)

        await self.async_set_unique_id(info["serial_number"])
        self._abort_if_unique_id_configured(updates={CONF_HOST: user_input[CONF_HOST]})

        return self.async_create_entry(title=info["title"], data=user_input)

    async def async_step_homekit(self, discovery_info):
        """Handle a flow initialized by homekit discovery."""

        # If we already have the host configured do
        # not open connections to it if we can avoid it.
        self._async_abort_entries_match({CONF_HOST: discovery_info[CONF_HOST]})

        self.discovery_info.update({CONF_HOST: discovery_info[CONF_HOST]})

        try:
            info = await validate_input(self.opp, self.discovery_info)
        except RokuError:
            _LOGGER.debug("Roku Error", exc_info=True)
            return self.async_abort(reason=ERROR_CANNOT_CONNECT)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unknown error trying to connect")
            return self.async_abort(reason=ERROR_UNKNOWN)

        await self.async_set_unique_id(info["serial_number"])
        self._abort_if_unique_id_configured(
            updates={CONF_HOST: discovery_info[CONF_HOST]},
        )

        self.context.update({"title_placeholders": {"name": info["title"]}})
        self.discovery_info.update({CONF_NAME: info["title"]})

        return await self.async_step_discovery_confirm()

    async def async_step_ssdp(self, discovery_info: dict | None = None) -> FlowResult:
        """Handle a flow initialized by discovery."""
        host = urlparse(discovery_info[ATTR_SSDP_LOCATION]).hostname
        name = discovery_info[ATTR_UPNP_FRIENDLY_NAME]
        serial_number = discovery_info[ATTR_UPNP_SERIAL]

        await self.async_set_unique_id(serial_number)
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})

        self.context.update({"title_placeholders": {"name": name}})

        self.discovery_info.update({CONF_HOST: host, CONF_NAME: name})

        try:
            await validate_input(self.opp, self.discovery_info)
        except RokuError:
            _LOGGER.debug("Roku Error", exc_info=True)
            return self.async_abort(reason=ERROR_CANNOT_CONNECT)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unknown error trying to connect")
            return self.async_abort(reason=ERROR_UNKNOWN)

        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Handle user-confirmation of discovered device."""
        if user_input is None:
            return self.async_show_form(
                step_id="discovery_confirm",
                description_placeholders={"name": self.discovery_info[CONF_NAME]},
                errors={},
            )

        return self.async_create_entry(
            title=self.discovery_info[CONF_NAME],
            data=self.discovery_info,
        )
