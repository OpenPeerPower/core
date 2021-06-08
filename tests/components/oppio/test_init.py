"""The tests for the oppio component."""
from datetime import timedelta
import os
from unittest.mock import patch

import pytest

from openpeerpower.auth.const import GROUP_ID_ADMIN
from openpeerpower.components import frontend
from openpeerpower.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from openpeerpower.components.oppio import ADDONS_COORDINATOR, DOMAIN, STORAGE_KEY
from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.helpers.device_registry import async_get
from openpeerpower.setup import async_setup_component
from openpeerpower.util import dt as dt_util

from tests.common import MockConfigEntry, async_fire_time_changed

MOCK_ENVIRON = {"OPPIO": "127.0.0.1", "OPPIO_TOKEN": "abcdefgh"}


@pytest.fixture(autouse=True)
def mock_all(aioclient_mock, request):
    """Mock all setup requests."""
    aioclient_mock.post("http://127.0.0.1/openpeerpower/options", json={"result": "ok"})
    aioclient_mock.get("http://127.0.0.1/supervisor/ping", json={"result": "ok"})
    aioclient_mock.post("http://127.0.0.1/supervisor/options", json={"result": "ok"})
    aioclient_mock.get(
        "http://127.0.0.1/info",
        json={
            "result": "ok",
            "data": {"supervisor": "222", "openpeerpower": "0.110.0", "oppos": None},
        },
    )
    aioclient_mock.get(
        "http://127.0.0.1/store",
        json={
            "result": "ok",
            "data": {"addons": [], "repositories": []},
        },
    )
    aioclient_mock.get(
        "http://127.0.0.1/host/info",
        json={
            "result": "ok",
            "data": {
                "result": "ok",
                "data": {
                    "copp.s": "vm",
                    "operating_system": "Debian GNU/Linux 10 (buster)",
                    "kernel": "4.19.0-6-amd64",
                },
            },
        },
    )
    aioclient_mock.get(
        "http://127.0.0.1/core/info",
        json={"result": "ok", "data": {"version_latest": "1.0.0"}},
    )
    aioclient_mock.get(
        "http://127.0.0.1/os/info",
        json={"result": "ok", "data": {"version_latest": "1.0.0"}},
    )
    aioclient_mock.get(
        "http://127.0.0.1/supervisor/info",
        json={
            "result": "ok",
            "data": {"version_latest": "1.0.0"},
            "addons": [
                {
                    "name": "test",
                    "slug": "test",
                    "installed": True,
                    "update_available": False,
                    "version": "1.0.0",
                    "version_latest": "1.0.0",
                    "repository": "core",
                    "url": "https://github.com/openpeerpower/addons/test",
                },
                {
                    "name": "test2",
                    "slug": "test2",
                    "installed": True,
                    "update_available": False,
                    "version": "1.0.0",
                    "version_latest": "1.0.0",
                    "repository": "core",
                    "url": "https://github.com",
                },
            ],
        },
    )
    aioclient_mock.get(
        "http://127.0.0.1/ingress/panels", json={"result": "ok", "data": {"panels": {}}}
    )


async def test_setup_api_ping(opp, aioclient_mock):
    """Test setup with API ping."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(opp, "oppio", {})
        assert result

    assert aioclient_mock.call_count == 10
    assert opp.components.oppio.get_core_info()["version_latest"] == "1.0.0"
    assert opp.components.oppio.is_oppio()


async def test_setup_api_panel(opp, aioclient_mock):
    """Test setup with API ping."""
    assert await async_setup_component(opp, "frontend", {})
    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(opp, "oppio", {})
        assert result

    panels = opp.data[frontend.DATA_PANELS]

    assert panels.get("oppio").to_response() == {
        "component_name": "custom",
        "icon": "opp:open-peer-power",
        "title": "Supervisor",
        "url_path": "oppio",
        "require_admin": True,
        "config": {
            "_panel_custom": {
                "embed_iframe": True,
                "js_url": "/api/oppio/app/entrypoint.js",
                "name": "oppio-main",
                "trust_external": False,
            }
        },
    }


async def test_setup_api_push_api_data(opp, aioclient_mock):
    """Test setup with API push."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(
            opp, "oppio", {"http": {"server_port": 9999}, "oppio": {}}
        )
        assert result

    assert aioclient_mock.call_count == 10
    assert not aioclient_mock.mock_calls[1][2]["ssl"]
    assert aioclient_mock.mock_calls[1][2]["port"] == 9999
    assert aioclient_mock.mock_calls[1][2]["watchdog"]


