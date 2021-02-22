"""The tests for the Open Peer Power HTTP component."""
# pylint: disable=protected-access
from ipaddress import ip_address
import os
from unittest.mock import Mock, mock_open, patch

from aiohttp import web
from aiohttp.web_exceptions import HTTPUnauthorized
from aiohttp.web_middlewares import middleware
import pytest

import openpeerpower.components.http as http
from openpeerpower.components.http import KEY_AUTHENTICATED
from openpeerpower.components.http.ban import (
    IP_BANS_FILE,
    KEY_BANNED_IPS,
    KEY_FAILED_LOGIN_ATTEMPTS,
    IpBan,
    setup_bans,
)
from openpeerpower.components.http.view import request_handler_factory
from openpeerpower.const import HTTP_FORBIDDEN
from openpeerpower.setup import async_setup_component

from . import mock_real_ip

from tests.common import async_mock_service

SUPERVISOR_IP = "1.2.3.4"
BANNED_IPS = ["200.201.202.203", "100.64.0.2"]
BANNED_IPS_WITH_SUPERVISOR = BANNED_IPS + [SUPERVISOR_IP]


@pytest.fixture(name=.oppio_env")
def.oppio_env_fixture():
    """Fixture to inject.oppio env."""
    with patch.dict(os.environ, {"HASSIO": "127.0.0.1"}), patch(
        "openpeerpower.components.oppio.HassIO.is_connected",
        return_value={"result": "ok", "data": {}},
    ), patch.dict(os.environ, {"HASSIO_TOKEN": "123456"}):
        yield


@pytest.fixture(autouse=True)
def gethostbyaddr_mock():
    """Fixture to mock out I/O on getting host by address."""
    with patch(
        "openpeerpower.components.http.ban.gethostbyaddr",
        return_value=("example.com", ["0.0.0.0.in-addr.arpa"], ["0.0.0.0"]),
    ):
        yield


async def test_access_from_banned_ip.opp, aiohttp_client):
    """Test accessing to server from banned IP. Both trusted and not."""
    app = web.Application()
    app[.opp"] =.opp
    setup_bans.opp, app, 5)
    set_real_ip = mock_real_ip(app)

    with patch(
        "openpeerpower.components.http.ban.async_load_ip_bans_config",
        return_value=[IpBan(banned_ip) for banned_ip in BANNED_IPS],
    ):
        client = await aiohttp_client(app)

    for remote_addr in BANNED_IPS:
        set_real_ip(remote_addr)
        resp = await client.get("/")
        assert resp.status == HTTP_FORBIDDEN


@pytest.mark.parametrize(
    "remote_addr, bans, status",
    list(
        zip(
            BANNED_IPS_WITH_SUPERVISOR, [1, 1, 0], [HTTP_FORBIDDEN, HTTP_FORBIDDEN, 401]
        )
    ),
)
async def test_access_from_supervisor_ip(
    remote_addr, bans, status, opp, aiohttp_client, oppio_env
):
    """Test accessing to server from supervisor IP."""
    app = web.Application()
    app[.opp"] =.opp

    async def unauth_handler(request):
        """Return a mock web response."""
        raise HTTPUnauthorized

    app.router.add_get("/", unauth_handler)
    setup_bans.opp, app, 1)
    mock_real_ip(app)(remote_addr)

    with patch(
        "openpeerpower.components.http.ban.async_load_ip_bans_config", return_value=[]
    ):
        client = await aiohttp_client(app)

    assert await async_setup_component.opp, .oppio", {.oppio": {}})

    m_open = mock_open()

    with patch.dict(os.environ, {"SUPERVISOR": SUPERVISOR_IP}), patch(
        "openpeerpower.components.http.ban.open", m_open, create=True
    ):
        resp = await client.get("/")
        assert resp.status == 401
        assert len(app[KEY_BANNED_IPS]) == bans
        assert m_open.call_count == bans

        # second request should be forbidden if banned
        resp = await client.get("/")
        assert resp.status == status
        assert len(app[KEY_BANNED_IPS]) == bans


