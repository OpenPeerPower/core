"""Handler for Opp.io."""
import asyncio
import logging
import os

import aiohttp
import async_timeout

from openpeerpower.components.http import (
    CONF_SERVER_HOST,
    CONF_SERVER_PORT,
    CONF_SSL_CERTIFICATE,
)
from openpeerpower.const import HTTP_BAD_REQUEST, HTTP_OK, SERVER_PORT

from .const import X_OPPIO

_LOGGER = logging.getLogger(__name__)


class OppioAPIError(RuntimeError):
    """Return if a API trow a error."""


def _api_bool(funct):
    """Return a boolean."""

    async def _wrapper(*argv, **kwargs):
        """Wrap function."""
        try:
            data = await funct(*argv, **kwargs)
            return data["result"] == "ok"
        except OppioAPIError:
            return False

    return _wrapper


def api_data(funct):
    """Return data of an api."""

    async def _wrapper(*argv, **kwargs):
        """Wrap function."""
        data = await funct(*argv, **kwargs)
        if data["result"] == "ok":
            return data["data"]
        raise OppioAPIError(data["message"])

    return _wrapper


class OppIO:
    """Small API wrapper for Opp.io."""

    def __init__(self, loop, websession, ip):
        """Initialize Opp.io API."""
        self.loop = loop
        self.websession = websession
        self._ip = ip

    @_api_bool
    def is_connected(self):
        """Return true if it connected to Opp.io supervisor.

        This method return a coroutine.
        """
        return self.send_command("/supervisor/ping", method="get", timeout=15)

    @api_data
    def get_info(self):
        """Return generic Supervisor information.

        This method return a coroutine.
        """
        return self.send_command("/info", method="get")

    @api_data
    def get_host_info(self):
        """Return data for Host.

        This method return a coroutine.
        """
        return self.send_command("/host/info", method="get")

    @api_data
    def get_os_info(self):
        """Return data for the OS.

        This method return a coroutine.
        """
        return self.send_command("/os/info", method="get")

    @api_data
    def get_core_info(self):
        """Return data for Home Asssistant Core.

        This method returns a coroutine.
        """
        return self.send_command("/core/info", method="get")

    @api_data
    def get_supervisor_info(self):
        """Return data for the Supervisor.

        This method returns a coroutine.
        """
        return self.send_command("/supervisor/info", method="get")

    @api_data
    def get_addon_info(self, addon):
        """Return data for a Add-on.

        This method return a coroutine.
        """
        return self.send_command(f"/addons/{addon}/info", method="get")

    @api_data
    def get_ingress_panels(self):
        """Return data for Add-on ingress panels.

        This method return a coroutine.
        """
        return self.send_command("/ingress/panels", method="get")

    @_api_bool
    def restart_openpeerpower(self):
        """Restart Open-Peer-Power container.

        This method return a coroutine.
        """
        return self.send_command("/openpeerpower/restart")

    @_api_bool
    def stop_openpeerpower(self):
        """Stop Open-Peer-Power container.

        This method return a coroutine.
        """
        return self.send_command("/openpeerpower/stop")

    @api_data
    def retrieve_discovery_messages(self):
        """Return all discovery data from Opp.io API.

        This method return a coroutine.
        """
        return self.send_command("/discovery", method="get")

    @api_data
    def get_discovery_message(self, uuid):
        """Return a single discovery data message.

        This method return a coroutine.
        """
        return self.send_command(f"/discovery/{uuid}", method="get")

    @_api_bool
    async def update_opp_api(self, http_config, refresh_token):
        """Update Open Peer Power API data on Opp.io."""
        port = http_config.get(CONF_SERVER_PORT) or SERVER_PORT
        options = {
            "ssl": CONF_SSL_CERTIFICATE in http_config,
            "port": port,
            "watchdog": True,
            "refresh_token": refresh_token.token,
        }

        if http_config.get(CONF_SERVER_HOST) is not None:
            options["watchdog"] = False
            _LOGGER.warning(
                "Found incompatible HTTP option 'server_host'. Watchdog feature disabled"
            )

        return await self.send_command("/openpeerpower/options", payload=options)

    @_api_bool
    def update_opp_timezone(self, timezone):
        """Update Open-Peer-Power timezone data on Opp.io.

        This method return a coroutine.
        """
        return self.send_command("/supervisor/options", payload={"timezone": timezone})

    async def send_command(self, command, method="post", payload=None, timeout=10):
        """Send API command to Opp.io.

        This method is a coroutine.
        """
        try:
            with async_timeout.timeout(timeout):
                request = await self.websession.request(
                    method,
                    f"http://{self._ip}{command}",
                    json=payload,
                    headers={X_OPPIO: os.environ.get("OPPIO_TOKEN", "")},
                )

                if request.status not in (HTTP_OK, HTTP_BAD_REQUEST):
                    _LOGGER.error("%s return code %d", command, request.status)
                    raise OppioAPIError()

                answer = await request.json()
                return answer

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout on %s request", command)

        except aiohttp.ClientError as err:
            _LOGGER.error("Client error on %s request %s", command, err)

        raise OppioAPIError()
