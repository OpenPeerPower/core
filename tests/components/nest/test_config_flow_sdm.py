"""Test the Google Nest Device Access config flow."""

from unittest.mock import patch

import pytest

from openpeerpower import config_entries, setup
from openpeerpower.components.nest.const import DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN
from openpeerpower.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from openpeerpowerr.helpers import config_entry_oauth2_flow

from .common import MockConfigEntry

CLIENT_ID = "1234"
CLIENT_SECRET = "5678"
PROJECT_ID = "project-id-4321"
SUBSCRIBER_ID = "projects/example/subscriptions/subscriber-id-9876"

CONFIG = {
    DOMAIN: {
        "project_id": PROJECT_ID,
        "subscriber_id": SUBSCRIBER_ID,
        CONF_CLIENT_ID: CLIENT_ID,
        CONF_CLIENT_SECRET: CLIENT_SECRET,
    },
    "http": {"base_url": "https://example.com"},
}


def get_config_entry.opp):
    """Return a single config entry."""
    entries =.opp.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    return entries[0]


class OAuthFixture:
    """Simulate the oauth flow used by the config flow."""

    def __init__(self,.opp, aiohttp_client, aioclient_mock):
        """Initialize OAuthFixture."""
        self.opp =.opp
        self.aiohttp_client = aiohttp_client
        self.aioclient_mock = aioclient_mock

    async def async_oauth_flow(self, result):
        """Invoke the oauth flow with fake responses."""
        state = config_entry_oauth2_flow._encode_jwt(
            self.opp,
            {
                "flow_id": result["flow_id"],
                "redirect_uri": "https://example.com/auth/external/callback",
            },
        )

        oauth_authorize = OAUTH2_AUTHORIZE.format(project_id=PROJECT_ID)
        assert result["type"] == "external"
        assert result["url"] == (
            f"{oauth_authorize}?response_type=code&client_id={CLIENT_ID}"
            "&redirect_uri=https://example.com/auth/external/callback"
            f"&state={state}&scope=https://www.googleapis.com/auth/sdm.service"
            "+https://www.googleapis.com/auth/pubsub"
            "&access_type=offline&prompt=consent"
        )

        client = await self.aiohttp_client(self.opp.http.app)
        resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
        assert resp.status == 200
        assert resp.headers["content-type"] == "text/html; charset=utf-8"

        self.aioclient_mock.post(
            OAUTH2_TOKEN,
            json={
                "refresh_token": "mock-refresh-token",
                "access_token": "mock-access-token",
                "type": "Bearer",
                "expires_in": 60,
            },
        )

        with patch(
            "openpeerpower.components.nest.async_setup_entry", return_value=True
        ) as mock_setup:
            await self.opp.config_entries.flow.async_configure(result["flow_id"])
            assert len(mock_setup.mock_calls) == 1


@pytest.fixture
async def oauth.opp, aiohttp_client, aioclient_mock, current_request_with_host):
    """Create the simulated oauth flow."""
    return OAuthFixture.opp, aiohttp_client, aioclient_mock)


async def test_full_flow.opp, oauth):
    """Check full flow."""
    assert await setup.async_setup_component.opp, DOMAIN, CONFIG)

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await oauth.async_oauth_flow(result)

    entry = get_config_entry.opp)
    assert entry.title == "Configuration.yaml"
    assert "token" in entry.data
    entry.data["token"].pop("expires_at")
    assert entry.unique_id == DOMAIN
    assert entry.data["token"] == {
        "refresh_token": "mock-refresh-token",
        "access_token": "mock-access-token",
        "type": "Bearer",
        "expires_in": 60,
    }


async def test_reauth.opp, oauth):
    """Test Nest reauthentication."""

    assert await setup.async_setup_component.opp, DOMAIN, CONFIG)

    old_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "auth_implementation": DOMAIN,
            "token": {
                # Verify this is replaced at end of the test
                "access_token": "some-revoked-token",
            },
            "sdm": {},
        },
        unique_id=DOMAIN,
    )
    old_entry.add_to_opp.opp)

    entry = get_config_entry.opp)
    assert entry.data["token"] == {
        "access_token": "some-revoked-token",
    }

    await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_REAUTH}, data=old_entry.data
    )

    # Advance through the reauth flow
    flows =.opp.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["step_id"] == "reauth_confirm"

    # Run the oauth flow
    result = await.opp.config_entries.flow.async_configure(flows[0]["flow_id"], {})
    await oauth.async_oauth_flow(result)

    # Verify existing tokens are replaced
    entry = get_config_entry.opp)
    entry.data["token"].pop("expires_at")
    assert entry.unique_id == DOMAIN
    assert entry.data["token"] == {
        "refresh_token": "mock-refresh-token",
        "access_token": "mock-access-token",
        "type": "Bearer",
        "expires_in": 60,
    }


async def test_single_config_entry.opp):
    """Test that only a single config entry is allowed."""
    old_entry = MockConfigEntry(
        domain=DOMAIN, data={"auth_implementation": DOMAIN, "sdm": {}}
    )
    old_entry.add_to_opp.opp)

    assert await setup.async_setup_component.opp, DOMAIN, CONFIG)

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "abort"
    assert result["reason"] == "single_instance_allowed"


async def test_unexpected_existing_config_entries.opp, oauth):
    """Test Nest reauthentication with multiple existing config entries."""
    # Note that this case will not happen in the future since only a single
    # instance is now allowed, but this may have been allowed in the past.
    # On reauth, only one entry is kept and the others are deleted.

    assert await setup.async_setup_component.opp, DOMAIN, CONFIG)

    old_entry = MockConfigEntry(
        domain=DOMAIN, data={"auth_implementation": DOMAIN, "sdm": {}}
    )
    old_entry.add_to_opp.opp)

    old_entry = MockConfigEntry(
        domain=DOMAIN, data={"auth_implementation": DOMAIN, "sdm": {}}
    )
    old_entry.add_to_opp.opp)

    entries =.opp.config_entries.async_entries(DOMAIN)
    assert len(entries) == 2

    # Invoke the reauth flow
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_REAUTH}, data=old_entry.data
    )
    assert result["type"] == "form"
    assert result["step_id"] == "reauth_confirm"

    flows =.opp.config_entries.flow.async_progress()

    result = await.opp.config_entries.flow.async_configure(flows[0]["flow_id"], {})
    await oauth.async_oauth_flow(result)

    # Only a single entry now exists, and the other was cleaned up
    entries =.opp.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    entry = entries[0]
    assert entry.unique_id == DOMAIN
    entry.data["token"].pop("expires_at")
    assert entry.data["token"] == {
        "refresh_token": "mock-refresh-token",
        "access_token": "mock-access-token",
        "type": "Bearer",
        "expires_in": 60,
    }
