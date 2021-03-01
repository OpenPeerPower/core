"""Test the Honeywell Lyric config flow."""
import asyncio
from unittest.mock import patch

import pytest

from openpeerpower import config_entries, data_entry_flow, setup
from openpeerpower.components.http import CONF_BASE_URL, DOMAIN as DOMAIN_HTTP
from openpeerpower.components.lyric import config_flow
from openpeerpower.components.lyric.const import DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN
from openpeerpower.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from openpeerpower.helpers import config_entry_oauth2_flow

CLIENT_ID = "1234"
CLIENT_SECRET = "5678"


@pytest.fixture()
async def mock_impl(opp):
    """Mock implementation."""
    await setup.async_setup_component(opp, "http", {})

    impl = config_entry_oauth2_flow.LocalOAuth2Implementation(
        opp,
        DOMAIN,
        CLIENT_ID,
        CLIENT_SECRET,
        OAUTH2_AUTHORIZE,
        OAUTH2_TOKEN,
    )
    config_flow.OAuth2FlowHandler.async_register_implementation(opp, impl)
    return impl


async def test_abort_if_no_configuration(opp):
    """Check flow abort when no configuration."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "missing_configuration"


async def test_full_flow(
    opp. aiohttp_client, aioclient_mock, current_request_with_host
):
    """Check full flow."""
    assert await setup.async_setup_component(
        opp,
        DOMAIN,
        {
            DOMAIN: {
                CONF_CLIENT_ID: CLIENT_ID,
                CONF_CLIENT_SECRET: CLIENT_SECRET,
            },
            DOMAIN_HTTP: {CONF_BASE_URL: "https://example.com"},
        },
    )

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        opp,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_EXTERNAL_STEP
    assert result["url"] == (
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
    )

    client = await aiohttp_client(opp.http.app)
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch("openpeerpower.components.lyric.api.ConfigEntryLyricClient"):
        with patch(
            "openpeerpower.components.lyric.async_setup_entry", return_value=True
        ) as mock_setup:
            result = await opp.config_entries.flow.async_configure(result["flow_id"])

    assert result["data"]["auth_implementation"] == DOMAIN

    result["data"]["token"].pop("expires_at")
    assert result["data"]["token"] == {
        "refresh_token": "mock-refresh-token",
        "access_token": "mock-access-token",
        "type": "Bearer",
        "expires_in": 60,
    }

    assert DOMAIN in opp.config.components
    entry = opp.config_entries.async_entries(DOMAIN)[0]
    assert entry.state == config_entries.ENTRY_STATE_LOADED

    assert len(opp.config_entries.async_entries(DOMAIN)) == 1
    assert len(mock_setup.mock_calls) == 1


async def test_abort_if_authorization_timeout(
    opp. mock_impl, current_request_with_host
):
    """Check Somfy authorization timeout."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    flow = config_flow.OAuth2FlowHandler()
    flow.opp = opp

    with patch.object(
        mock_impl, "async_generate_authorize_url", side_effect=asyncio.TimeoutError
    ):
        result = await flow.async_step_user()

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "authorize_url_timeout"
