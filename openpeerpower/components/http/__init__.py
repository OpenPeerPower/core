"""Support to serve the Open Peer Power API as WSGI application."""
from contextvars import ContextVar
from ipaddress import ip_network
import logging
import os
import ssl
from typing import Dict, Optional, cast

from aiohttp import web
from aiohttp.web_exceptions import HTTPMovedPermanently
import voluptuous as vol

from openpeerpower.const import (
    EVENT_OPENPEERPOWER_START,
    EVENT_OPENPEERPOWER_STOP,
    SERVER_PORT,
)
from openpeerpower.core import Event, OpenPeerPower
from openpeerpower.helpers import storage
import openpeerpower.helpers.config_validation as cv
from openpeerpower.loader import bind_opp
from openpeerpower.setup import ATTR_COMPONENT, EVENT_COMPONENT_LOADED
import openpeerpower.util as opp_util
from openpeerpower.util import ssl as ssl_util

from .auth import setup_auth
from .ban import setup_bans
from .const import KEY_AUTHENTICATED, KEY_OPP, KEY_OPP_USER  # noqa: F401
from .cors import setup_cors
from .forwarded import async_setup_forwarded
from .request_context import setup_request_context
from .security_filter import setup_security_filter
from .static import CACHE_HEADERS, CachingStaticResource
from .view import OpenPeerPowerView  # noqa: F401
from .web_runner import OpenPeerPowerTCPSite

# mypy: allow-untyped-defs, no-check-untyped-defs

DOMAIN = "http"

CONF_SERVER_HOST = "server_host"
CONF_SERVER_PORT = "server_port"
CONF_BASE_URL = "base_url"
CONF_SSL_CERTIFICATE = "ssl_certificate"
CONF_SSL_PEER_CERTIFICATE = "ssl_peer_certificate"
CONF_SSL_KEY = "ssl_key"
CONF_CORS_ORIGINS = "cors_allowed_origins"
CONF_USE_X_FORWARDED_FOR = "use_x_forwarded_for"
CONF_TRUSTED_PROXIES = "trusted_proxies"
CONF_LOGIN_ATTEMPTS_THRESHOLD = "login_attempts_threshold"
CONF_IP_BAN_ENABLED = "ip_ban_enabled"
CONF_SSL_PROFILE = "ssl_profile"

SSL_MODERN = "modern"
SSL_INTERMEDIATE = "intermediate"

_LOGGER = logging.getLogger(__name__)

DEFAULT_DEVELOPMENT = "0"
# Cast to be able to load custom cards.
# My to be able to check url and version info.
DEFAULT_CORS = ["https://cast.openpeerpower.io"]
NO_LOGIN_ATTEMPT_THRESHOLD = -1

MAX_CLIENT_SIZE: int = 1024 ** 2 * 16

STORAGE_KEY = DOMAIN
STORAGE_VERSION = 1


HTTP_SCHEMA = vol.All(
    cv.deprecated(CONF_BASE_URL),
    vol.Schema(
        {
            vol.Optional(CONF_SERVER_HOST): vol.All(
                cv.ensure_list, vol.Length(min=1), [cv.string]
            ),
            vol.Optional(CONF_SERVER_PORT, default=SERVER_PORT): cv.port,
            vol.Optional(CONF_BASE_URL): cv.string,
            vol.Optional(CONF_SSL_CERTIFICATE): cv.isfile,
            vol.Optional(CONF_SSL_PEER_CERTIFICATE): cv.isfile,
            vol.Optional(CONF_SSL_KEY): cv.isfile,
            vol.Optional(CONF_CORS_ORIGINS, default=DEFAULT_CORS): vol.All(
                cv.ensure_list, [cv.string]
            ),
            vol.Inclusive(CONF_USE_X_FORWARDED_FOR, "proxy"): cv.boolean,
            vol.Inclusive(CONF_TRUSTED_PROXIES, "proxy"): vol.All(
                cv.ensure_list, [ip_network]
            ),
            vol.Optional(
                CONF_LOGIN_ATTEMPTS_THRESHOLD, default=NO_LOGIN_ATTEMPT_THRESHOLD
            ): vol.Any(cv.positive_int, NO_LOGIN_ATTEMPT_THRESHOLD),
            vol.Optional(CONF_IP_BAN_ENABLED, default=True): cv.boolean,
            vol.Optional(CONF_SSL_PROFILE, default=SSL_MODERN): vol.In(
                [SSL_INTERMEDIATE, SSL_MODERN]
            ),
        }
    ),
)

