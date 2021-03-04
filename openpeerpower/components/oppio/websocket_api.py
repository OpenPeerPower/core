"""Websocekt API handlers for the oppio integration."""
import logging

import voluptuous as vol

from openpeerpower.components import websocket_api
from openpeerpower.components.websocket_api.connection import ActiveConnection
from openpeerpower.core import OpenPeerPower, callback
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)

from .const import (
    ATTR_DATA,
    ATTR_ENDPOINT,
    ATTR_METHOD,
    ATTR_TIMEOUT,
    ATTR_WS_EVENT,
    DOMAIN,
    EVENT_SUPERVISOR_EVENT,
    WS_ID,
    WS_TYPE,
    WS_TYPE_API,
    WS_TYPE_EVENT,
    WS_TYPE_SUBSCRIBE,
)
from .handler import OppIO

SCHEMA_WEBSOCKET_EVENT = vol.Schema(
    {vol.Required(ATTR_WS_EVENT): cv.string},
    extra=vol.ALLOW_EXTRA,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)


@callback
def async_load_websocket_api(opp: OpenPeerPower):
    """Set up the websocket API."""
    websocket_api.async_register_command(opp, websocket_supervisor_event)
    websocket_api.async_register_command(opp, websocket_supervisor_api)
    websocket_api.async_register_command(opp, websocket_subscribe)


@websocket_api.require_admin
@websocket_api.async_response
@websocket_api.websocket_command({vol.Required(WS_TYPE): WS_TYPE_SUBSCRIBE})
async def websocket_subscribe(
    opp: OpenPeerPower, connection: ActiveConnection, msg: dict
):
    """Subscribe to supervisor events."""

    @callback
    def forward_messages(data):
        """Forward events to websocket."""
        connection.send_message(websocket_api.event_message(msg[WS_ID], data))

    connection.subscriptions[msg[WS_ID]] = async_dispatcher_connect(
        opp, EVENT_SUPERVISOR_EVENT, forward_messages
    )
    connection.send_message(websocket_api.result_message(msg[WS_ID]))


@websocket_api.async_response
@websocket_api.websocket_command(
    {
        vol.Required(WS_TYPE): WS_TYPE_EVENT,
        vol.Required(ATTR_DATA): SCHEMA_WEBSOCKET_EVENT,
    }
)
async def websocket_supervisor_event(
    opp: OpenPeerPower, connection: ActiveConnection, msg: dict
):
    """Publish events from the Supervisor."""
    async_dispatcher_send(opp, EVENT_SUPERVISOR_EVENT, msg[ATTR_DATA])
    connection.send_result(msg[WS_ID])


@websocket_api.require_admin
@websocket_api.async_response
@websocket_api.websocket_command(
    {
        vol.Required(WS_TYPE): WS_TYPE_API,
        vol.Required(ATTR_ENDPOINT): cv.string,
        vol.Required(ATTR_METHOD): cv.string,
        vol.Optional(ATTR_DATA): dict,
        vol.Optional(ATTR_TIMEOUT): vol.Any(cv.Number, None),
    }
)
async def websocket_supervisor_api(
    opp: OpenPeerPower, connection: ActiveConnection, msg: dict
):
    """Websocket handler to call Supervisor API."""
    supervisor: OppIO = opp.data[DOMAIN]
    result = False
    try:
        result = await supervisor.send_command(
            msg[ATTR_ENDPOINT],
            method=msg[ATTR_METHOD],
            timeout=msg.get(ATTR_TIMEOUT, 10),
            payload=msg.get(ATTR_DATA, {}),
        )
    except opp.components.oppio.OppioAPIError as err:
        _LOGGER.error("Failed to to call %s - %s", msg[ATTR_ENDPOINT], err)
        connection.send_error(
            msg[WS_ID], code=websocket_api.ERR_UNKNOWN_ERROR, message=str(err)
        )
    else:
        connection.send_result(msg[WS_ID], result.get(ATTR_DATA, {}))
