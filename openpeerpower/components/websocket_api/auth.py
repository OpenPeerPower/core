"""Handle the auth of a connection."""
import voluptuous as vol
from voluptuous.humanize import humanize_error

from openpeerpower.auth.models import RefreshToken, User
from openpeerpower.components.http.ban import process_success_login, process_wrong_login
from openpeerpower.const import __version__

from .connection import ActiveConnection
from .error import Disconnect

# mypy: allow-untyped-calls, allow-untyped-defs

TYPE_AUTH = "auth"
TYPE_AUTH_INVALID = "auth_invalid"
TYPE_AUTH_OK = "auth_ok"
TYPE_AUTH_REQUIRED = "auth_required"

AUTH_MESSAGE_SCHEMA = vol.Schema(
    {
        vol.Required("type"): TYPE_AUTH,
        vol.Exclusive("api_password", "auth"): str,
        vol.Exclusive("access_token", "auth"): str,
    }
)


def auth_ok_message():
    """Return an auth_ok message."""
    return {"type": TYPE_AUTH_OK, "ha_version": __version__}


def auth_required_message():
    """Return an auth_required message."""
    return {"type": TYPE_AUTH_REQUIRED, "ha_version": __version__}


def auth_invalid_message(message):
    """Return an auth_invalid message."""
    return {"type": TYPE_AUTH_INVALID, "message": message}


class AuthPhase:
    """Connection that requires client to authenticate first."""

    def __init__(self, logger, opp, send_message, request):
        """Initialize the authentiated connection."""
        self._opp = opp
        self._send_message = send_message
        self._logger = logger
        self._request = request
        self._authenticated = False
        self._connection = None

    async def async_handle(self, msg):
        """Handle authentication."""
        try:
            msg = AUTH_MESSAGE_SCHEMA(msg)
        except vol.Invalid as err:
            error_msg = (
                f"Auth message incorrectly formatted: {humanize_error(msg, err)}"
            )
            self._logger.warning(error_msg)
            self._send_message(auth_invalid_message(error_msg))
            raise Disconnect from err

        if "access_token" in msg:
            self._logger.debug("Received access_token")
            refresh_token = await self._opp.auth.async_validate_access_token(
                msg["access_token"]
            )
            if refresh_token is not None:
                return await self._async_finish_auth(refresh_token.user, refresh_token)

        self._send_message(auth_invalid_message("Invalid access token or password"))
        await process_wrong_login(self._request)
        raise Disconnect

    async def _async_finish_auth(
        self, user: User, refresh_token: RefreshToken
    ) -> ActiveConnection:
        """Create an active connection."""
        self._logger.debug("Auth OK")
        await process_success_login(self._request)
        self._send_message(auth_ok_message())
        return ActiveConnection(
            self._logger, self._opp, self._send_message, user, refresh_token
        )
