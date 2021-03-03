"""Test config entries API."""
import pytest

from openpeerpower.auth.providers import openpeerpower as prov_ha
from openpeerpower.components.config import auth_provider_openpeerpower as auth_ha

from tests.common import CLIENT_ID, MockUser


@pytest.fixture(autouse=True)
async def setup_config(opp, local_auth):
    """Fixture that sets up the auth provider ."""
    await auth_op.async_setup(opp)


@pytest.fixture
async def auth_provider(local_auth):
    """Opp auth provider."""
    return local_auth


@pytest.fixture
async def owner_access_token(opp, opp_owner_user):
    """Access token for owner user."""
    refresh_token = await opp.auth.async_create_refresh_token(
        opp.owner_user, CLIENT_ID
    )
    return opp.auth.async_create_access_token(refresh_token)


@pytest.fixture
async def opp_admin_credential(opp, auth_provider):
    """Overload credentials to admin user."""
    await opp.async_add_executor_job(
        auth_provider.data.add_auth, "test-user", "test-pass"
    )

    return await auth_provider.async_get_or_create_credentials(
        {"username": "test-user"}
    )


async def test_create_auth_system_generated_user(opp, opp_ws_client):
    """Test we can't add auth to system generated users."""
    system_user = MockUser(system_generated=True).add_to_opp(opp)
    client = await opp_ws_client(opp)

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth_provider/openpeerpower/create",
            "user_id": system_user.id,
            "username": "test-user",
            "password": "test-pass",
        }
    )

    result = await client.receive_json()

    assert not result["success"], result
    assert result["error"]["code"] == "system_generated"


async def test_create_auth_user_already_credentials():
    """Test we can't create auth for user with pre-existing credentials."""
    # assert False


async def test_create_auth_unknown_user(opp_ws_client, opp):
    """Test create pointing at unknown user."""
    client = await opp_ws_client(opp)

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth_provider/openpeerpower/create",
            "user_id": "test-id",
            "username": "test-user",
            "password": "test-pass",
        }
    )

    result = await client.receive_json()

    assert not result["success"], result
    assert result["error"]["code"] == "not_found"


async def test_create_auth_requires_admin(
    opp, opp_ws_client, opp_read_only_access_token
):
    """Test create requires admin to call API."""
    client = await opp_ws_client(opp, opp_read_only_access_token)

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth_provider/openpeerpower/create",
            "user_id": "test-id",
            "username": "test-user",
            "password": "test-pass",
        }
    )

    result = await client.receive_json()
    assert not result["success"], result
    assert result["error"]["code"] == "unauthorized"


async def test_create_auth(opp, opp_ws_client, opp_storage):
    """Test create auth command works."""
    client = await opp_ws_client(opp)
    user = MockUser().add_to_opp(opp)

    assert len(user.credentials) == 0

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth_provider/openpeerpower/create",
            "user_id": user.id,
            "username": "test-user2",
            "password": "test-pass",
        }
    )

    result = await client.receive_json()
    assert result["success"], result
    assert len(user.credentials) == 1
    creds = user.credentials[0]
    assert creds.auth_provider_type == "openpeerpower"
    assert creds.auth_provider_id is None
    assert creds.data == {"username": "test-user2"}
    assert prov_op.STORAGE_KEY in opp_storage
    entry = opp_storage[prov_op.STORAGE_KEY]["data"]["users"][1]
    assert entry["username"] == "test-user2"


async def test_create_auth_duplicate_username(opp, opp_ws_client, opp_storage):
    """Test we can't create auth with a duplicate username."""
    client = await opp_ws_client(opp)
    user = MockUser().add_to_opp(opp)

    opp.storage[prov_op.STORAGE_KEY] = {
        "version": 1,
        "data": {"users": [{"username": "test-user"}]},
    }

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth_provider/openpeerpower/create",
            "user_id": user.id,
            "username": "test-user",
            "password": "test-pass",
        }
    )

    result = await client.receive_json()
    assert not result["success"], result
    assert result["error"]["code"] == "username_exists"


async def test_delete_removes_just_auth(opp_ws_client, opp, opp_storage):
    """Test deleting an auth without being connected to a user."""
    client = await opp_ws_client(opp)

    opp.storage[prov_op.STORAGE_KEY] = {
        "version": 1,
        "data": {"users": [{"username": "test-user"}]},
    }

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth_provider/openpeerpower/delete",
            "username": "test-user",
        }
    )

    result = await client.receive_json()
    assert result["success"], result
    assert len.opp_storage[prov_op.STORAGE_KEY]["data"]["users"]) == 0