async def test_setup_api_push_api_data_server_host(opp, aioclient_mock):
    """Test setup with API push with active server host."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(
            opp,
            "oppio",
            {"http": {"server_port": 9999, "server_host": "127.0.0.1"}, "oppio": {}},
        )
        assert result

    assert aioclient_mock.call_count == 10
    assert not aioclient_mock.mock_calls[1][2]["ssl"]
    assert aioclient_mock.mock_calls[1][2]["port"] == 9999
    assert not aioclient_mock.mock_calls[1][2]["watchdog"]


async def test_setup_api_push_api_data_default(opp, aioclient_mock, opp_storage):
    """Test setup with API push default data."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(opp, "oppio", {"http": {}, "oppio": {}})
        assert result

    assert aioclient_mock.call_count == 10
    assert not aioclient_mock.mock_calls[1][2]["ssl"]
    assert aioclient_mock.mock_calls[1][2]["port"] == 8123
    refresh_token = aioclient_mock.mock_calls[1][2]["refresh_token"]
    oppio_user = await opp.auth.async_get_user(
        opp_storage[STORAGE_KEY]["data"]["oppio_user"]
    )
    assert oppio_user is not None
    assert oppio_user.system_generated
    assert len(oppio_user.groups) == 1
    assert oppio_user.groups[0].id == GROUP_ID_ADMIN
    for token in oppio_user.refresh_tokens.values():
        if token.token == refresh_token:
            break
    else:
        assert False, "refresh token not found"


async def test_setup_adds_admin_group_to_user(opp, aioclient_mock, opp_storage):
    """Test setup with API push default data."""
    # Create user without admin
    user = await opp.auth.async_create_system_user("Opp.io")
    assert not user.is_admin
    await opp.auth.async_create_refresh_token(user)

    opp_storage[STORAGE_KEY] = {
        "data": {"oppio_user": user.id},
        "key": STORAGE_KEY,
        "version": 1,
    }

    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(opp, "oppio", {"http": {}, "oppio": {}})
        assert result

    assert user.is_admin


async def test_setup_api_existing_oppio_user(opp, aioclient_mock, opp_storage):
    """Test setup with API push default data."""
    user = await opp.auth.async_create_system_user("Opp.io test")
    token = await opp.auth.async_create_refresh_token(user)
    opp_storage[STORAGE_KEY] = {"version": 1, "data": {"oppio_user": user.id}}
    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(opp, "oppio", {"http": {}, "oppio": {}})
        assert result

    assert aioclient_mock.call_count == 10
    assert not aioclient_mock.mock_calls[1][2]["ssl"]
    assert aioclient_mock.mock_calls[1][2]["port"] == 8123
    assert aioclient_mock.mock_calls[1][2]["refresh_token"] == token.token


async def test_setup_core_push_timezone(opp, aioclient_mock):
    """Test setup with API push default data."""
    opp.config.time_zone = "testzone"

    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(opp, "oppio", {"oppio": {}})
        assert result

    assert aioclient_mock.call_count == 10
    assert aioclient_mock.mock_calls[2][2]["timezone"] == "testzone"

    with patch("openpeerpower.util.dt.set_default_time_zone"):
        await opp.config.async_update(time_zone="America/New_York")
    await opp.async_block_till_done()
    assert aioclient_mock.mock_calls[-1][2]["timezone"] == "America/New_York"


async def test_setup_oppio_no_additional_data(opp, aioclient_mock):
    """Test setup with API push default data."""
    with patch.dict(os.environ, MOCK_ENVIRON), patch.dict(
        os.environ, {"OPPIO_TOKEN": "123456"}
    ):
        result = await async_setup_component(opp, "oppio", {"oppio": {}})
        assert result

    assert aioclient_mock.call_count == 10
    assert aioclient_mock.mock_calls[-1][3]["X-Oppio-Key"] == "123456"


async def test_fail_setup_without_environ_var(opp):
    """Fail setup if no environ variable set."""
    with patch.dict(os.environ, {}, clear=True):
        result = await async_setup_component(opp, "oppio", {})
        assert not result


async def test_warn_when_cannot_connect(opp, caplog):
    """Fail warn when we cannot connect."""
    with patch.dict(os.environ, MOCK_ENVIRON), patch(
        "openpeerpower.components.oppio.OppIO.is_connected",
        return_value=None,
    ):
        result = await async_setup_component(opp, "oppio", {})
        assert result

    assert opp.components.oppio.is_oppio()
    assert "Not connected with Opp.io / system too busy!" in caplog.text


