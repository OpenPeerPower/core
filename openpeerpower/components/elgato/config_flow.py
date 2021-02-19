"""Config flow to configure the Elgato Key Light integration."""
from __future__ import annotations

from typing import Any, Dict

from elgato import Elgato, ElgatoError
import voluptuous as vol

from openpeerpower.config_entries import CONN_CLASS_LOCAL_POLL, ConfigFlow
from openpeerpower.const import CONF_HOST, CONF_PORT
from openpeerpower.core import callback
from openpeerpower.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_SERIAL_NUMBER, DOMAIN  # pylint: disable=unused-import


class ElgatoFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a Elgato Key Light config flow."""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_LOCAL_POLL

    host: str
    port: int
    serial_number: str

    async def async_step_user(
        self, user_input: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """Handle a flow initiated by the user."""
        if user_input is None:
            return self._async_show_setup_form()

        self.host = user_input[CONF_HOST]
        self.port = user_input[CONF_PORT]

        try:
            await self._get_elgato_serial_number(raise_on_progress=False)
        except ElgatoError:
            return self._async_show_setup_form({"base": "cannot_connect"})

        return self._async_create_entry()

    async def async_step_zeroconf(
        self, discovery_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle zeroconf discovery."""
        self.host = discovery_info[CONF_HOST]
        self.port = discovery_info[CONF_PORT]

        try:
            await self._get_elgato_serial_number()
        except ElgatoError:
            return self.async_abort(reason="cannot_connect")

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={"serial_number": self.serial_number},
        )

    async def async_step_zeroconf_confirm(
        self, _: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """Handle a flow initiated by zeroconf."""
        return self._async_create_entry()

    @callback
    def _async_show_setup_form(
        self, errors: Dict[str, str] | None = None
    ) -> Dict[str, Any]:
        """Show the setup form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=9123): int,
                }
            ),
            errors=errors or {},
        )

    @callback
    def _async_create_entry(self) -> Dict[str, Any]:
        return self.async_create_entry(
            title=self.serial_number,
            data={
                CONF_HOST: self.host,
                CONF_PORT: self.port,
                CONF_SERIAL_NUMBER: self.serial_number,
            },
        )

    async def _get_elgato_serial_number(self, raise_on_progress: bool = True) -> None:
        """Get device information from an Elgato Key Light device."""
        session = async_get_clientsession(self.opp)
        elgato = Elgato(
            host=self.host,
            port=self.port,
            session=session,
        )
        info = await elgato.info()

        # Check if already configured
        await self.async_set_unique_id(
            info.serial_number, raise_on_progress=raise_on_progress
        )
        self._abort_if_unique_id_configured(
            updates={CONF_HOST: self.host, CONF_PORT: self.port}
        )

        self.serial_number = info.serial_number
