"""WebSocket based API for Open Peer Power."""
from typing import Optional, Union, cast

import voluptuous as vol

from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.loader import bind_opp

from . import commands, connection, const, decorators, http, messages  # noqa: F401
from .connection import ActiveConnection  # noqa: F401
from .const import (  # noqa: F401
    ERR_INVALID_FORMAT,
    ERR_NOT_FOUND,
    ERR_NOT_SUPPORTED,
    ERR_OPEN_PEER_POWER_ERROR,
    ERR_TEMPLATE_ERROR,
    ERR_TIMEOUT,
    ERR_UNAUTHORIZED,
    ERR_UNKNOWN_COMMAND,
    ERR_UNKNOWN_ERROR,
)
from .decorators import (  # noqa: F401
    async_response,
    require_admin,
    websocket_command,
    ws_require_user,
)
from .messages import (  # noqa: F401
    BASE_COMMAND_MESSAGE_SCHEMA,
    error_message,
    event_message,
    result_message,
)

# mypy: allow-untyped-calls, allow-untyped-defs

DOMAIN = const.DOMAIN

DEPENDENCIES = ("http",)


@bind_opp
@callback
def async_register_command(
    opp: OpenPeerPower,
    command_or_handler: Union[str, const.WebSocketCommandHandler],
    handler: Optional[const.WebSocketCommandHandler] = None,
    schema: Optional[vol.Schema] = None,
) -> None:
    """Register a websocket command."""
    # pylint: disable=protected-access
    if handler is None:
        handler = cast(const.WebSocketCommandHandler, command_or_handler)
        command = handler._ws_command  # type: ignore
        schema = handler._ws_schema  # type: ignore
    else:
        command = command_or_handler
    handlers = opp.data.get(DOMAIN)
    if handlers is None:
        handlers = opp.data[DOMAIN] = {}
    handlers[command] = (handler, schema)


async def async_setup(opp, config):
    """Initialize the websocket API."""
    opp.http.register_view(http.WebsocketAPIView)
    commands.async_register_commands(opp, async_register_command)
    return True
