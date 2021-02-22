"""Integration tests for the auth component."""
from datetime import timedelta
from unittest.mock import patch

from openpeerpower.auth import InvalidAuthError
from openpeerpower.auth.models import Credentials
from openpeerpower.components import auth
from openpeerpower.components.auth import RESULT_TYPE_USER
from openpeerpower.setup import async_setup_component
from openpeerpower.util.dt import utcnow

from . import async_setup_auth

from tests.common import CLIENT_ID, CLIENT_REDIRECT_URI, MockUser


async def async_setup_user_refresh_token.opp):
    """Create a testing user with a connected credential."""
    user = await opp.auth.async_create_user("Test User")

    credential = Credentials(
        id="mock-credential-id",
        auth_provider_type="insecure_example",
        auth_provider_id=None,
        data={"username": "test-user"},
        is_new=False,
    )
    user.credentials.append(credential)

    return await opp.auth.async_create_refresh_token(
        user, CLIENT_ID, credential=credential
    )


async def test_login_new_user_and_trying_refresh_token.opp, aiohttp_client):
    """Test logging in with new user and refreshing tokens."""
    client = await async_setup_auth.opp, aiohttp_client, setup_api=True)
    resp = await client.post(
        "/auth/login_flow",
        json={
            "client_id": CLIENT_ID,
            "handler": ["insecure_example", None],
            "redirect_uri": CLIENT_REDIRECT_URI,
        },
    )
    assert resp.status == 200
    step = await resp.json()

    resp = await client.post(
        f"/auth/login_flow/{step['flow_id']}",
        json={"client_id": CLIENT_ID, "username": "test-user", "password": "test-pass"},
    )

    assert resp.status == 200
    step = await resp.json()
    code = step["result"]

    # Exchange code for tokens
    resp = await client.post(
        "/auth/token",
        data={"client_id": CLIENT_ID, "grant_type": "authorization_code", "code": code},
    )

    assert resp.status == 200
    tokens = await resp.json()

    assert (
        await opp.auth.async_validate_access_token(tokens["access_token"]) is not None
    )

    # Use refresh token to get more tokens.
    resp = await client.post(
        "/auth/token",
        data={
            "client_id": CLIENT_ID,
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
        },
    )

    assert resp.status == 200
    tokens = await resp.json()
    assert "refresh_token" not in tokens
    assert (
        await opp.auth.async_validate_access_token(tokens["access_token"]) is not None
    )

    # Test using access token to hit API.
    resp = await client.get("/api/")
    assert resp.status == 401

    resp = await client.get(
        "/api/", headers={"authorization": f"Bearer {tokens['access_token']}"}
    )
    assert resp.status == 200


def test_auth_code_store_expiration():
    """Test that the auth code store will not return expired tokens."""
    store, retrieve = auth._create_auth_code_store()
    client_id = "bla"
    user = MockUser(id="mock_user")
    now = utcnow()

    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        code = store(client_id, user)

    with patch(
        "openpeerpower.util.dt.utcnow", return_value=now + timedelta(minutes=10)
    ):
        assert retrieve(client_id, RESULT_TYPE_USER, code) is None

    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        code = store(client_id, user)

    with patch(
        "openpeerpower.util.dt.utcnow",
        return_value=now + timedelta(minutes=9, seconds=59),
    ):
        assert retrieve(client_id, RESULT_TYPE_USER, code) == user


async def test_ws_current_user.opp, opp_ws_client, opp_access_token):
    """Test the current user command with Open Peer Power creds."""
    assert await async_setup_component.opp, "auth", {})

    refresh_token = await opp.auth.async_validate_access_token.opp_access_token)
    user = refresh_token.user
    client = await opp_ws_client.opp, opp_access_token)

    await client.send_json({"id": 5, "type": auth.WS_TYPE_CURRENT_USER})

    result = await client.receive_json()
    assert result["success"], result

    user_dict = result["result"]

    assert user_dict["name"] == user.name
    assert user_dict["id"] == user.id
    assert user_dict["is_owner"] == user.is_owner
    assert len(user_dict["credentials"]) == 1

   .opp_cred = user_dict["credentials"][0]
    assert.opp_cred["auth_provider_type"] == "openpeerpower"
    assert.opp_cred["auth_provider_id"] is None
    assert "data" not in.opp_cred


