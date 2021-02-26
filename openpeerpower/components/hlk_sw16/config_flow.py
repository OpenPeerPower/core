"""Config flow for HLK-SW16."""
import asyncio

from hlk_sw16 import create_hlk_sw16_connection
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.const import CONF_HOST, CONF_PORT
from openpeerpower.core import OpenPeerPower

from .const import (
    CONNECTION_TIMEOUT,
    DEFAULT_KEEP_ALIVE_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_RECONNECT_INTERVAL,
    DOMAIN,
)
from .errors import AlreadyConfigured, CannotConnect

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
    }
)


async def connect_client(opp, user_input):
    """Connect the HLK-SW16 client."""
    client_aw = create_hlk_sw16_connection(
        host=user_input[CONF_HOST],
        port=user_input[CONF_PORT],
        loop=opp.loop,
        timeout=CONNECTION_TIMEOUT,
        reconnect_interval=DEFAULT_RECONNECT_INTERVAL,
        keep_alive_interval=DEFAULT_KEEP_ALIVE_INTERVAL,
    )
    return await asyncio.wait_for(client_aw, timeout=CONNECTION_TIMEOUT)


async def validate_input(opp: OpenPeerPower, user_input):
    """Validate the user input allows us to connect."""
    for entry in opp.config_entries.async_entries(DOMAIN):
        if (
            entry.data[CONF_HOST] == user_input[CONF_HOST]
            and entry.data[CONF_PORT] == user_input[CONF_PORT]
        ):
            raise AlreadyConfigured

    try:
        client = await connect_client(opp, user_input)
    except asyncio.TimeoutError as err:
        raise CannotConnect from err
    try:

        def disconnect_callback():
            if client.in_transaction:
                client.active_transaction.set_exception(CannotConnect)

        client.disconnect_callback = disconnect_callback
        await client.status()
    except CannotConnect:
        client.disconnect_callback = None
        client.stop()
        raise
    else:
        client.disconnect_callback = None
        client.stop()


class SW16FlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a HLK-SW16 config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_import(self, user_input):
        """Handle import."""
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                await validate_input(self.opp, user_input)
                address = f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                return self.async_create_entry(title=address, data=user_input)
            except AlreadyConfigured:
                errors["base"] = "already_configured"
            except CannotConnect:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
