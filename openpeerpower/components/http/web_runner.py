"""OpenPeerPower specific aiohttp Site."""
import asyncio
from ssl import SSLContext
from typing import List, Optional, Union

from aiohttp import web
from yarl import URL


class OpenPeerPowerTCPSite(web.BaseSite):
    """OpenPeerPower specific aiohttp Site.

    Vanilla TCPSite accepts only str as host. However, the underlying asyncio's
    create_server() implementation does take a list of strings to bind to multiple
    host IP's. To support multiple server_host entries (e.g. to enable dual-stack
    explicitly), we would like to pass an array of strings. Bring our own
    implementation inspired by TCPSite.

    Custom TCPSite can be dropped when https://github.com/aio-libs/aiohttp/pull/4894
    is merged.
    """

    __slots__ = ("_host", "_port", "_reuse_address", "_reuse_port", "_hosturl")

    def __init__(
        self,
        runner: "web.BaseRunner",
        host: Union[None, str, List[str]],
        port: int,
        *,
        shutdown_timeout: float = 10.0,
        ssl_context: Optional[SSLContext] = None,
        backlog: int = 128,
        reuse_address: Optional[bool] = None,
        reuse_port: Optional[bool] = None,
    ) -> None:  # noqa: D107
        super().__init__(
            runner,
            shutdown_timeout=shutdown_timeout,
            ssl_context=ssl_context,
            backlog=backlog,
        )
        self._host = host
        self._port = port
        self._reuse_address = reuse_address
        self._reuse_port = reuse_port

    @property
    def name(self) -> str:  # noqa: D102
        scheme = "https" if self._ssl_context else "http"
        host = self._host[0] if isinstance(self._host, list) else "0.0.0.0"
        return str(URL.build(scheme=scheme, host=host, port=self._port))

    async def start(self) -> None:  # noqa: D102
        await super().start()
        loop = asyncio.get_running_loop()
        server = self._runner.server
        assert server is not None
        self._server = await loop.create_server(
            server,
            self._host,
            self._port,
            ssl=self._ssl_context,
            backlog=self._backlog,
            reuse_address=self._reuse_address,
            reuse_port=self._reuse_port,
        )