async def test_service_register(oppio_env, opp):
    """Check if service will be setup."""
    assert await async_setup_component(opp, "oppio", {})
    assert opp.services.has_service("oppio", "addon_start")
    assert opp.services.has_service("oppio", "addon_stop")
    assert opp.services.has_service("oppio", "addon_restart")
    assert opp.services.has_service("oppio", "addon_update")
    assert opp.services.has_service("oppio", "addon_stdin")
    assert opp.services.has_service("oppio", "host_shutdown")
    assert opp.services.has_service("oppio", "host_reboot")
    assert opp.services.has_service("oppio", "host_reboot")
    assert opp.services.has_service("oppio", "snapshot_full")
    assert opp.services.has_service("oppio", "snapshot_partial")
    assert opp.services.has_service("oppio", "restore_full")
    assert opp.services.has_service("oppio", "restore_partial")


async def test_service_calls(oppio_env, opp, aioclient_mock):
    """Call service and check the API calls behind that."""
    assert await async_setup_component(opp, "oppio", {})

    aioclient_mock.post("http://127.0.0.1/addons/test/start", json={"result": "ok"})
    aioclient_mock.post("http://127.0.0.1/addons/test/stop", json={"result": "ok"})
    aioclient_mock.post("http://127.0.0.1/addons/test/restart", json={"result": "ok"})
    aioclient_mock.post("http://127.0.0.1/addons/test/update", json={"result": "ok"})
    aioclient_mock.post("http://127.0.0.1/addons/test/stdin", json={"result": "ok"})
    aioclient_mock.post("http://127.0.0.1/host/shutdown", json={"result": "ok"})
    aioclient_mock.post("http://127.0.0.1/host/reboot", json={"result": "ok"})
    aioclient_mock.post("http://127.0.0.1/snapshots/new/full", json={"result": "ok"})
    aioclient_mock.post("http://127.0.0.1/snapshots/new/partial", json={"result": "ok"})
    aioclient_mock.post(
        "http://127.0.0.1/snapshots/test/restore/full", json={"result": "ok"}
    )
    aioclient_mock.post(
        "http://127.0.0.1/snapshots/test/restore/partial", json={"result": "ok"}
    )

    await opp.services.async_call("oppio", "addon_start", {"addon": "test"})
    await opp.services.async_call("oppio", "addon_stop", {"addon": "test"})
    await opp.services.async_call("oppio", "addon_restart", {"addon": "test"})
    await opp.services.async_call("oppio", "addon_update", {"addon": "test"})
    await opp.services.async_call(
        "oppio", "addon_stdin", {"addon": "test", "input": "test"}
    )
    await opp.async_block_till_done()

    assert aioclient_mock.call_count == 8
    assert aioclient_mock.mock_calls[-1][2] == "test"

    await opp.services.async_call("oppio", "host_shutdown", {})
    await opp.services.async_call("oppio", "host_reboot", {})
    await opp.async_block_till_done()

    assert aioclient_mock.call_count == 10

    await opp.services.async_call("oppio", "snapshot_full", {})
    await opp.services.async_call(
        "oppio",
        "snapshot_partial",
        {"addons": ["test"], "folders": ["ssl"], "password": "123456"},
    )
    await opp.async_block_till_done()

    assert aioclient_mock.call_count == 12
    assert aioclient_mock.mock_calls[-1][2] == {
        "addons": ["test"],
        "folders": ["ssl"],
        "password": "123456",
    }

    await opp.services.async_call("oppio", "restore_full", {"snapshot": "test"})
    await opp.services.async_call(
        "oppio",
        "restore_partial",
        {
            "snapshot": "test",
            "openpeerpower": False,
            "addons": ["test"],
            "folders": ["ssl"],
            "password": "123456",
        },
    )
    await opp.async_block_till_done()

    assert aioclient_mock.call_count == 14
    assert aioclient_mock.mock_calls[-1][2] == {
        "addons": ["test"],
        "folders": ["ssl"],
        "openpeerpower": False,
        "password": "123456",
    }