CONFIG_SCHEMA = vol.Schema({DOMAIN: HTTP_SCHEMA}, extra=vol.ALLOW_EXTRA)


@bind_opp
async def async_get_last_config(opp: OpenPeerPower) -> Optional[dict]:
    """Return the last known working config."""
    store = storage.Store(opp, STORAGE_VERSION, STORAGE_KEY)
    return cast(Optional[dict], await store.async_load())


class ApiConfig:
    """Configuration settings for API server."""

    def __init__(
        self,
        local_ip: str,
        host: str,
        port: Optional[int] = SERVER_PORT,
        use_ssl: bool = False,
    ) -> None:
        """Initialize a new API config object."""
        self.local_ip = local_ip
        self.host = host
        self.port = port
        self.use_ssl = use_ssl


async def async_setup(opp, config):
    """Set up the HTTP API and debug interface."""
    conf = config.get(DOMAIN)

    if conf is None:
        conf = HTTP_SCHEMA({})

    server_host = conf.get(CONF_SERVER_HOST)
    server_port = conf[CONF_SERVER_PORT]
    ssl_certificate = conf.get(CONF_SSL_CERTIFICATE)
    ssl_peer_certificate = conf.get(CONF_SSL_PEER_CERTIFICATE)
    ssl_key = conf.get(CONF_SSL_KEY)
    cors_origins = conf[CONF_CORS_ORIGINS]
    use_x_forwarded_for = conf.get(CONF_USE_X_FORWARDED_FOR, False)
    trusted_proxies = conf.get(CONF_TRUSTED_PROXIES, [])
    is_ban_enabled = conf[CONF_IP_BAN_ENABLED]
    login_threshold = conf[CONF_LOGIN_ATTEMPTS_THRESHOLD]
    ssl_profile = conf[CONF_SSL_PROFILE]

    server = OpenPeerPowerHTTP(
        opp,
        server_host=server_host,
        server_port=server_port,
        ssl_certificate=ssl_certificate,
        ssl_peer_certificate=ssl_peer_certificate,
        ssl_key=ssl_key,
        cors_origins=cors_origins,
        use_x_forwarded_for=use_x_forwarded_for,
        trusted_proxies=trusted_proxies,
        login_threshold=login_threshold,
        is_ban_enabled=is_ban_enabled,
        ssl_profile=ssl_profile,
    )

    startup_listeners = []

    async def stop_server(event: Event) -> None:
        """Stop the server."""
        await server.stop()

    async def start_server(event: Event) -> None:
        """Start the server."""

        for listener in startup_listeners:
            listener()

        opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, stop_server)

        await start_http_server_and_save_config(opp, dict(conf), server)

    async def async_wait_frontend_load(event: Event) -> None:
        """Wait for the frontend to load."""

        if event.data[ATTR_COMPONENT] != "frontend":
            return

        await start_server(event)

    startup_listeners.append(
        opp.bus.async_listen(EVENT_COMPONENT_LOADED, async_wait_frontend_load)
    )
    startup_listeners.append(
        opp.bus.async_listen(EVENT_OPENPEERPOWER_START, start_server)
    )

    opp.http = server

    local_ip = await opp.async_add_executor_job(opp_util.get_local_ip)

    host = local_ip
    if server_host is not None:
        # Assume the first server host name provided as API host
        host = server_host[0]

    opp.config.api = ApiConfig(local_ip, host, server_port, ssl_certificate is not None)

    return True


