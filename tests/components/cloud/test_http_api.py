"""Tests for the HTTP API for the cloud component."""
import asyncio
from ipaddress import ip_network
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import aiohttp
from opp_nabucasa import thingtalk, voice
from opp_nabucasa.auth import Unauthenticated, UnknownError
from opp_nabucasa.const import STATE_CONNECTED
from jose import jwt
import pytest

from openpeerpower.auth.providers import trusted_networks as tn_auth
from openpeerpower.components.alexa import errors as alexa_errors
from openpeerpower.components.alexa.entities import LightCapabilities
from openpeerpower.components.cloud.const import DOMAIN, RequireRelink
from openpeerpower.components.google_assistant.helpers import GoogleEntity
from openpeerpower.const import HTTP_INTERNAL_SERVER_ERROR
from openpeerpower.core import State

from . import mock_cloud, mock_cloud_prefs

from tests.components.google_assistant import MockConfig

SUBSCRIPTION_INFO_URL = "https://api-test.opp.io/subscription_info"


@pytest.fixture(name="mock_auth")
def mock_auth_fixture():
    """Mock check token."""
    with patch(.opp_nabucasa.auth.CognitoAuth.async_check_token"):
        yield


@pytest.fixture(name="mock_cloud_login")
def mock_cloud_login_fixture(opp, setup_api):
    """Mock cloud is logged in."""
    opp.data[DOMAIN].id_token = jwt.encode(
        {
            "email": "hello@open-peer-power.io",
            "custom:sub-exp": "2018-01-03",
            "cognito:username": "abcdefghjkl",
        },
        "test",
    )


@pytest.fixture(autouse=True, name="setup_api")
def setup_api_fixture(opp, aioclient_mock):
    """Initialize HTTP API."""
    opp.loop.run_until_complete(
        mock_cloud(
            opp,
            {
                "mode": "development",
                "cognito_client_id": "cognito_client_id",
                "user_pool_id": "user_pool_id",
                "region": "region",
                "relayer": "relayer",
                "subscription_info_url": SUBSCRIPTION_INFO_URL,
                "google_actions": {"filter": {"include_domains": "light"}},
                "alexa": {
                    "filter": {"include_entities": ["light.kitchen", "switch.ac"]}
                },
            },
        )
    )
    return mock_cloud_prefs.opp)


@pytest.fixture(name="cloud_client")
def cloud_client_fixture(opp, opp_client):
    """Fixture that can fetch from the cloud client."""
    with patch(.opp_nabucasa.Cloud.write_user_info"):
        yield.opp.loop.run_until_complete.opp_client())