async def test_service_calls_core(oppio_env, opp, aioclient_mock):
    """Call core service and check the API calls behind that."""
    assert await async_setup_component(opp, "oppio", {})

    aioclient_mock.post("http://127.0.0.1/openpeerpower/restart", json={"result": "ok"})
    aioclient_mock.post("http://127.0.0.1/openpeerpower/stop", json={"result": "ok"})

    await opp.services.async_call("openpeerpower", "stop")
    await opp.async_block_till_done()

    assert aioclient_mock.call_count == 4

    await opp.services.async_call("openpeerpower", "check_config")
    await opp.async_block_till_done()

    assert aioclient_mock.call_count == 4

    with patch(
        "openpeerpower.config.async_check_op_config_file", return_value=None
    ) as mock_check_config:
        await opp.services.async_call("openpeerpower", "restart")
        await opp.async_block_till_done()
        assert mock_check_config.called

    assert aioclient_mock.call_count == 5


async def test_entry_load_and_unload(opp):
    """Test loading and unloading config entry."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_opp(opp)
        assert await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()

    assert SENSOR_DOMAIN in opp.config.components
    assert BINARY_SENSOR_DOMAIN in opp.config.components
    assert ADDONS_COORDINATOR in opp.data

    assert await opp.config_entries.async_unload(config_entry.entry_id)
    await opp.async_block_till_done()
    assert ADDONS_COORDINATOR not in opp.data


async def test_migration_off_oppio(opp):
    """Test that when a user moves instance off Opp.io, config entry gets cleaned up."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    config_entry.add_to_opp(opp)
    assert not await opp.config_entries.async_setup(config_entry.entry_id)
    await opp.async_block_till_done()
    assert opp.config_entries.async_entries(DOMAIN) == []


async def test_device_registry_calls(opp):
    """Test device registry entries for oppio."""
    dev_reg = async_get(opp)
    supervisor_mock_data = {
        "addons": [
            {
                "name": "test",
                "slug": "test",
                "installed": True,
                "update_available": False,
                "version": "1.0.0",
                "version_latest": "1.0.0",
                "repository": "test",
                "url": "https://github.com/openpeerpower/addons/test",
            },
            {
                "name": "test2",
                "slug": "test2",
                "installed": True,
                "update_available": False,
                "version": "1.0.0",
                "version_latest": "1.0.0",
                "url": "https://github.com",
            },
        ]
    }
    os_mock_data = {
        "board": "odroid-n2",
        "boot": "A",
        "update_available": False,
        "version": "5.12",
        "version_latest": "5.12",
    }

    with patch.dict(os.environ, MOCK_ENVIRON), patch(
        "openpeerpower.components.oppio.OppIO.get_supervisor_info",
        return_value=supervisor_mock_data,
    ), patch(
        "openpeerpower.components.oppio.OppIO.get_os_info",
        return_value=os_mock_data,
    ):
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_opp(opp)
        assert await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()
        assert len(dev_reg.devices) == 3

    supervisor_mock_data = {
        "addons": [
            {
                "name": "test2",
                "slug": "test2",
                "installed": True,
                "update_available": False,
                "version": "1.0.0",
                "version_latest": "1.0.0",
                "url": "https://github.com",
            },
        ]
    }

    # Test that when addon is removed, next update will remove the add-on and subsequent updates won't
    with patch(
        "openpeerpower.components.oppio.OppIO.get_supervisor_info",
        return_value=supervisor_mock_data,
    ), patch(
        "openpeerpower.components.oppio.OppIO.get_os_info",
        return_value=os_mock_data,
    ):
        async_fire_time_changed(opp, dt_util.now() + timedelta(hours=1))
        await opp.async_block_till_done()
        assert len(dev_reg.devices) == 2

        async_fire_time_changed(opp, dt_util.now() + timedelta(hours=2))
        await opp.async_block_till_done()
        assert len(dev_reg.devices) == 2

    supervisor_mock_data = {
        "addons": [
            {
                "name": "test2",
                "slug": "test2",
                "installed": True,
                "update_available": False,
                "version": "1.0.0",
                "version_latest": "1.0.0",
                "url": "https://github.com",
            },
            {
                "name": "test3",
                "slug": "test3",
                "installed": True,
                "update_available": False,
                "version": "1.0.0",
                "version_latest": "1.0.0",
                "url": "https://github.com",
            },
        ]
    }

    # Test that when addon is added, next update will reload the entry so we register
    # a new device
    with patch(
        "openpeerpower.components.oppio.OppIO.get_supervisor_info",
        return_value=supervisor_mock_data,
    ), patch(
        "openpeerpower.components.oppio.OppIO.get_os_info",
        return_value=os_mock_data,
    ):
        async_fire_time_changed(opp, dt_util.now() + timedelta(hours=3))
        await opp.async_block_till_done()
        assert len(dev_reg.devices) == 3
