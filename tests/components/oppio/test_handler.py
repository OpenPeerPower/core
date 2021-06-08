"""The tests for the oppio component."""

import aiohttp
import pytest

from openpeerpower.components.oppio.handler import OppioAPIError


async def test_api_ping(oppio_handler, aioclient_mock):
    """Test setup with API ping."""
    aioclient_mock.get("http://127.0.0.1/supervisor/ping", json={"result": "ok"})

    assert await oppio_handler.is_connected()
    assert aioclient_mock.call_count == 1


async def test_api_ping_error(oppio_handler, aioclient_mock):
    """Test setup with API ping error."""
    aioclient_mock.get("http://127.0.0.1/supervisor/ping", json={"result": "error"})

    assert not (await oppio_handler.is_connected())
    assert aioclient_mock.call_count == 1


async def test_api_ping_exeption(oppio_handler, aioclient_mock):
    """Test setup with API ping exception."""
    aioclient_mock.get("http://127.0.0.1/supervisor/ping", exc=aiohttp.ClientError())

    assert not (await oppio_handler.is_connected())
    assert aioclient_mock.call_count == 1


async def test_api_info(oppio_handler, aioclient_mock):
    """Test setup with API generic info."""
    aioclient_mock.get(
        "http://127.0.0.1/info",
        json={
            "result": "ok",
            "data": {"supervisor": "222", "openpeerpower": "0.110.0", "oppos": None},
        },
    )

    data = await oppio_handler.get_info()
    assert aioclient_mock.call_count == 1
    assert data["oppos"] is None
    assert data["openpeerpower"] == "0.110.0"
    assert data["supervisor"] == "222"


async def test_api_info_error(oppio_handler, aioclient_mock):
    """Test setup with API Open Peer Power info error."""
    aioclient_mock.get(
        "http://127.0.0.1/info", json={"result": "error", "message": None}
    )

    with pytest.raises(OppioAPIError):
        await oppio_handler.get_info()

    assert aioclient_mock.call_count == 1


async def test_api_host_info(oppio_handler, aioclient_mock):
    """Test setup with API Host info."""
    aioclient_mock.get(
        "http://127.0.0.1/host/info",
        json={
            "result": "ok",
            "data": {
                "copp.s": "vm",
                "operating_system": "Debian GNU/Linux 10 (buster)",
                "kernel": "4.19.0-6-amd64",
            },
        },
    )

    data = await oppio_handler.get_host_info()
    assert aioclient_mock.call_count == 1
    assert data["copp.s"] == "vm"
    assert data["kernel"] == "4.19.0-6-amd64"
    assert data["operating_system"] == "Debian GNU/Linux 10 (buster)"


async def test_api_supervisor_info(oppio_handler, aioclient_mock):
    """Test setup with API Supervisor info."""
    aioclient_mock.get(
        "http://127.0.0.1/supervisor/info",
        json={
            "result": "ok",
            "data": {"supported": True, "version": "2020.11.1", "channel": "stable"},
        },
    )

    data = await oppio_handler.get_supervisor_info()
    assert aioclient_mock.call_count == 1
    assert data["supported"]
    assert data["version"] == "2020.11.1"
    assert data["channel"] == "stable"


async def test_api_os_info(oppio_handler, aioclient_mock):
    """Test setup with API OS info."""
    aioclient_mock.get(
        "http://127.0.0.1/os/info",
        json={
            "result": "ok",
            "data": {"board": "odroid-n2", "version": "2020.11.1"},
        },
    )

    data = await oppio_handler.get_os_info()
    assert aioclient_mock.call_count == 1
    assert data["board"] == "odroid-n2"
    assert data["version"] == "2020.11.1"


async def test_api_host_info_error(oppio_handler, aioclient_mock):
    """Test setup with API Open Peer Power info error."""
    aioclient_mock.get(
        "http://127.0.0.1/host/info", json={"result": "error", "message": None}
    )

    with pytest.raises(OppioAPIError):
        await oppio_handler.get_host_info()

    assert aioclient_mock.call_count == 1


async def test_api_core_info(oppio_handler, aioclient_mock):
    """Test setup with API Open Peer Power Core info."""
    aioclient_mock.get(
        "http://127.0.0.1/core/info",
        json={"result": "ok", "data": {"version_latest": "1.0.0"}},
    )

    data = await oppio_handler.get_core_info()
    assert aioclient_mock.call_count == 1
    assert data["version_latest"] == "1.0.0"


async def test_api_core_info_error(oppio_handler, aioclient_mock):
    """Test setup with API Open Peer Power Core info error."""
    aioclient_mock.get(
        "http://127.0.0.1/core/info", json={"result": "error", "message": None}
    )

    with pytest.raises(OppioAPIError):
        await oppio_handler.get_core_info()

    assert aioclient_mock.call_count == 1


async def test_api_openpeerpower_stop(oppio_handler, aioclient_mock):
    """Test setup with API Open Peer Power stop."""
    aioclient_mock.post("http://127.0.0.1/openpeerpower/stop", json={"result": "ok"})

    assert await oppio_handler.stop_openpeerpower()
    assert aioclient_mock.call_count == 1


async def test_api_openpeerpower_restart(oppio_handler, aioclient_mock):
    """Test setup with API Open Peer Power restart."""
    aioclient_mock.post("http://127.0.0.1/openpeerpower/restart", json={"result": "ok"})

    assert await oppio_handler.restart_openpeerpower()
    assert aioclient_mock.call_count == 1


async def test_api_addon_info(oppio_handler, aioclient_mock):
    """Test setup with API Add-on info."""
    aioclient_mock.get(
        "http://127.0.0.1/addons/test/info",
        json={"result": "ok", "data": {"name": "bla"}},
    )

    data = await oppio_handler.get_addon_info("test")
    assert data["name"] == "bla"
    assert aioclient_mock.call_count == 1


async def test_api_discovery_message(oppio_handler, aioclient_mock):
    """Test setup with API discovery message."""
    aioclient_mock.get(
        "http://127.0.0.1/discovery/test",
        json={"result": "ok", "data": {"service": "mqtt"}},
    )

    data = await oppio_handler.get_discovery_message("test")
    assert data["service"] == "mqtt"
    assert aioclient_mock.call_count == 1


async def test_api_retrieve_discovery(oppio_handler, aioclient_mock):
    """Test setup with API discovery message."""
    aioclient_mock.get(
        "http://127.0.0.1/discovery",
        json={"result": "ok", "data": {"discovery": [{"service": "mqtt"}]}},
    )

    data = await oppio_handler.retrieve_discovery_messages()
    assert data["discovery"][-1]["service"] == "mqtt"
    assert aioclient_mock.call_count == 1


async def test_api_ingress_panels(oppio_handler, aioclient_mock):
    """Test setup with API Ingress panels."""
    aioclient_mock.get(
        "http://127.0.0.1/ingress/panels",
        json={
            "result": "ok",
            "data": {
                "panels": {
                    "slug": {
                        "enable": True,
                        "title": "Test",
                        "icon": "mdi:test",
                        "admin": False,
                    }
                }
            },
        },
    )

    data = await oppio_handler.get_ingress_panels()
    assert aioclient_mock.call_count == 1
    assert data["panels"]
    assert "slug" in data["panels"]
