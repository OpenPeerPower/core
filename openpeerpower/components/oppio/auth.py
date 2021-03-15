"""Implement the auth feature from Opp.io for Add-ons."""
from ipaddress import ip_address
import logging
import os

from aiohttp import web
from aiohttp.web_exceptions import HTTPNotFound, HTTPUnauthorized
import voluptuous as vol

from openpeerpower.auth.models import User
from openpeerpower.auth.providers import openpeerpower as auth_op
from openpeerpower.components.http import OpenPeerPowerView
from openpeerpower.components.http.const import KEY_OPP_USER
from openpeerpower.components.http.data_validator import RequestDataValidator
from openpeerpower.const import HTTP_OK
from openpeerpower.core import callback
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.typing import OpenPeerPowerType

from .const import ATTR_ADDON, ATTR_PASSWORD, ATTR_USERNAME

_LOGGER = logging.getLogger(__name__)


@callback
def async_setup_auth_view(opp: OpenPeerPowerType, user: User):
    """Auth setup."""
    oppio_auth = OppIOAuth(opp, user)
    oppio_password_reset = OppIOPasswordReset(opp, user)

    opp.http.register_view(oppio_auth)
    opp.http.register_view(oppio_password_reset)


class OppIOBaseAuth(OpenPeerPowerView):
    """Opp.io view to handle auth requests."""

    def __init__(self, opp: OpenPeerPowerType, user: User):
        """Initialize WebView."""
        self.opp = opp
        self.user = user

    def _check_access(self, request: web.Request):
        """Check if this call is from Supervisor."""
        # Check caller IP
        oppio_ip = os.environ["OPPIO"].split(":")[0]
        if ip_address(request.transport.get_extra_info("peername")[0]) != ip_address(
            oppio_ip
        ):
            _LOGGER.error("Invalid auth request from %s", request.remote)
            raise HTTPUnauthorized()

        # Check caller token
        if request[KEY_OPP_USER].id != self.user.id:
            _LOGGER.error("Invalid auth request from %s", request[KEY_OPP_USER].name)
            raise HTTPUnauthorized()


class OppIOAuth(OppIOBaseAuth):
    """Opp.io view to handle auth requests."""

    name = "api:oppio:auth"
    url = "/api/oppio_auth"

    @RequestDataValidator(
        vol.Schema(
            {
                vol.Required(ATTR_USERNAME): cv.string,
                vol.Required(ATTR_PASSWORD): cv.string,
                vol.Required(ATTR_ADDON): cv.string,
            },
            extra=vol.ALLOW_EXTRA,
        )
    )
    async def post(self, request, data):
        """Handle auth requests."""
        self._check_access(request)
        provider = auth_op.async_get_provider(request.app["opp"])

        try:
            await provider.async_validate_login(
                data[ATTR_USERNAME], data[ATTR_PASSWORD]
            )
        except auth_op.InvalidAuth:
            raise HTTPNotFound() from None

        return web.Response(status=HTTP_OK)


class OppIOPasswordReset(OppIOBaseAuth):
    """Opp.io view to handle password reset requests."""

    name = "api:oppio:auth:password:reset"
    url = "/api/oppio_auth/password_reset"

    @RequestDataValidator(
        vol.Schema(
            {
                vol.Required(ATTR_USERNAME): cv.string,
                vol.Required(ATTR_PASSWORD): cv.string,
            },
            extra=vol.ALLOW_EXTRA,
        )
    )
    async def post(self, request, data):
        """Handle password reset requests."""
        self._check_access(request)
        provider = auth_op.async_get_provider(request.app["opp"])

        try:
            await provider.async_change_password(
                data[ATTR_USERNAME], data[ATTR_PASSWORD]
            )
        except auth_op.InvalidUser as err:
            raise HTTPNotFound() from err

        return web.Response(status=HTTP_OK)
