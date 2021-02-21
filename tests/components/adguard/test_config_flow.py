"""Tests for the AdGuard Home config flow."""

from unittest.mock import patch

import aiohttp

from openpeerpower import config_entries, data_entry_flow
from openpeerpower.components.adguard import config_flow
from openpeerpower.components.adguard.const import DOMAIN
from openpeerpower.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    CONTENT_TYPE_JSON,
)

from tests.common import MockConfigEntry

FIXTURE_USER_INPUT = {
    CONF_HOST: "127.0.0.1",
    CONF_PORT: 3000,
    CONF_USERNAME: "user",
    CONF_PASSWORD: "pass",
    CONF_SSL: True,
    CONF_VERIFY_SSL: True,
}


async def test_show_authenticate_form.opp):
    """Test that the setup form is served."""
    flow = config_flow.AdGuardHomeFlowHandler()
    flow.opp = opp
    result = await flow.async_step_user(user_input=None)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"


async def test_connection_error.opp, aioclient_mock):
    """Test we show user form on AdGuard Home connection error."""
    aioclient_mock.get(
        f"{'https' if FIXTURE_USER_INPUT[CONF_SSL] else 'http'}"
        f"://{FIXTURE_USER_INPUT[CONF_HOST]}"
        f":{FIXTURE_USER_INPUT[CONF_PORT]}/control/status",
        exc=aiohttp.ClientError,
    )

    flow = config_flow.AdGuardHomeFlowHandler()
    flow.opp = opp
    result = await flow.async_step_user(user_input=FIXTURE_USER_INPUT)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_full_flow_implementation.opp, aioclient_mock):
    """Test registering an integration and finishing flow works."""
    aioclient_mock.get(
        f"{'https' if FIXTURE_USER_INPUT[CONF_SSL] else 'http'}"
        f"://{FIXTURE_USER_INPUT[CONF_HOST]}"
        f":{FIXTURE_USER_INPUT[CONF_PORT]}/control/status",
        json={"version": "v0.99.0"},
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    flow = config_flow.AdGuardHomeFlowHandler()
    flow.opp = opp
    result = await flow.async_step_user(user_input=None)
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await flow.async_step_user(user_input=FIXTURE_USER_INPUT)
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == FIXTURE_USER_INPUT[CONF_HOST]
    assert result["data"][CONF_HOST] == FIXTURE_USER_INPUT[CONF_HOST]
    assert result["data"][CONF_PASSWORD] == FIXTURE_USER_INPUT[CONF_PASSWORD]
    assert result["data"][CONF_PORT] == FIXTURE_USER_INPUT[CONF_PORT]
    assert result["data"][CONF_SSL] == FIXTURE_USER_INPUT[CONF_SSL]
    assert result["data"][CONF_USERNAME] == FIXTURE_USER_INPUT[CONF_USERNAME]
    assert result["data"][CONF_VERIFY_SSL] == FIXTURE_USER_INPUT[CONF_VERIFY_SSL]


async def test_integration_already_exists.opp):
    """Test we only allow a single config flow."""
    MockConfigEntry(domain=DOMAIN).add_to_opp.opp)

    result = await opp..config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == "abort"
    assert result["reason"] == "single_instance_allowed"


async def test_oppio_single_instance.opp):
    """Test we only allow a single config flow."""
    MockConfigEntry(
        domain="adguard", data={"host": "mock-adguard", "port": "3000"}
    ).add_to_opp.opp)

    result = await opp..config_entries.flow.async_init(
        "adguard",
        data={"addon": "AdGuard Home Addon", "host": "mock-adguard", "port": "3000"},
        context={"source": "oppio"},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_oppio_update_instance_not_running.opp):
    """Test we only allow a single config flow."""
    entry = MockConfigEntry(
        domain="adguard", data={"host": "mock-adguard", "port": "3000"}
    )
    entry.add_to_opp.opp)
    assert entry.state == config_entries.ENTRY_STATE_NOT_LOADED

    result = await opp..config_entries.flow.async_init(
        "adguard",
        data={
            "addon": "AdGuard Home Addon",
            "host": "mock-adguard-updated",
            "port": "3000",
        },
        context={"source": "oppio"},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "existing_instance_updated"


async def test_oppio_update_instance_running.opp, aioclient_mock):
    """Test we only allow a single config flow."""
    aioclient_mock.get(
        "http://mock-adguard-updated:3000/control/status",
        json={"version": "v0.99.0"},
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )
    aioclient_mock.get(
        "http://mock-adguard:3000/control/status",
        json={"version": "v0.99.0"},
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    entry = MockConfigEntry(
        domain="adguard",
        data={
            "host": "mock-adguard",
            "port": "3000",
            "verify_ssl": False,
            "username": None,
            "password": None,
            "ssl": False,
        },
    )
    entry.add_to_opp.opp)

    with patch.object(
       .opp.config_entries,
        "async_forward_entry_setup",
        return_value=True,
    ) as mock_load:
        assert await opp..config_entries.async_setup(entry.entry_id)
        assert entry.state == config_entries.ENTRY_STATE_LOADED
        assert len(mock_load.mock_calls) == 2

    with patch.object(
       .opp.config_entries,
        "async_forward_entry_unload",
        return_value=True,
    ) as mock_unload, patch.object(
       .opp.config_entries,
        "async_forward_entry_setup",
        return_value=True,
    ) as mock_load:
        result = await opp..config_entries.flow.async_init(
            "adguard",
            data={
                "addon": "AdGuard Home Addon",
                "host": "mock-adguard-updated",
                "port": "3000",
            },
            context={"source": "oppio"},
        )
        assert len(mock_unload.mock_calls) == 2
        assert len(mock_load.mock_calls) == 2

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "existing_instance_updated"
    assert entry.data["host"] == "mock-adguard-updated"


async def test_oppio_confirm.opp, aioclient_mock):
    """Test we can finish a config flow."""
    aioclient_mock.get(
        "http://mock-adguard:3000/control/status",
        json={"version": "v0.99.0"},
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    result = await opp..config_entries.flow.async_init(
        "adguard",
        data={"addon": "AdGuard Home Addon", "host": "mock-adguard", "port": 3000},
        context={"source": "oppio"},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "oppio_confirm"
    assert result["description_placeholders"] == {"addon": "AdGuard Home Addon"}

    result = await opp..config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "AdGuard Home Addon"
    assert result["data"][CONF_HOST] == "mock-adguard"
    assert result["data"][CONF_PASSWORD] is None
    assert result["data"][CONF_PORT] == 3000
    assert result["data"][CONF_SSL] is False
    assert result["data"][CONF_USERNAME] is None
    assert result["data"][CONF_VERIFY_SSL]


async def test_oppio_connection_error.opp, aioclient_mock):
    """Test we show Opp.io confirm form on AdGuard Home connection error."""
    aioclient_mock.get(
        "http://mock-adguard:3000/control/status", exc=aiohttp.ClientError
    )

    result = await opp..config_entries.flow.async_init(
        "adguard",
        data={"addon": "AdGuard Home Addon", "host": "mock-adguard", "port": 3000},
        context={"source": "oppio"},
    )

    result = await opp..config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "oppio_confirm"
    assert result["errors"] == {"base": "cannot_connect"}