@pytest.fixture(name="mock_cognito")
def mock_cognito_fixture():
    """Mock warrant."""
    with patch(.opp_nabucasa.auth.CognitoAuth._cognito") as mock_cog:
        yield mock_cog()


async def test_google_actions_sync(mock_cognito, mock_cloud_login, cloud_client):
    """Test syncing Google Actions."""
    with patch(
         opp.nabucasa.cloud_api.async_google_actions_request_sync",
        return_value=Mock(status=200),
    ) as mock_request_sync:
        req = await cloud_client.post("/api/cloud/google_actions/sync")
        assert req.status == 200
        assert len(mock_request_sync.mock_calls) == 1


async def test_google_actions_sync_fails(mock_cognito, mock_cloud_login, cloud_client):
    """Test syncing Google Actions gone bad."""
    with patch(
         opp.nabucasa.cloud_api.async_google_actions_request_sync",
        return_value=Mock(status=HTTP_INTERNAL_SERVER_ERROR),
    ) as mock_request_sync:
        req = await cloud_client.post("/api/cloud/google_actions/sync")
        assert req.status == HTTP_INTERNAL_SERVER_ERROR
        assert len(mock_request_sync.mock_calls) == 1


async def test_login_view(opp, cloud_client):
    """Test logging in."""
    opp.data["cloud"] = MagicMock(login=AsyncMock())

    req = await cloud_client.post(
        "/api/cloud/login", json={"email": "my_username", "password": "my_password"}
    )

    assert req.status == 200
    result = await req.json()
    assert result == {"success": True}


async def test_login_view_random_exception(cloud_client):
    """Try logging in with invalid JSON."""
    with patch("async_timeout.timeout", side_effect=ValueError("Boom")):
        req = await cloud_client.post(
            "/api/cloud/login", json={"email": "my_username", "password": "my_password"}
        )
    assert req.status == 502
    resp = await req.json()
    assert resp == {"code": "valueerror", "message": "Unexpected error: Boom"}


async def test_login_view_invalid_json(cloud_client):
    """Try logging in with invalid JSON."""
    with patch(.opp_nabucasa.auth.CognitoAuth.async_login") as mock_login:
        req = await cloud_client.post("/api/cloud/login", data="Not JSON")
    assert req.status == 400
    assert len(mock_login.mock_calls) == 0


async def test_login_view_invalid_schema(cloud_client):
    """Try logging in with invalid schema."""
    with patch(.opp_nabucasa.auth.CognitoAuth.async_login") as mock_login:
        req = await cloud_client.post("/api/cloud/login", json={"invalid": "schema"})
    assert req.status == 400
    assert len(mock_login.mock_calls) == 0


async def test_login_view_request_timeout(cloud_client):
    """Test request timeout while trying to log in."""
    with patch(
         opp.nabucasa.auth.CognitoAuth.async_login", side_effect=asyncio.TimeoutError
    ):
        req = await cloud_client.post(
            "/api/cloud/login", json={"email": "my_username", "password": "my_password"}
        )

    assert req.status == 502


async def test_login_view_invalid_credentials(cloud_client):
    """Test logging in with invalid credentials."""
    with patch(
         opp.nabucasa.auth.CognitoAuth.async_login", side_effect=Unauthenticated
    ):
        req = await cloud_client.post(
            "/api/cloud/login", json={"email": "my_username", "password": "my_password"}
        )

    assert req.status == 401


async def test_login_view_unknown_error(cloud_client):
    """Test unknown error while logging in."""
    with patch(.opp_nabucasa.auth.CognitoAuth.async_login", side_effect=UnknownError):
        req = await cloud_client.post(
            "/api/cloud/login", json={"email": "my_username", "password": "my_password"}
        )

    assert req.status == 502


async def test_logout_view(opp, cloud_client):
    """Test logging out."""
    cloud = opp.data["cloud"] = MagicMock()
    cloud.logout = AsyncMock(return_value=None)
    req = await cloud_client.post("/api/cloud/logout")
    assert req.status == 200
    data = await req.json()
    assert data == {"message": "ok"}
    assert len(cloud.logout.mock_calls) == 1


async def test_logout_view_request_timeout(opp, cloud_client):
    """Test timeout while logging out."""
    cloud = opp.data["cloud"] = MagicMock()
    cloud.logout.side_effect = asyncio.TimeoutError
    req = await cloud_client.post("/api/cloud/logout")
    assert req.status == 502


async def test_logout_view_unknown_error(opp, cloud_client):
    """Test unknown error while logging out."""
    cloud = opp.data["cloud"] = MagicMock()
    cloud.logout.side_effect = UnknownError
    req = await cloud_client.post("/api/cloud/logout")
    assert req.status == 502


async def test_register_view(mock_cognito, cloud_client):
    """Test logging out."""
    req = await cloud_client.post(
        "/api/cloud/register", json={"email": "hello@bla.com", "password": "falcon42"}
    )
    assert req.status == 200
    assert len(mock_cognito.register.mock_calls) == 1
    result_email, result_pass = mock_cognito.register.mock_calls[0][1]
    assert result_email == "hello@bla.com"
    assert result_pass == "falcon42"


async def test_register_view_bad_data(mock_cognito, cloud_client):
    """Test logging out."""
    req = await cloud_client.post(
        "/api/cloud/register", json={"email": "hello@bla.com", "not_password": "falcon"}
    )
    assert req.status == 400
    assert len(mock_cognito.logout.mock_calls) == 0


async def test_register_view_request_timeout(mock_cognito, cloud_client):
    """Test timeout while logging out."""
    mock_cognito.register.side_effect = asyncio.TimeoutError
    req = await cloud_client.post(
        "/api/cloud/register", json={"email": "hello@bla.com", "password": "falcon42"}
    )
    assert req.status == 502


async def test_register_view_unknown_error(mock_cognito, cloud_client):
    """Test unknown error while logging out."""
    mock_cognito.register.side_effect = UnknownError
    req = await cloud_client.post(
        "/api/cloud/register", json={"email": "hello@bla.com", "password": "falcon42"}
    )
    assert req.status == 502


async def test_forgot_password_view(mock_cognito, cloud_client):
    """Test logging out."""
    req = await cloud_client.post(
        "/api/cloud/forgot_password", json={"email": "hello@bla.com"}
    )
    assert req.status == 200
    assert len(mock_cognito.initiate_forgot_password.mock_calls) == 1


async def test_forgot_password_view_bad_data(mock_cognito, cloud_client):
    """Test logging out."""
    req = await cloud_client.post(
        "/api/cloud/forgot_password", json={"not_email": "hello@bla.com"}
    )
    assert req.status == 400
    assert len(mock_cognito.initiate_forgot_password.mock_calls) == 0


async def test_forgot_password_view_request_timeout(mock_cognito, cloud_client):
    """Test timeout while logging out."""
    mock_cognito.initiate_forgot_password.side_effect = asyncio.TimeoutError
    req = await cloud_client.post(
        "/api/cloud/forgot_password", json={"email": "hello@bla.com"}
    )
    assert req.status == 502


async def test_forgot_password_view_unknown_error(mock_cognito, cloud_client):
    """Test unknown error while logging out."""
    mock_cognito.initiate_forgot_password.side_effect = UnknownError
    req = await cloud_client.post(
        "/api/cloud/forgot_password", json={"email": "hello@bla.com"}
    )
    assert req.status == 502


async def test_forgot_password_view_aiohttp_error(mock_cognito, cloud_client):
    """Test unknown error while logging out."""
    mock_cognito.initiate_forgot_password.side_effect = aiohttp.ClientResponseError(
        Mock(), Mock()
    )
    req = await cloud_client.post(
        "/api/cloud/forgot_password", json={"email": "hello@bla.com"}
    )
    assert req.status == 500


async def test_resend_confirm_view(mock_cognito, cloud_client):
    """Test logging out."""
    req = await cloud_client.post(
        "/api/cloud/resend_confirm", json={"email": "hello@bla.com"}
    )
    assert req.status == 200
    assert len(mock_cognito.client.resend_confirmation_code.mock_calls) == 1


async def test_resend_confirm_view_bad_data(mock_cognito, cloud_client):
    """Test logging out."""
    req = await cloud_client.post(
        "/api/cloud/resend_confirm", json={"not_email": "hello@bla.com"}
    )
    assert req.status == 400
    assert len(mock_cognito.client.resend_confirmation_code.mock_calls) == 0


async def test_resend_confirm_view_request_timeout(mock_cognito, cloud_client):
    """Test timeout while logging out."""
    mock_cognito.client.resend_confirmation_code.side_effect = asyncio.TimeoutError
    req = await cloud_client.post(
        "/api/cloud/resend_confirm", json={"email": "hello@bla.com"}
    )
    assert req.status == 502


async def test_resend_confirm_view_unknown_error(mock_cognito, cloud_client):
    """Test unknown error while logging out."""
    mock_cognito.client.resend_confirmation_code.side_effect = UnknownError
    req = await cloud_client.post(
        "/api/cloud/resend_confirm", json={"email": "hello@bla.com"}
    )
    assert req.status == 502


async def test_websocket_status(
    opp. opp_ws_client, mock_cloud_fixture, mock_cloud_login
):
    """Test querying the status."""
    opp.data[DOMAIN].iot.state = STATE_CONNECTED
    client = await opp_ws_client.opp)

    with patch.dict(
        "openpeerpower.components.google_assistant.const.DOMAIN_TO_GOOGLE_TYPES",
        {"light": None},
        clear=True,
    ), patch.dict(
        "openpeerpower.components.alexa.entities.ENTITY_ADAPTERS",
        {"switch": None},
        clear=True,
    ):
        await client.send_json({"id": 5, "type": "cloud/status"})
        response = await client.receive_json()
    assert response["result"] == {
        "logged_in": True,
        "email": "hello@open-peer-power.io",
        "cloud": "connected",
        "prefs": {
            "alexa_enabled": True,
            "cloudhooks": {},
            "google_enabled": True,
            "google_entity_configs": {},
            "google_secure_devices_pin": None,
            "google_default_expose": None,
            "alexa_default_expose": None,
            "alexa_entity_configs": {},
            "alexa_report_state": False,
            "google_report_state": False,
            "remote_enabled": False,
            "tts_default_voice": ["en-US", "female"],
        },
        "alexa_entities": {
            "include_domains": [],
            "include_entity_globs": [],
            "include_entities": ["light.kitchen", "switch.ac"],
            "exclude_domains": [],
            "exclude_entity_globs": [],
            "exclude_entities": [],
        },
        "google_entities": {
            "include_domains": ["light"],
            "include_entity_globs": [],
            "include_entities": [],
            "exclude_domains": [],
            "exclude_entity_globs": [],
            "exclude_entities": [],
        },
        "remote_domain": None,
        "remote_connected": False,
        "remote_certificate": None,
    }


async def test_websocket_status_not_logged_in(opp, opp_ws_client):
    """Test querying the status."""
    client = await opp_ws_client.opp)
    await client.send_json({"id": 5, "type": "cloud/status"})
    response = await client.receive_json()
    assert response["result"] == {"logged_in": False, "cloud": "disconnected"}


async def test_websocket_subscription_reconnect(
    opp. opp_ws_client, aioclient_mock, mock_auth, mock_cloud_login
):
    """Test querying the status and connecting because valid account."""
    aioclient_mock.get(SUBSCRIPTION_INFO_URL, json={"provider": "stripe"})
    client = await opp_ws_client.opp)

    with patch(
         opp.nabucasa.auth.CognitoAuth.async_renew_access_token"
    ) as mock_renew, patch(.opp_nabucasa.iot.CloudIoT.connect") as mock_connect:
        await client.send_json({"id": 5, "type": "cloud/subscription"})
        response = await client.receive_json()

    assert response["result"] == {"provider": "stripe"}
    assert len(mock_renew.mock_calls) == 1
    assert len(mock_connect.mock_calls) == 1


async def test_websocket_subscription_no_reconnect_if_connected(
    opp. opp_ws_client, aioclient_mock, mock_auth, mock_cloud_login
):
    """Test querying the status and not reconnecting because still expired."""
    aioclient_mock.get(SUBSCRIPTION_INFO_URL, json={"provider": "stripe"})
    opp.data[DOMAIN].iot.state = STATE_CONNECTED
    client = await opp_ws_client.opp)

    with patch(
         opp.nabucasa.auth.CognitoAuth.async_renew_access_token"
    ) as mock_renew, patch(.opp_nabucasa.iot.CloudIoT.connect") as mock_connect:
        await client.send_json({"id": 5, "type": "cloud/subscription"})
        response = await client.receive_json()

    assert response["result"] == {"provider": "stripe"}
    assert len(mock_renew.mock_calls) == 0
    assert len(mock_connect.mock_calls) == 0


async def test_websocket_subscription_no_reconnect_if_expired(
    opp. opp_ws_client, aioclient_mock, mock_auth, mock_cloud_login
):
    """Test querying the status and not reconnecting because still expired."""
    aioclient_mock.get(SUBSCRIPTION_INFO_URL, json={"provider": "stripe"})
    client = await opp_ws_client.opp)

    with patch(
         opp.nabucasa.auth.CognitoAuth.async_renew_access_token"
    ) as mock_renew, patch(.opp_nabucasa.iot.CloudIoT.connect") as mock_connect:
        await client.send_json({"id": 5, "type": "cloud/subscription"})
        response = await client.receive_json()

    assert response["result"] == {"provider": "stripe"}
    assert len(mock_renew.mock_calls) == 1
    assert len(mock_connect.mock_calls) == 1


async def test_websocket_subscription_fail(
    opp. opp_ws_client, aioclient_mock, mock_auth, mock_cloud_login
):
    """Test querying the status."""
    aioclient_mock.get(SUBSCRIPTION_INFO_URL, status=HTTP_INTERNAL_SERVER_ERROR)
    client = await opp_ws_client.opp)
    await client.send_json({"id": 5, "type": "cloud/subscription"})
    response = await client.receive_json()

    assert not response["success"]
    assert response["error"]["code"] == "request_failed"


async def test_websocket_subscription_not_logged_in(opp, opp_ws_client):
    """Test querying the status."""
    client = await opp_ws_client.opp)
    with patch(
         opp.nabucasa.Cloud.fetch_subscription_info",
        return_value={"return": "value"},
    ):
        await client.send_json({"id": 5, "type": "cloud/subscription"})
        response = await client.receive_json()

    assert not response["success"]
    assert response["error"]["code"] == "not_logged_in"


