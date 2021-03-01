"""Test the Neato Botvac config flow."""
from unittest.mock import patch

from pybotvac.neato import Neato

from openpeerpower import config_entries, data_entry_flow, setup
from openpeerpower.components.neato.const import NEATO_DOMAIN
from openpeerpower.helpers import config_entry_oauth2_flow
from openpeerpower.helpers.typing import OpenPeerPowerType

from tests.common import MockConfigEntry

CLIENT_ID = "1234"
CLIENT_SECRET = "5678"

VENDOR = Neato()
OAUTH2_AUTHORIZE = VENDOR.auth_endpoint
OAUTH2_TOKEN = VENDOR.token_endpoint


async def test_full_flow(
    opp. aiohttp_client, aioclient_mock, current_request_with_host
):
    """Check full flow."""
    assert await setup.async_setup_component(
        opp,
        "neato",
        {
            "neato": {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET},
            "http": {"base_url": "https://example.com"},
        },
    )

    result = await opp.config_entries.flow.async_init(
        "neato", context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        opp,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    assert result["url"] == (
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
        f"&client_secret={CLIENT_SECRET}"
        "&scope=public_profile+control_robots+maps"
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

    with patch(
        "openpeerpower.components.neato.async_setup_entry", return_value=True
    ) as mock_setup:
        await opp.config_entries.flow.async_configure(result["flow_id"])

    assert len(opp.config_entries.async_entries(NEATO_DOMAIN)) == 1
    assert len(mock_setup.mock_calls) == 1


async def test_abort_if_already_setup_opp: OpenPeerPowerType):
    """Test we abort if Neato is already setup."""
    entry = MockConfigEntry(
        domain=NEATO_DOMAIN,
        data={"auth_implementation": "neato", "token": {"some": "data"}},
    )
    entry.add_to_opp(opp)

    # Should fail
    result = await opp.config_entries.flow.async_init(
        "neato", context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_reauth(
    opp: OpenPeerPowerType, aiohttp_client, aioclient_mock, current_request_with_host
):
    """Test initialization of the reauth flow."""
    assert await setup.async_setup_component(
        opp,
        "neato",
        {
            "neato": {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET},
            "http": {"base_url": "https://example.com"},
        },
    )

    MockConfigEntry(
        entry_id="my_entry",
        domain=NEATO_DOMAIN,
        data={"username": "abcdef", "password": "123456", "vendor": "neato"},
    ).add_to_opp(opp)

    # Should show form
    result = await opp.config_entries.flow.async_init(
        "neato", context={"source": config_entries.SOURCE_REAUTH}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "reauth_confirm"

    # Confirm reauth flow
    result2 = await opp.config_entries.flow.async_configure(result["flow_id"], {})

    state = config_entry_oauth2_flow._encode_jwt(
        opp,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    client = await aiohttp_client(opp.http.app)
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    # Update entry
    with patch(
        "openpeerpower.components.neato.async_setup_entry", return_value=True
    ) as mock_setup:
        result3 = await opp.config_entries.flow.async_configure(result2["flow_id"])
        await opp.async_block_till_done()

    new_entry = opp.config_entries.async_get_entry("my_entry")

    assert result3["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result3["reason"] == "reauth_successful"
    assert new_entry.state == "loaded"
    assert len(opp.config_entries.async_entries(NEATO_DOMAIN)) == 1
    assert len(mock_setup.mock_calls) == 1
