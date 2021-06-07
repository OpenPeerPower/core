"""Tests for the AdGuard Home config flow."""
import aiohttp

from openpeerpower import config_entries, data_entry_flow
from openpeerpower.components.adguard.const import DOMAIN
from openpeerpower.config_entries import SOURCE_USER
from openpeerpower.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    CONTENT_TYPE_JSON,
)
from openpeerpower.core import OpenPeerPower

from tests.common import MockConfigEntry
from tests.test_util.aiohttp import AiohttpClientMocker

FIXTURE_USER_INPUT = {
    CONF_HOST: "127.0.0.1",
    CONF_PORT: 3000,
    CONF_USERNAME: "user",
    CONF_PASSWORD: "pass",
    CONF_SSL: True,
    CONF_VERIFY_SSL: True,
}


async def test_show_authenticate_form(opp: OpenPeerPower) -> None:
    """Test that the setup form is served."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"


async def test_connection_error(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test we show user form on AdGuard Home connection error."""
    aioclient_mock.get(
        f"{'https' if FIXTURE_USER_INPUT[CONF_SSL] else 'http'}"
        f"://{FIXTURE_USER_INPUT[CONF_HOST]}"
        f":{FIXTURE_USER_INPUT[CONF_PORT]}/control/status",
        exc=aiohttp.ClientError,
    )

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=FIXTURE_USER_INPUT
    )

    assert result
    assert result.get("type") == data_entry_flow.RESULT_TYPE_FORM
    assert result.get("step_id") == "user"
    assert result.get("errors") == {"base": "cannot_connect"}


async def test_full_flow_implementation(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test registering an integration and finishing flow works."""
    aioclient_mock.get(
        f"{'https' if FIXTURE_USER_INPUT[CONF_SSL] else 'http'}"
        f"://{FIXTURE_USER_INPUT[CONF_HOST]}"
        f":{FIXTURE_USER_INPUT[CONF_PORT]}/control/status",
        json={"version": "v0.99.0"},
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result
    assert result.get("flow_id")
    assert result.get("type") == data_entry_flow.RESULT_TYPE_FORM
    assert result.get("step_id") == "user"

    result2 = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input=FIXTURE_USER_INPUT
    )
    assert result2
    assert result2.get("type") == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result2.get("title") == FIXTURE_USER_INPUT[CONF_HOST]

    data = result2.get("data")
    assert data
    assert data[CONF_HOST] == FIXTURE_USER_INPUT[CONF_HOST]
    assert data[CONF_PASSWORD] == FIXTURE_USER_INPUT[CONF_PASSWORD]
    assert data[CONF_PORT] == FIXTURE_USER_INPUT[CONF_PORT]
    assert data[CONF_SSL] == FIXTURE_USER_INPUT[CONF_SSL]
    assert data[CONF_USERNAME] == FIXTURE_USER_INPUT[CONF_USERNAME]
    assert data[CONF_VERIFY_SSL] == FIXTURE_USER_INPUT[CONF_VERIFY_SSL]


async def test_integration_already_exists(opp: OpenPeerPower) -> None:
    """Test we only allow a single config flow."""
    MockConfigEntry(
        domain=DOMAIN, data={"host": "mock-adguard", "port": "3000"}
    ).add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        data={"host": "mock-adguard", "port": "3000"},
        context={"source": config_entries.SOURCE_USER},
    )
    assert result
    assert result.get("type") == "abort"
    assert result.get("reason") == "already_configured"


async def test_oppio_already_configured(opp: OpenPeerPower) -> None:
    """Test we only allow a single config flow."""
    MockConfigEntry(
        domain=DOMAIN, data={"host": "mock-adguard", "port": "3000"}
    ).add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        data={"addon": "AdGuard Home Addon", "host": "mock-adguard", "port": "3000"},
        context={"source": config_entries.SOURCE_OPPIO},
    )
    assert result
    assert result.get("type") == data_entry_flow.RESULT_TYPE_ABORT
    assert result.get("reason") == "already_configured"


async def test_oppio_ignored(opp: OpenPeerPower) -> None:
    """Test we supervisor discovered instance can be ignored."""
    MockConfigEntry(domain=DOMAIN, source=config_entries.SOURCE_IGNORE).add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        data={"addon": "AdGuard Home Addon", "host": "mock-adguard", "port": "3000"},
        context={"source": config_entries.SOURCE_OPPIO},
    )
    assert result
    assert result.get("type") == data_entry_flow.RESULT_TYPE_ABORT
    assert result.get("reason") == "already_configured"


async def test_oppio_confirm(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test we can finish a config flow."""
    aioclient_mock.get(
        "http://mock-adguard:3000/control/status",
        json={"version": "v0.99.0"},
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        data={"addon": "AdGuard Home Addon", "host": "mock-adguard", "port": 3000},
        context={"source": config_entries.SOURCE_OPPIO},
    )
    assert result
    assert result.get("type") == data_entry_flow.RESULT_TYPE_FORM
    assert result.get("step_id") == "oppio_confirm"
    assert result.get("description_placeholders") == {"addon": "AdGuard Home Addon"}

    result2 = await opp.config_entries.flow.async_configure(result["flow_id"], {})

    assert result2
    assert result2.get("type") == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result2.get("title") == "AdGuard Home Addon"

    data = result2.get("data")
    assert data
    assert data[CONF_HOST] == "mock-adguard"
    assert data[CONF_PASSWORD] is None
    assert data[CONF_PORT] == 3000
    assert data[CONF_SSL] is False
    assert data[CONF_USERNAME] is None
    assert data[CONF_VERIFY_SSL]


async def test_oppio_connection_error(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test we show Opp.io confirm form on AdGuard Home connection error."""
    aioclient_mock.get(
        "http://mock-adguard:3000/control/status", exc=aiohttp.ClientError
    )

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        data={"addon": "AdGuard Home Addon", "host": "mock-adguard", "port": 3000},
        context={"source": config_entries.SOURCE_OPPIO},
    )

    result = await opp.config_entries.flow.async_configure(result["flow_id"], {})

    assert result
    assert result.get("type") == data_entry_flow.RESULT_TYPE_FORM
    assert result.get("step_id") == "oppio_confirm"
    assert result.get("errors") == {"base": "cannot_connect"}