async def test_websocket_update_preferences(
    opp. opp_ws_client, aioclient_mock, setup_api, mock_cloud_login
):
    """Test updating preference."""
    assert setup_api.google_enabled
    assert setup_api.alexa_enabled
    assert setup_api.google_secure_devices_pin is None
    client = await opp_ws_client.opp)
    await client.send_json(
        {
            "id": 5,
            "type": "cloud/update_prefs",
            "alexa_enabled": False,
            "google_enabled": False,
            "google_secure_devices_pin": "1234",
            "google_default_expose": ["light", "switch"],
            "alexa_default_expose": ["sensor", "media_player"],
            "tts_default_voice": ["en-GB", "male"],
        }
    )
    response = await client.receive_json()

    assert response["success"]
    assert not setup_api.google_enabled
    assert not setup_api.alexa_enabled
    assert setup_api.google_secure_devices_pin == "1234"
    assert setup_api.google_default_expose == ["light", "switch"]
    assert setup_api.alexa_default_expose == ["sensor", "media_player"]
    assert setup_api.tts_default_voice == ("en-GB", "male")


async def test_websocket_update_preferences_require_relink(
    opp. opp_ws_client, aioclient_mock, setup_api, mock_cloud_login
):
    """Test updating preference requires relink."""
    client = await opp_ws_client.opp)

    with patch(
        "openpeerpower.components.cloud.alexa_config.AlexaConfig"
        ".async_get_access_token",
        side_effect=RequireRelink,
    ):
        await client.send_json(
            {"id": 5, "type": "cloud/update_prefs", "alexa_report_state": True}
        )
        response = await client.receive_json()

    assert not response["success"]
    assert response["error"]["code"] == "alexa_relink"