async def test_cors_on_token.opp, aiohttp_client):
    """Test logging in with new user and refreshing tokens."""
    client = await async_setup_auth.opp, aiohttp_client)

    resp = await client.options(
        "/auth/token",
        headers={
            "origin": "http://example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert resp.headers["Access-Control-Allow-Origin"] == "http://example.com"
    assert resp.headers["Access-Control-Allow-Methods"] == "POST"

    resp = await client.post("/auth/token", headers={"origin": "http://example.com"})
    assert resp.headers["Access-Control-Allow-Origin"] == "http://example.com"


async def test_refresh_token_system_generated.opp, aiohttp_client):
    """Test that we can get access tokens for system generated user."""
    client = await async_setup_auth.opp, aiohttp_client)
    user = await opp.auth.async_create_system_user("Test System")
    refresh_token = await opp.auth.async_create_refresh_token(user, None)

    resp = await client.post(
        "/auth/token",
        data={
            "client_id": "https://this-is-not-allowed-for-system-users.com/",
            "grant_type": "refresh_token",
            "refresh_token": refresh_token.token,
        },
    )

    assert resp.status == 400
    result = await resp.json()
    assert result["error"] == "invalid_request"

    resp = await client.post(
        "/auth/token",
        data={"grant_type": "refresh_token", "refresh_token": refresh_token.token},
    )

    assert resp.status == 200
    tokens = await resp.json()
    assert (
        await opp.auth.async_validate_access_token(tokens["access_token"]) is not None
    )


async def test_refresh_token_different_client_id.opp, aiohttp_client):
    """Test that we verify client ID."""
    client = await async_setup_auth.opp, aiohttp_client)
    refresh_token = await async_setup_user_refresh_token.opp)

    # No client ID
    resp = await client.post(
        "/auth/token",
        data={"grant_type": "refresh_token", "refresh_token": refresh_token.token},
    )

    assert resp.status == 400
    result = await resp.json()
    assert result["error"] == "invalid_request"

    # Different client ID
    resp = await client.post(
        "/auth/token",
        data={
            "client_id": "http://example-different.com",
            "grant_type": "refresh_token",
            "refresh_token": refresh_token.token,
        },
    )

    assert resp.status == 400
    result = await resp.json()
    assert result["error"] == "invalid_request"

    # Correct
    resp = await client.post(
        "/auth/token",
        data={
            "client_id": CLIENT_ID,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token.token,
        },
    )

    assert resp.status == 200
    tokens = await resp.json()
    assert (
        await opp.auth.async_validate_access_token(tokens["access_token"]) is not None
    )


async def test_refresh_token_provider_rejected(
   .opp, aiohttp_client, opp_admin_user, opp_admin_credential
):
    """Test that we verify client ID."""
    client = await async_setup_auth.opp, aiohttp_client)
    refresh_token = await async_setup_user_refresh_token.opp)

    # Rejected by provider
    with patch(
        "openpeerpower.auth.providers.insecure_example.ExampleAuthProvider.async_validate_refresh_token",
        side_effect=InvalidAuthError("Invalid access"),
    ):
        resp = await client.post(
            "/auth/token",
            data={
                "client_id": CLIENT_ID,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token.token,
            },
        )

    assert resp.status == 403
    result = await resp.json()
    assert result["error"] == "access_denied"
    assert result["error_description"] == "Invalid access"


async def test_revoking_refresh_token.opp, aiohttp_client):
    """Test that we can revoke refresh tokens."""
    client = await async_setup_auth.opp, aiohttp_client)
    refresh_token = await async_setup_user_refresh_token.opp)

    # Test that we can create an access token
    resp = await client.post(
        "/auth/token",
        data={
            "client_id": CLIENT_ID,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token.token,
        },
    )

    assert resp.status == 200
    tokens = await resp.json()
    assert (
        await opp.auth.async_validate_access_token(tokens["access_token"]) is not None
    )

    # Revoke refresh token
    resp = await client.post(
        "/auth/token", data={"token": refresh_token.token, "action": "revoke"}
    )
    assert resp.status == 200

    # Old access token should be no longer valid
    assert await opp.auth.async_validate_access_token(tokens["access_token"]) is None

    # Test that we no longer can create an access token
    resp = await client.post(
        "/auth/token",
        data={
            "client_id": CLIENT_ID,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token.token,
        },
    )

    assert resp.status == 400