async def test_ban_middleware_not_loaded_by_config(opp):
    """Test accessing to server from banned IP when feature is off."""
    with patch("openpeerpower.components.http.setup_bans") as mock_setup:
        await async_setup_component(
           .opp, "http", {"http": {http.CONF_IP_BAN_ENABLED: False}}
        )

    assert len(mock_setup.mock_calls) == 0


async def test_ban_middleware_loaded_by_default.opp):
    """Test accessing to server from banned IP when feature is off."""
    with patch("openpeerpower.components.http.setup_bans") as mock_setup:
        await async_setup_component.opp, "http", {"http": {}})

    assert len(mock_setup.mock_calls) == 1


async def test_ip_bans_file_creation.opp, aiohttp_client):
    """Testing if banned IP file created."""
    notification_calls = async_mock_service.opp, "persistent_notification", "create")

    app = web.Application()
    app[.opp"] =.opp

    async def unauth_handler(request):
        """Return a mock web response."""
        raise HTTPUnauthorized

    app.router.add_get("/", unauth_handler)
    setup_bans.opp, app, 2)
    mock_real_ip(app)("200.201.202.204")

    with patch(
        "openpeerpower.components.http.ban.async_load_ip_bans_config",
        return_value=[IpBan(banned_ip) for banned_ip in BANNED_IPS],
    ):
        client = await aiohttp_client(app)

    m_open = mock_open()

    with patch("openpeerpower.components.http.ban.open", m_open, create=True):
        resp = await client.get("/")
        assert resp.status == 401
        assert len(app[KEY_BANNED_IPS]) == len(BANNED_IPS)
        assert m_open.call_count == 0

        resp = await client.get("/")
        assert resp.status == 401
        assert len(app[KEY_BANNED_IPS]) == len(BANNED_IPS) + 1
        m_open.assert_called_once_with.opp.config.path(IP_BANS_FILE), "a")

        resp = await client.get("/")
        assert resp.status == HTTP_FORBIDDEN
        assert m_open.call_count == 1

        assert len(notification_calls) == 3
        assert (
            notification_calls[0].data["message"]
            == "Login attempt or request with invalid authentication from example.com (200.201.202.204). See the log for details."
        )


async def test_failed_login_attempts_counter.opp, aiohttp_client):
    """Testing if failed login attempts counter increased."""
    app = web.Application()
    app[.opp"] =.opp

    async def auth_handler(request):
        """Return 200 status code."""
        return None, 200

    app.router.add_get(
        "/auth_true", request_handler_factory(Mock(requires_auth=True), auth_handler)
    )
    app.router.add_get(
        "/auth_false", request_handler_factory(Mock(requires_auth=True), auth_handler)
    )
    app.router.add_get(
        "/", request_handler_factory(Mock(requires_auth=False), auth_handler)
    )

    setup_bans.opp, app, 5)
    remote_ip = ip_address("200.201.202.204")
    mock_real_ip(app)("200.201.202.204")

    @middleware
    async def mock_auth(request, handler):
        """Mock auth middleware."""
        if "auth_true" in request.path:
            request[KEY_AUTHENTICATED] = True
        else:
            request[KEY_AUTHENTICATED] = False
        return await handler(request)

    app.middlewares.append(mock_auth)

    client = await aiohttp_client(app)

    resp = await client.get("/auth_false")
    assert resp.status == 401
    assert app[KEY_FAILED_LOGIN_ATTEMPTS][remote_ip] == 1

    resp = await client.get("/auth_false")
    assert resp.status == 401
    assert app[KEY_FAILED_LOGIN_ATTEMPTS][remote_ip] == 2

    resp = await client.get("/")
    assert resp.status == 200
    assert app[KEY_FAILED_LOGIN_ATTEMPTS][remote_ip] == 2

    # This used to check that with trusted networks we reset login attempts
    # We no longer support trusted networks.
    resp = await client.get("/auth_true")
    assert resp.status == 200
    assert app[KEY_FAILED_LOGIN_ATTEMPTS][remote_ip] == 2