async def test_websocket_update_preferences_no_token(
    opp. opp_ws_client, aioclient_mock, setup_api, mock_cloud_login
):
    """Test updating preference no token available."""
    client = await opp_ws_client.opp)

    with patch(
        "openpeerpower.components.cloud.alexa_config.AlexaConfig"
        ".async_get_access_token",
        side_effect=alexa_errors.NoTokenAvailable,
    ):
        await client.send_json(
            {"id": 5, "type": "cloud/update_prefs", "alexa_report_state": True}
        )
        response = await client.receive_json()

    assert not response["success"]
    assert response["error"]["code"] == "alexa_relink"


async def test_enabling_webhook(opp, opp_ws_client, setup_api, mock_cloud_login):
    """Test we call right code to enable webhooks."""
    client = await opp_ws_client.opp)
    with patch(
         opp.nabucasa.cloudhooks.Cloudhooks.async_create", return_value={}
    ) as mock_enable:
        await client.send_json(
            {"id": 5, "type": "cloud/cloudhook/create", "webhook_id": "mock-webhook-id"}
        )
        response = await client.receive_json()
    assert response["success"]

    assert len(mock_enable.mock_calls) == 1
    assert mock_enable.mock_calls[0][1][0] == "mock-webhook-id"


async def test_disabling_webhook(opp, opp_ws_client, setup_api, mock_cloud_login):
    """Test we call right code to disable webhooks."""
    client = await opp_ws_client.opp)
    with patch(.opp_nabucasa.cloudhooks.Cloudhooks.async_delete") as mock_disable:
        await client.send_json(
            {"id": 5, "type": "cloud/cloudhook/delete", "webhook_id": "mock-webhook-id"}
        )
        response = await client.receive_json()
    assert response["success"]

    assert len(mock_disable.mock_calls) == 1
    assert mock_disable.mock_calls[0][1][0] == "mock-webhook-id"


async def test_enabling_remote(opp, opp_ws_client, setup_api, mock_cloud_login):
    """Test we call right code to enable remote UI."""
    client = await opp_ws_client.opp)
    cloud = opp.data[DOMAIN]

    with patch(.opp_nabucasa.remote.RemoteUI.connect") as mock_connect:
        await client.send_json({"id": 5, "type": "cloud/remote/connect"})
        response = await client.receive_json()
    assert response["success"]
    assert cloud.client.remote_autostart

    assert len(mock_connect.mock_calls) == 1


async def test_disabling_remote(opp, opp_ws_client, setup_api, mock_cloud_login):
    """Test we call right code to disable remote UI."""
    client = await opp_ws_client.opp)
    cloud = opp.data[DOMAIN]

    with patch(.opp_nabucasa.remote.RemoteUI.disconnect") as mock_disconnect:
        await client.send_json({"id": 5, "type": "cloud/remote/disconnect"})
        response = await client.receive_json()
    assert response["success"]
    assert not cloud.client.remote_autostart

    assert len(mock_disconnect.mock_calls) == 1


async def test_enabling_remote_trusted_networks_local4(
    opp. opp_ws_client, setup_api, mock_cloud_login
):
    """Test we cannot enable remote UI when trusted networks active."""
    # pylint: disable=protected-access
    opp.auth._providers[
        ("trusted_networks", None)
    ] = tn_auth.TrustedNetworksAuthProvider(
        opp,
        None,
        tn_auth.CONFIG_SCHEMA(
            {"type": "trusted_networks", "trusted_networks": ["127.0.0.1"]}
        ),
    )

    client = await opp_ws_client.opp)

    with patch(
         opp.nabucasa.remote.RemoteUI.connect", side_effect=AssertionError
    ) as mock_connect:
        await client.send_json({"id": 5, "type": "cloud/remote/connect"})
        response = await client.receive_json()

    assert not response["success"]
    assert response["error"]["code"] == HTTP_INTERNAL_SERVER_ERROR
    assert (
        response["error"]["message"]
        == "Remote UI not compatible with 127.0.0.1/::1 as a trusted network."
    )

    assert len(mock_connect.mock_calls) == 0