async def test_delete_removes_credential(opp, opp_ws_client, opp_storage):
    """Test deleting auth that is connected to a user."""
    client = await opp_ws_client(opp)

    user = MockUser().add_to_opp(opp)
    opp.storage[prov_op.STORAGE_KEY] = {
        "version": 1,
        "data": {"users": [{"username": "test-user"}]},
    }

    user.credentials.append(
        await opp.auth.auth_providers[0].async_get_or_create_credentials(
            {"username": "test-user"}
        )
    )

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth_provider/openpeerpower/delete",
            "username": "test-user",
        }
    )

    result = await client.receive_json()
    assert result["success"], result
    assert len.opp_storage[prov_op.STORAGE_KEY]["data"]["users"]) == 0


async def test_delete_requires_admin(opp, opp_ws_client, opp_read_only_access_token):
    """Test delete requires admin."""
    client = await opp_ws_client(opp, opp_read_only_access_token)

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth_provider/openpeerpower/delete",
            "username": "test-user",
        }
    )

    result = await client.receive_json()
    assert not result["success"], result
    assert result["error"]["code"] == "unauthorized"


async def test_delete_unknown_auth(opp, opp_ws_client):
    """Test trying to delete an unknown auth username."""
    client = await opp_ws_client(opp)

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth_provider/openpeerpower/delete",
            "username": "test-user2",
        }
    )

    result = await client.receive_json()
    assert not result["success"], result
    assert result["error"]["code"] == "auth_not_found"


async def test_change_password(opp, opp_ws_client, auth_provider):
    """Test that change password succeeds with valid password."""
    client = await opp_ws_client(opp)
    await client.send_json(
        {
            "id": 6,
            "type": "config/auth_provider/openpeerpower/change_password",
            "current_password": "test-pass",
            "new_password": "new-pass",
        }
    )

    result = await client.receive_json()
    assert result["success"], result
    await auth_provider.async_validate_login("test-user", "new-pass")


async def test_change_password_wrong_pw(
    opp, opp_ws_client, opp_admin_user, auth_provider
):
    """Test that change password fails with invalid password."""

    client = await opp_ws_client(opp)
    await client.send_json(
        {
            "id": 6,
            "type": "config/auth_provider/openpeerpower/change_password",
            "current_password": "wrong-pass",
            "new_password": "new-pass",
        }
    )

    result = await client.receive_json()
    assert not result["success"], result
    assert result["error"]["code"] == "invalid_current_password"
    with pytest.raises(prov_op.InvalidAuth):
        await auth_provider.async_validate_login("test-user", "new-pass")


async def test_change_password_no_creds(opp, opp_ws_client, opp_admin_user):
    """Test that change password fails with no credentials."""
    opp.admin_user.credentials.clear()
    client = await opp_ws_client(opp)

    await client.send_json(
        {
            "id": 6,
            "type": "config/auth_provider/openpeerpower/change_password",
            "current_password": "test-pass",
            "new_password": "new-pass",
        }
    )

    result = await client.receive_json()
    assert not result["success"], result
    assert result["error"]["code"] == "credentials_not_found"


async def test_admin_change_password_not_owner(opp, opp_ws_client, auth_provider):
    """Test that change password fails when not owner."""
    client = await opp_ws_client(opp)

    await client.send_json(
        {
            "id": 6,
            "type": "config/auth_provider/openpeerpower/admin_change_password",
            "user_id": "test-user",
            "password": "new-pass",
        }
    )

    result = await client.receive_json()
    assert not result["success"], result
    assert result["error"]["code"] == "unauthorized"

    # Validate old login still works
    await auth_provider.async_validate_login("test-user", "test-pass")


async def test_admin_change_password_no_user(opp, opp_ws_client, owner_access_token):
    """Test that change password fails with unknown user."""
    client = await opp_ws_client(opp, owner_access_token)

    await client.send_json(
        {
            "id": 6,
            "type": "config/auth_provider/openpeerpower/admin_change_password",
            "user_id": "non-existing",
            "password": "new-pass",
        }
    )

    result = await client.receive_json()
    assert not result["success"], result
    assert result["error"]["code"] == "user_not_found"


async def test_admin_change_password_no_cred(
    opp, opp_ws_client, owner_access_token, opp_admin_user
):
    """Test that change password fails with unknown credential."""

    opp.admin_user.credentials.clear()
    client = await opp_ws_client(opp, owner_access_token)

    await client.send_json(
        {
            "id": 6,
            "type": "config/auth_provider/openpeerpower/admin_change_password",
            "user_id":.opp_admin_user.id,
            "password": "new-pass",
        }
    )

    result = await client.receive_json()
    assert not result["success"], result
    assert result["error"]["code"] == "credentials_not_found"


async def test_admin_change_password(
    opp,
    opp_ws_client,
    owner_access_token,
    auth_provider,
    opp_admin_user,
):
    """Test that owners can change any password."""
    client = await opp_ws_client(opp, owner_access_token)

    await client.send_json(
        {
            "id": 6,
            "type": "config/auth_provider/openpeerpower/admin_change_password",
            "user_id":.opp_admin_user.id,
            "password": "new-pass",
        }
    )

    result = await client.receive_json()
    assert result["success"], result

    await auth_provider.async_validate_login("test-user", "new-pass")