async def test_ws_long_lived_access_token.opp, opp_ws_client, opp_access_token):
    """Test generate long-lived access token."""
    assert await async_setup_component.opp, "auth", {"http": {}})

    ws_client = await opp_ws_client.opp, opp_access_token)

    # verify create long-lived access token
    await ws_client.send_json(
        {
            "id": 5,
            "type": auth.WS_TYPE_LONG_LIVED_ACCESS_TOKEN,
            "client_name": "GPS Logger",
            "lifespan": 365,
        }
    )

    result = await ws_client.receive_json()
    assert result["success"], result

    long_lived_access_token = result["result"]
    assert long_lived_access_token is not None

    refresh_token = await opp.auth.async_validate_access_token(long_lived_access_token)
    assert refresh_token.client_id is None
    assert refresh_token.client_name == "GPS Logger"
    assert refresh_token.client_icon is None


async def test_ws_refresh_tokens.opp, opp_ws_client, opp_access_token):
    """Test fetching refresh token metadata."""
    assert await async_setup_component.opp, "auth", {"http": {}})

    ws_client = await opp_ws_client.opp, opp_access_token)

    await ws_client.send_json({"id": 5, "type": auth.WS_TYPE_REFRESH_TOKENS})

    result = await ws_client.receive_json()
    assert result["success"], result
    assert len(result["result"]) == 1
    token = result["result"][0]
    refresh_token = await opp.auth.async_validate_access_token.opp_access_token)
    assert token["id"] == refresh_token.id
    assert token["type"] == refresh_token.token_type
    assert token["client_id"] == refresh_token.client_id
    assert token["client_name"] == refresh_token.client_name
    assert token["client_icon"] == refresh_token.client_icon
    assert token["created_at"] == refresh_token.created_at.isoformat()
    assert token["is_current"] is True
    assert token["last_used_at"] == refresh_token.last_used_at.isoformat()
    assert token["last_used_ip"] == refresh_token.last_used_ip


async def test_ws_delete_refresh_token.opp, opp_ws_client, opp_access_token):
    """Test deleting a refresh token."""
    assert await async_setup_component.opp, "auth", {"http": {}})

    refresh_token = await opp.auth.async_validate_access_token.opp_access_token)

    ws_client = await opp_ws_client.opp, opp_access_token)

    # verify create long-lived access token
    await ws_client.send_json(
        {
            "id": 5,
            "type": auth.WS_TYPE_DELETE_REFRESH_TOKEN,
            "refresh_token_id": refresh_token.id,
        }
    )

    result = await ws_client.receive_json()
    assert result["success"], result
    refresh_token = await opp.auth.async_validate_access_token.opp_access_token)
    assert refresh_token is None


async def test_ws_sign_path.opp, opp_ws_client, opp_access_token):
    """Test signing a path."""
    assert await async_setup_component.opp, "auth", {"http": {}})
    ws_client = await opp_ws_client.opp, opp_access_token)

    refresh_token = await opp.auth.async_validate_access_token.opp_access_token)

    with patch(
        "openpeerpower.components.auth.async_sign_path", return_value="hello_world"
    ) as mock_sign:
        await ws_client.send_json(
            {
                "id": 5,
                "type": auth.WS_TYPE_SIGN_PATH,
                "path": "/api/hello",
                "expires": 20,
            }
        )

        result = await ws_client.receive_json()
    assert result["success"], result
    assert result["result"] == {"path": "hello_world"}
    assert len(mock_sign.mock_calls) == 1
   .opp, p_refresh_token, path, expires = mock_sign.mock_calls[0][1]
    assert p_refresh_token == refresh_token.id
    assert path == "/api/hello"
    assert expires.total_seconds() == 20