async def test_enabling_remote_trusted_networks_local6(
    opp. opp_ws_client, setup_api, mock_cloud_login
):
    """Test we cannot enable remote UI when trusted networks active."""
    # pylint: disable=protected-access
    opp.auth._providers[
        ("trusted_networks", None)
    ] = tn_auth.TrustedNetworksAuthProvider(
        opp,
        None,
        tn_auth.CONFIG_SCHEMA(
            {"type": "trusted_networks", "trusted_networks": ["::1"]}
        ),
    )

    client = await opp_ws_client.opp)

    with patch(
         opp.nabucasa.remote.RemoteUI.connect", side_effect=AssertionError
    ) as mock_connect:
        await client.send_json({"id": 5, "type": "cloud/remote/connect"})
        response = await client.receive_json()

    assert not response["success"]
    assert response["error"]["code"] == HTTP_INTERNAL_SERVER_ERROR
    assert (
        response["error"]["message"]
        == "Remote UI not compatible with 127.0.0.1/::1 as a trusted network."
    )

    assert len(mock_connect.mock_calls) == 0


async def test_enabling_remote_trusted_networks_other(
    opp. opp_ws_client, setup_api, mock_cloud_login
):
    """Test we can enable remote UI when trusted networks active."""
    # pylint: disable=protected-access
    opp.auth._providers[
        ("trusted_networks", None)
    ] = tn_auth.TrustedNetworksAuthProvider(
        opp,
        None,
        tn_auth.CONFIG_SCHEMA(
            {"type": "trusted_networks", "trusted_networks": ["192.168.0.0/24"]}
        ),
    )

    client = await opp_ws_client.opp)
    cloud = opp.data[DOMAIN]

    with patch(.opp_nabucasa.remote.RemoteUI.connect") as mock_connect:
        await client.send_json({"id": 5, "type": "cloud/remote/connect"})
        response = await client.receive_json()

    assert response["success"]
    assert cloud.client.remote_autostart

    assert len(mock_connect.mock_calls) == 1


async def test_list_google_entities(opp, opp_ws_client, setup_api, mock_cloud_login):
    """Test that we can list Google entities."""
    client = await opp_ws_client.opp)
    entity = GoogleEntity(
        opp. MockConfig(should_expose=lambda *_: False), State("light.kitchen", "on")
    )
    entity2 = GoogleEntity(
        opp,
        MockConfig(should_expose=lambda *_: True, should_2fa=lambda *_: False),
        State("cover.garage", "open", {"device_class": "garage"}),
    )
    with patch(
        "openpeerpower.components.google_assistant.helpers.async_get_entities",
        return_value=[entity, entity2],
    ):
        await client.send_json({"id": 5, "type": "cloud/google_assistant/entities"})
        response = await client.receive_json()

    assert response["success"]
    assert len(response["result"]) == 2
    assert response["result"][0] == {
        "entity_id": "light.kitchen",
        "might_2fa": False,
        "traits": ["action.devices.traits.OnOff"],
    }
    assert response["result"][1] == {
        "entity_id": "cover.garage",
        "might_2fa": True,
        "traits": ["action.devices.traits.OpenClose"],
    }


