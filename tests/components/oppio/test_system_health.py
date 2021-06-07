"""Test oppio system health."""
import asyncio
import os
from unittest.mock import patch

from aiohttp import ClientError

from openpeerpower.setup import async_setup_component

from .test_init import MOCK_ENVIRON

from tests.common import get_system_health_info


async def test_oppio_system_health(opp, aioclient_mock):
    """Test oppio system health."""
    aioclient_mock.get("http://127.0.0.1/info", json={"result": "ok", "data": {}})
    aioclient_mock.get("http://127.0.0.1/host/info", json={"result": "ok", "data": {}})
    aioclient_mock.get("http://127.0.0.1/os/info", json={"result": "ok", "data": {}})
    aioclient_mock.get("http://127.0.0.1/supervisor/ping", text="")
    aioclient_mock.get("https://version.openpeerpower.io/stable.json", text="")
    aioclient_mock.get(
        "http://127.0.0.1/supervisor/info", json={"result": "ok", "data": {}}
    )

    opp.config.components.add("oppio")
    with patch.dict(os.environ, MOCK_ENVIRON):
        assert await async_setup_component(opp, "system_health", {})

    opp.data["oppio_info"] = {
        "channel": "stable",
        "supervisor": "2020.11.1",
        "docker": "19.0.3",
        "oppos": True,
    }
    opp.data["oppio_host_info"] = {
        "operating_system": "Open Peer Power OS 5.9",
        "disk_total": "32.0",
        "disk_used": "30.0",
    }
    opp.data["oppio_os_info"] = {"board": "odroid-n2"}
    opp.data["oppio_supervisor_info"] = {
        "healthy": True,
        "supported": True,
        "addons": [{"name": "Awesome Addon", "version": "1.0.0"}],
    }

    info = await get_system_health_info(opp, "oppio")

    for key, val in info.items():
        if asyncio.iscoroutine(val):
            info[key] = await val

    assert info == {
        "board": "odroid-n2",
        "disk_total": "32.0 GB",
        "disk_used": "30.0 GB",
        "docker_version": "19.0.3",
        "healthy": True,
        "host_os": "Open Peer Power OS 5.9",
        "installed_addons": "Awesome Addon (1.0.0)",
        "supervisor_api": "ok",
        "supervisor_version": "supervisor-2020.11.1",
        "supported": True,
        "update_channel": "stable",
        "version_api": "ok",
    }


async def test_oppio_system_health_with_issues(opp, aioclient_mock):
    """Test oppio system health."""
    aioclient_mock.get("http://127.0.0.1/info", json={"result": "ok", "data": {}})
    aioclient_mock.get("http://127.0.0.1/host/info", json={"result": "ok", "data": {}})
    aioclient_mock.get("http://127.0.0.1/os/info", json={"result": "ok", "data": {}})
    aioclient_mock.get("http://127.0.0.1/supervisor/ping", text="")
    aioclient_mock.get("https://version.openpeerpower.io/stable.json", exc=ClientError)
    aioclient_mock.get(
        "http://127.0.0.1/supervisor/info", json={"result": "ok", "data": {}}
    )

    opp.config.components.add("oppio")
    with patch.dict(os.environ, MOCK_ENVIRON):
        assert await async_setup_component(opp, "system_health", {})

    opp.data["oppio_info"] = {"channel": "stable"}
    opp.data["oppio_host_info"] = {}
    opp.data["oppio_os_info"] = {}
    opp.data["oppio_supervisor_info"] = {
        "healthy": False,
        "supported": False,
    }

    info = await get_system_health_info(opp, "oppio")

    for key, val in info.items():
        if asyncio.iscoroutine(val):
            info[key] = await val

    assert info["healthy"] == {
        "error": "Unhealthy",
        "more_info": "/oppio/system",
        "type": "failed",
    }
    assert info["supported"] == {
        "error": "Unsupported",
        "more_info": "/oppio/system",
        "type": "failed",
    }
    assert info["version_api"] == {
        "error": "unreachable",
        "more_info": "/oppio/system",
        "type": "failed",
    }
