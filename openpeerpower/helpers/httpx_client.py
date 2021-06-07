"""Helper for httpx."""
from __future__ import annotations

import sys
from typing import Any, Callable

import httpx

from openpeerpower.const import EVENT_OPENPEERPOWER_CLOSE, __version__
from openpeerpower.core import Event, OpenPeerPower, callback
from openpeerpower.helpers.frame import warn_use
from openpeerpower.loader import bind_opp

DATA_ASYNC_CLIENT = "httpx_async_client"
DATA_ASYNC_CLIENT_NOVERIFY = "httpx_async_client_noverify"
SERVER_SOFTWARE = "OpenPeerPower/{0} httpx/{1} Python/{2[0]}.{2[1]}".format(
    __version__, httpx.__version__, sys.version_info
)
USER_AGENT = "User-Agent"


@callback
@bind_opp
def get_async_client(opp: OpenPeerPower, verify_ssl: bool = True) -> httpx.AsyncClient:
    """Return default httpx AsyncClient.

    This method must be run in the event loop.
    """
    key = DATA_ASYNC_CLIENT if verify_ssl else DATA_ASYNC_CLIENT_NOVERIFY

    client: httpx.AsyncClient | None = opp.data.get(key)

    if client is None:
        client = opp.data[key] = create_async_httpx_client(opp, verify_ssl)

    return client


class OppHttpXAsyncClient(httpx.AsyncClient):
    """httpx AsyncClient that suppresses context management."""

    async def __aenter__(self: OppHttpXAsyncClient) -> OppHttpXAsyncClient:
        """Prevent an integration from reopen of the client via context manager."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Prevent an integration from close of the client via context manager."""


@callback
def create_async_httpx_client(
    opp: OpenPeerPower,
    verify_ssl: bool = True,
    auto_cleanup: bool = True,
    **kwargs: Any,
) -> httpx.AsyncClient:
    """Create a new httpx.AsyncClient with kwargs, i.e. for cookies.

    If auto_cleanup is False, the client will be
    automatically closed on openpeerpower_stop.

    This method must be run in the event loop.
    """
    client = OppHttpXAsyncClient(
        verify=verify_ssl,
        headers={USER_AGENT: SERVER_SOFTWARE},
        **kwargs,
    )

    original_aclose = client.aclose

    client.aclose = warn_use(  # type: ignore
        client.aclose, "closes the Open Peer Power httpx client"
    )

    if auto_cleanup:
        _async_register_async_client_shutdown(opp, client, original_aclose)

    return client


@callback
def _async_register_async_client_shutdown(
    opp: OpenPeerPower,
    client: httpx.AsyncClient,
    original_aclose: Callable[..., Any],
) -> None:
    """Register httpx AsyncClient aclose on Open Peer Power shutdown.

    This method must be run in the event loop.
    """

    async def _async_close_client(event: Event) -> None:
        """Close httpx client."""
        await original_aclose()

    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_CLOSE, _async_close_client)