async def test_update_google_entity(opp, opp_ws_client, setup_api, mock_cloud_login):
    """Test that we can update config of a Google entity."""
    client = await opp_ws_client.opp)
    await client.send_json(
        {
            "id": 5,
            "type": "cloud/google_assistant/entities/update",
            "entity_id": "light.kitchen",
            "should_expose": False,
            "override_name": "updated name",
            "aliases": ["lefty", "righty"],
            "disable_2fa": False,
        }
    )
    response = await client.receive_json()

    assert response["success"]
    prefs = opp.data[DOMAIN].client.prefs
    assert prefs.google_entity_configs["light.kitchen"] == {
        "should_expose": False,
        "override_name": "updated name",
        "aliases": ["lefty", "righty"],
        "disable_2fa": False,
    }

    await client.send_json(
        {
            "id": 6,
            "type": "cloud/google_assistant/entities/update",
            "entity_id": "light.kitchen",
            "should_expose": None,
        }
    )
    response = await client.receive_json()

    assert response["success"]
    prefs = opp.data[DOMAIN].client.prefs
    assert prefs.google_entity_configs["light.kitchen"] == {
        "should_expose": None,
        "override_name": "updated name",
        "aliases": ["lefty", "righty"],
        "disable_2fa": False,
    }


async def test_enabling_remote_trusted_proxies_local4(
    opp. opp_ws_client, setup_api, mock_cloud_login
):
    """Test we cannot enable remote UI when trusted networks active."""
    opp.http.trusted_proxies.append(ip_network("127.0.0.1"))

    client = await opp_ws_client.opp)

    with patch(
         opp.nabucasa.remote.RemoteUI.connect", side_effect=AssertionError
    ) as mock_connect:
        await client.send_json({"id": 5, "type": "cloud/remote/connect"})
        response = await client.receive_json()

    assert not response["success"]
    assert response["error"]["code"] == HTTP_INTERNAL_SERVER_ERROR
    assert (
        response["error"]["message"]
        == "Remote UI not compatible with 127.0.0.1/::1 as trusted proxies."
    )

    assert len(mock_connect.mock_calls) == 0


