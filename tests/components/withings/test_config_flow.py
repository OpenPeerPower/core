"""Tests for config flow."""
from aiohttp.test_utils import TestClient

from openpeerpower.components.withings import const
from openpeerpower.config import async_process_op_core_config
from openpeerpower.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_EXTERNAL_URL,
    CONF_UNIT_SYSTEM,
    CONF_UNIT_SYSTEM_METRIC,
)
from openpeerpower.core import DOMAIN as HA_DOMAIN, OpenPeerPower
from openpeerpower.helpers import config_entry_oauth2_flow
from openpeerpower.helpers.config_entry_oauth2_flow import AUTH_CALLBACK_PATH
from openpeerpower.setup import async_setup_component

from tests.common import MockConfigEntry


async def test_config_non_unique_profile.opp: OpenPeerPower) -> None:
    """Test setup a non-unique profile."""
    config_entry = MockConfigEntry(
        domain=const.DOMAIN, data={const.PROFILE: "person0"}, unique_id="0"
    )
    config_entry.add_to.opp.opp)

    result = await opp.config_entries.flow.async_init(
        const.DOMAIN, context={"source": "profile"}, data={const.PROFILE: "person0"}
    )

    assert result
    assert result["errors"]["base"] == "already_configured"


async def test_config_reauth_profile(
    opp. OpenPeerPower, aiohttp_client, aioclient_mock
) -> None:
    """Test reauth an existing profile re-creates the config entry."""
    opp.config = {
        HA_DOMAIN: {
            CONF_UNIT_SYSTEM: CONF_UNIT_SYSTEM_METRIC,
            CONF_EXTERNAL_URL: "http://127.0.0.1:8080/",
        },
        const.DOMAIN: {
            CONF_CLIENT_ID: "my_client_id",
            CONF_CLIENT_SECRET: "my_client_secret",
            const.CONF_USE_WEBHOOK: False,
        },
    }
    await async_process_op_core_config(opp, opp_config.get(HA_DOMAIN))
    assert await async_setup_component.opp, const.DOMAIN, opp_config)
    await opp.async_block_till_done()

    config_entry = MockConfigEntry(
        domain=const.DOMAIN, data={const.PROFILE: "person0"}, unique_id="0"
    )
    config_entry.add_to.opp.opp)

    result = await opp.config_entries.flow.async_init(
        const.DOMAIN, context={"source": "reauth", "profile": "person0"}
    )
    assert result
    assert result["type"] == "form"
    assert result["step_id"] == "reauth"
    assert result["description_placeholders"] == {const.PROFILE: "person0"}

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    # pylint: disable=protected-access
    state = config_entry_oauth2_flow._encode_jwt(
        opp.
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    client: TestClient = await aiohttp_client.opp.http.app)
    resp = await client.get(f"{AUTH_CALLBACK_PATH}?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        "https://account.withings.com/oauth2/token",
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
            "userid": "0",
        },
    )

    result = await opp.config_entries.flow.async_configure(result["flow_id"])
    assert result
    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"

    entries = opp.config_entries.async_entries(const.DOMAIN)
    assert entries
    assert entries[0].data["token"]["refresh_token"] == "mock-refresh-token"