class OpenPeerPowerHTTP:
    """HTTP server for Open Peer Power."""

    def __init__(
        self,
        opp,
        ssl_certificate,
        ssl_peer_certificate,
        ssl_key,
        server_host,
        server_port,
        cors_origins,
        use_x_forwarded_for,
        trusted_proxies,
        login_threshold,
        is_ban_enabled,
        ssl_profile,
    ):
        """Initialize the HTTP Open Peer Power server."""
        app = self.app = web.Application(
            middlewares=[], client_max_size=MAX_CLIENT_SIZE
        )
        app[KEY_OPP] = opp

        # Order matters, security filters middle ware needs to go first,
        # forwarded middleware needs to go second.
        setup_security_filter(app)

        # Only register middleware if `use_x_forwarded_for` is enabled
        # and trusted proxies are provided
        if use_x_forwarded_for and trusted_proxies:
            async_setup_forwarded(app, trusted_proxies)

        setup_request_context(app, current_request)

        if is_ban_enabled:
            setup_bans(opp, app, login_threshold)

        setup_auth(opp, app)

        setup_cors(app, cors_origins)

        self.opp = opp
        self.ssl_certificate = ssl_certificate
        self.ssl_peer_certificate = ssl_peer_certificate
        self.ssl_key = ssl_key
        self.server_host = server_host
        self.server_port = server_port
        self.trusted_proxies = trusted_proxies
        self.is_ban_enabled = is_ban_enabled
        self.ssl_profile = ssl_profile
        self._handler = None
        self.runner = None
        self.site = None

    def register_view(self, view):
        """Register a view with the WSGI server.

        The view argument must be a class that inherits from OpenPeerPowerView.
        It is optional to instantiate it before registering; this method will
        handle it either way.
        """
        if isinstance(view, type):
            # Instantiate the view, if needed
            view = view()

        if not hasattr(view, "url"):
            class_name = view.__class__.__name__
            raise AttributeError(f'{class_name} missing required attribute "url"')

        if not hasattr(view, "name"):
            class_name = view.__class__.__name__
            raise AttributeError(f'{class_name} missing required attribute "name"')

        view.register(self.app, self.app.router)

    def register_redirect(self, url, redirect_to, *, redirect_exc=HTTPMovedPermanently):
        """Register a redirect with the server.

        If given this must be either a string or callable. In case of a
        callable it's called with the url adapter that triggered the match and
        the values of the URL as keyword arguments and has to return the target
        for the redirect, otherwise it has to be a string with placeholders in
        rule syntax.
        """

        async def redirect(request):
            """Redirect to location."""
            raise redirect_exc(redirect_to)

        self.app.router.add_route("GET", url, redirect)

    def register_static_path(self, url_path, path, cache_headers=True):
        """Register a folder or file to serve as a static path."""
        if os.path.isdir(path):
            if cache_headers:
                resource = CachingStaticResource
            else:
                resource = web.StaticResource
            self.app.router.register_resource(resource(url_path, path))
            return

        if cache_headers:

            async def serve_file(request):
                """Serve file from disk."""
                return web.FileResponse(path, headers=CACHE_HEADERS)

        else:

            async def serve_file(request):
                """Serve file from disk."""
                return web.FileResponse(path)

        self.app.router.add_route("GET", url_path, serve_file)

    async def start(self):
        """Start the aiohttp server."""
        if self.ssl_certificate:
            try:
                if self.ssl_profile == SSL_INTERMEDIATE:
                    context = ssl_util.server_context_intermediate()
                else:
                    context = ssl_util.server_context_modern()
                await self.opp.async_add_executor_job(
                    context.load_cert_chain, self.ssl_certificate, self.ssl_key
                )
            except OSError as error:
                _LOGGER.error(
                    "Could not read SSL certificate from %s: %s",
                    self.ssl_certificate,
                    error,
                )
                return

            if self.ssl_peer_certificate:
                context.verify_mode = ssl.CERT_REQUIRED
                await self.opp.async_add_executor_job(
                    context.load_verify_locations, self.ssl_peer_certificate
                )

        else:
            context = None

        # Aiohttp freezes apps after start so that no changes can be made.
        # However in Open Peer Power components can be discovered after boot.
        # This will now raise a RunTimeError.
        # To work around this we now prevent the router from getting frozen
        # pylint: disable=protected-access
        self.app._router.freeze = lambda: None

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        self.site = OpenPeerPowerTCPSite(
            self.runner, self.server_host, self.server_port, ssl_context=context
        )
        try:
            await self.site.start()
        except OSError as error:
            _LOGGER.error(
                "Failed to create HTTP server at port %d: %s", self.server_port, error
            )

        _LOGGER.info("Now listening on port %d", self.server_port)

    async def stop(self):
        """Stop the aiohttp server."""
        await self.site.stop()
        await self.runner.cleanup()


async def start_http_server_and_save_config(
    opp: OpenPeerPower, conf: Dict, server: OpenPeerPowerHTTP
) -> None:
    """Startup the http server and save the config."""
    await server.start()  # type: ignore

    # If we are set up successful, we store the HTTP settings for safe mode.
    store = storage.Store(opp, STORAGE_VERSION, STORAGE_KEY)

    if CONF_TRUSTED_PROXIES in conf:
        conf[CONF_TRUSTED_PROXIES] = [
            str(ip.network_address) for ip in conf[CONF_TRUSTED_PROXIES]
        ]

    await store.async_save(conf)


current_request: ContextVar[Optional[web.Request]] = ContextVar(
    "current_request", default=None
)