async def test_enabling_remote_trusted_proxies_local6(
    opp. opp_ws_client, setup_api, mock_cloud_login
):
    """Test we cannot enable remote UI when trusted networks active."""
    opp.http.trusted_proxies.append(ip_network("::1"))

    client = await opp_ws_client.opp)

    with patch(
         opp.nabucasa.remote.RemoteUI.connect", side_effect=AssertionError
    ) as mock_connect:
        await client.send_json({"id": 5, "type": "cloud/remote/connect"})
        response = await client.receive_json()

    assert not response["success"]
    assert response["error"]["code"] == HTTP_INTERNAL_SERVER_ERROR
    assert (
        response["error"]["message"]
        == "Remote UI not compatible with 127.0.0.1/::1 as trusted proxies."
    )

    assert len(mock_connect.mock_calls) == 0


async def test_list_alexa_entities(opp, opp_ws_client, setup_api, mock_cloud_login):
    """Test that we can list Alexa entities."""
    client = await opp_ws_client.opp)
    entity = LightCapabilities(
        opp. MagicMock(entity_config={}), State("light.kitchen", "on")
    )
    with patch(
        "openpeerpower.components.alexa.entities.async_get_entities",
        return_value=[entity],
    ):
        await client.send_json({"id": 5, "type": "cloud/alexa/entities"})
        response = await client.receive_json()

    assert response["success"]
    assert len(response["result"]) == 1
    assert response["result"][0] == {
        "entity_id": "light.kitchen",
        "display_categories": ["LIGHT"],
        "interfaces": ["Alexa.PowerController", "Alexa.EndpointHealth", "Alexa"],
    }


async def test_update_alexa_entity(opp, opp_ws_client, setup_api, mock_cloud_login):
    """Test that we can update config of an Alexa entity."""
    client = await opp_ws_client.opp)
    await client.send_json(
        {
            "id": 5,
            "type": "cloud/alexa/entities/update",
            "entity_id": "light.kitchen",
            "should_expose": False,
        }
    )
    response = await client.receive_json()

    assert response["success"]
    prefs = opp.data[DOMAIN].client.prefs
    assert prefs.alexa_entity_configs["light.kitchen"] == {"should_expose": False}

    await client.send_json(
        {
            "id": 6,
            "type": "cloud/alexa/entities/update",
            "entity_id": "light.kitchen",
            "should_expose": None,
        }
    )
    response = await client.receive_json()

    assert response["success"]
    prefs = opp.data[DOMAIN].client.prefs
    assert prefs.alexa_entity_configs["light.kitchen"] == {"should_expose": None}


