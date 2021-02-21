"""The tests for the Open Peer Power HTTP component."""
from ipaddress import ip_network
import logging
from unittest.mock import Mock, patch

import pytest

import openpeerpower.components.http as http
from openpeerpowerr.setup import async_setup_component
from openpeerpowerr.util.ssl import server_context_intermediate, server_context_modern


@pytest.fixture
def mock_stack():
    """Mock extract stack."""
    with patch(
        "openpeerpower.components.http.extract_stack",
        return_value=[
            Mock(
                filename="/home/paulus/core/openpeerpower/core.py",
                lineno="23",
                line="do_something()",
            ),
            Mock(
                filename="/home/paulus/core/openpeerpower/components/hue/light.py",
                lineno="23",
                line="self.light.is_on",
            ),
            Mock(
                filename="/home/paulus/core/openpeerpower/components/http/__init__.py",
                lineno="157",
                line="base_url",
            ),
        ],
    ):
        yield


class TestView(http.OpenPeerPowerView):
    """Test the HTTP views."""

    name = "test"
    url = "/hello"

    async def get(self, request):
        """Return a get request."""
        return "hello"


async def test_registering_view_while_running(
   .opp, aiohttp_client, aiohttp_unused_port
):
    """Test that we can register a view while the server is running."""
    await async_setup_component(
       .opp, http.DOMAIN, {http.DOMAIN: {http.CONF_SERVER_PORT: aiohttp_unused_port()}}
    )

    await opp.async_start()
    # This raises a RuntimeError if app is frozen
   .opp.http.register_view(TestView)


async def test_not_log_password.opp, aiohttp_client, caplog, legacy_auth):
    """Test access with password doesn't get logged."""
    assert await async_setup_component.opp, "api", {"http": {}})
    client = await aiohttp_client.opp.http.app)
    logging.getLogger("aiohttp.access").setLevel(logging.INFO)

    resp = await client.get("/api/", params={"api_password": "test-password"})

    assert resp.status == 401
    logs = caplog.text

    # Ensure we don't log API passwords
    assert "/api/" in logs
    assert "some-pass" not in logs


async def test_proxy_config.opp):
    """Test use_x_forwarded_for must config together with trusted_proxies."""
    assert (
        await async_setup_component(
           .opp,
            "http",
            {
                "http": {
                    http.CONF_USE_X_FORWARDED_FOR: True,
                    http.CONF_TRUSTED_PROXIES: ["127.0.0.1"],
                }
            },
        )
        is True
    )


async def test_proxy_config_only_use_xff.opp):
    """Test use_x_forwarded_for must config together with trusted_proxies."""
    assert (
        await async_setup_component(
           .opp, "http", {"http": {http.CONF_USE_X_FORWARDED_FOR: True}}
        )
        is not True
    )


async def test_proxy_config_only_trust_proxies.opp):
    """Test use_x_forwarded_for must config together with trusted_proxies."""
    assert (
        await async_setup_component(
           .opp, "http", {"http": {http.CONF_TRUSTED_PROXIES: ["127.0.0.1"]}}
        )
        is not True
    )


async def test_ssl_profile_defaults_modern.opp):
    """Test default ssl profile."""
    assert await async_setup_component.opp, "http", {}) is True

   .opp.http.ssl_certificate = "bla"

    with patch("ssl.SSLContext.load_cert_chain"), patch(
        "openpeerpowerr.util.ssl.server_context_modern",
        side_effect=server_context_modern,
    ) as mock_context:
        await opp.async_start()
        await opp.async_block_till_done()

    assert len(mock_context.mock_calls) == 1


async def test_ssl_profile_change_intermediate.opp):
    """Test setting ssl profile to intermediate."""
    assert (
        await async_setup_component(
           .opp, "http", {"http": {"ssl_profile": "intermediate"}}
        )
        is True
    )

   .opp.http.ssl_certificate = "bla"

    with patch("ssl.SSLContext.load_cert_chain"), patch(
        "openpeerpowerr.util.ssl.server_context_intermediate",
        side_effect=server_context_intermediate,
    ) as mock_context:
        await opp.async_start()
        await opp.async_block_till_done()

    assert len(mock_context.mock_calls) == 1


async def test_ssl_profile_change_modern.opp):
    """Test setting ssl profile to modern."""
    assert (
        await async_setup_component.opp, "http", {"http": {"ssl_profile": "modern"}})
        is True
    )

   .opp.http.ssl_certificate = "bla"

    with patch("ssl.SSLContext.load_cert_chain"), patch(
        "openpeerpowerr.util.ssl.server_context_modern",
        side_effect=server_context_modern,
    ) as mock_context:
        await opp.async_start()
        await opp.async_block_till_done()

    assert len(mock_context.mock_calls) == 1


async def test_cors_defaults.opp):
    """Test the CORS default settings."""
    with patch("openpeerpower.components.http.setup_cors") as mock_setup:
        assert await async_setup_component.opp, "http", {})

    assert len(mock_setup.mock_calls) == 1
    assert mock_setup.mock_calls[0][1][1] == [
        "https://cast.openpeerpower.io",
        "https://my.openpeerpower.io",
    ]


async def test_storing_config.opp, aiohttp_client, aiohttp_unused_port):
    """Test that we store last working config."""
    config = {
        http.CONF_SERVER_PORT: aiohttp_unused_port(),
        "use_x_forwarded_for": True,
        "trusted_proxies": ["192.168.1.100"],
    }

    assert await async_setup_component.opp, http.DOMAIN, {http.DOMAIN: config})

    await opp.async_start()
    restored = await.opp.components.http.async_get_last_config()
    restored["trusted_proxies"][0] = ip_network(restored["trusted_proxies"][0])

    assert restored == http.HTTP_SCHEMA(config)
