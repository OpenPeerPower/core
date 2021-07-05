"""WebSocket based API for Open Peer Power."""
from __future__ import annotations

from typing import Final, cast

import voluptuous as vol

from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers.typing import ConfigType
from openpeerpower.loader import bind_opp

from . import commands, connection, const, decorators, http, messages  # noqa: F401
from .connection import ActiveConnection  # noqa: F401
from .const import (  # noqa: F401
    ERR_OPENPEERPOWER_ERROR,
    ERR_INVALID_FORMAT,
    ERR_NOT_FOUND,
    ERR_NOT_SUPPORTED,
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

DOMAIN: Final = const.DOMAIN

DEPENDENCIES: Final[tuple[str]] = ("http",)


@bind_opp
@callback
def async_register_command(
    opp: OpenPeerPower,
    command_or_handler: str | const.WebSocketCommandHandler,
    handler: const.WebSocketCommandHandler | None = None,
    schema: vol.Schema | None = None,
) -> None:
    """Register a websocket command."""
    # pylint: disable=protected-access
    if handler is None:
        handler = cast(const.WebSocketCommandHandler, command_or_handler)
        command = handler._ws_command  # type: ignore[attr-defined]
        schema = handler._ws_schema  # type: ignore[attr-defined]
    else:
        command = command_or_handler
    handlers = opp.data.get(DOMAIN)
    if handlers is None:
        handlers = opp.data[DOMAIN] = {}
    handlers[command] = (handler, schema)


async def async_setup(opp: OpenPeerPower, config: ConfigType) -> bool:
    """Initialize the websocket API."""
    opp.http.register_view(http.WebsocketAPIView())
    commands.async_register_commands(opp, async_register_command)
    return True