async def test_sync_alexa_entities_timeout(
    opp. opp_ws_client, setup_api, mock_cloud_login
):
    """Test that timeout syncing Alexa entities."""
    client = await opp_ws_client.opp)
    with patch(
        "openpeerpower.components.cloud.alexa_config.AlexaConfig"
        ".async_sync_entities",
        side_effect=asyncio.TimeoutError,
    ):
        await client.send_json({"id": 5, "type": "cloud/alexa/sync"})
        response = await client.receive_json()

    assert not response["success"]
    assert response["error"]["code"] == "timeout"


async def test_sync_alexa_entities_no_token(
    opp. opp_ws_client, setup_api, mock_cloud_login
):
    """Test sync Alexa entities when we have no token."""
    client = await opp_ws_client.opp)
    with patch(
        "openpeerpower.components.cloud.alexa_config.AlexaConfig"
        ".async_sync_entities",
        side_effect=alexa_errors.NoTokenAvailable,
    ):
        await client.send_json({"id": 5, "type": "cloud/alexa/sync"})
        response = await client.receive_json()

    assert not response["success"]
    assert response["error"]["code"] == "alexa_relink"


async def test_enable_alexa_state_report_fail(
    opp. opp_ws_client, setup_api, mock_cloud_login
):
    """Test enable Alexa entities state reporting when no token available."""
    client = await opp_ws_client.opp)
    with patch(
        "openpeerpower.components.cloud.alexa_config.AlexaConfig"
        ".async_sync_entities",
        side_effect=alexa_errors.NoTokenAvailable,
    ):
        await client.send_json({"id": 5, "type": "cloud/alexa/sync"})
        response = await client.receive_json()

    assert not response["success"]
    assert response["error"]["code"] == "alexa_relink"


async def test_thingtalk_convert(opp, opp_ws_client, setup_api):
    """Test that we can convert a query."""
    client = await opp_ws_client.opp)

    with patch(
        "openpeerpower.components.cloud.http_api.thingtalk.async_convert",
        return_value={"hello": "world"},
    ):
        await client.send_json(
            {"id": 5, "type": "cloud/thingtalk/convert", "query": "some-data"}
        )
        response = await client.receive_json()

    assert response["success"]
    assert response["result"] == {"hello": "world"}


async def test_thingtalk_convert_timeout(opp, opp_ws_client, setup_api):
    """Test that we can convert a query."""
    client = await opp_ws_client.opp)

    with patch(
        "openpeerpower.components.cloud.http_api.thingtalk.async_convert",
        side_effect=asyncio.TimeoutError,
    ):
        await client.send_json(
            {"id": 5, "type": "cloud/thingtalk/convert", "query": "some-data"}
        )
        response = await client.receive_json()

    assert not response["success"]
    assert response["error"]["code"] == "timeout"


async def test_thingtalk_convert_internal(opp, opp_ws_client, setup_api):
    """Test that we can convert a query."""
    client = await opp_ws_client.opp)

    with patch(
        "openpeerpower.components.cloud.http_api.thingtalk.async_convert",
        side_effect=thingtalk.ThingTalkConversionError("Did not understand"),
    ):
        await client.send_json(
            {"id": 5, "type": "cloud/thingtalk/convert", "query": "some-data"}
        )
        response = await client.receive_json()

    assert not response["success"]
    assert response["error"]["code"] == "unknown_error"
    assert response["error"]["message"] == "Did not understand"


async def test_tts_info(opp, opp_ws_client, setup_api):
    """Test that we can get TTS info."""
    # Verify the format is as expected
    assert voice.MAP_VOICE[("en-US", voice.Gender.FEMALE)] == "JennyNeural"

    client = await opp_ws_client.opp)

    with patch.dict(
        "openpeerpower.components.cloud.http_api.MAP_VOICE",
        {
            ("en-US", voice.Gender.MALE): "GuyNeural",
            ("en-US", voice.Gender.FEMALE): "JennyNeural",
        },
        clear=True,
    ):
        await client.send_json({"id": 5, "type": "cloud/tts/info"})
        response = await client.receive_json()

    assert response["success"]
    assert response["result"] == {"languages": [["en-US", "male"], ["en-US", "female"]]}
