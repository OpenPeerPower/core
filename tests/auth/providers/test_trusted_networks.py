"""Test the Trusted Networks auth provider."""
from ipaddress import ip_address, ip_network
from unittest.mock import Mock, patch

import pytest
import voluptuous as vol

from openpeerpower import auth
from openpeerpower.auth import auth_store
from openpeerpower.auth.providers import trusted_networks as tn_auth


@pytest.fixture
def store(opp):
    """Mock store."""
    return auth_store.AuthStore(opp)


@pytest.fixture
def provider(opp, store):
    """Mock provider."""
    return tn_auth.TrustedNetworksAuthProvider(
        opp,
        store,
        tn_auth.CONFIG_SCHEMA(
            {
                "type": "trusted_networks",
                "trusted_networks": [
                    "192.168.0.1",
                    "192.168.128.0/24",
                    "::1",
                    "fd00::/8",
                ],
            }
        ),
    )


@pytest.fixture
def provider_with_user(opp, store):
    """Mock provider with trusted users config."""
    return tn_auth.TrustedNetworksAuthProvider(
        opp,
        store,
        tn_auth.CONFIG_SCHEMA(
            {
                "type": "trusted_networks",
                "trusted_networks": [
                    "192.168.0.1",
                    "192.168.128.0/24",
                    "::1",
                    "fd00::/8",
                ],
                # user_id will be injected in test
                "trusted_users": {
                    "192.168.0.1": [],
                    "192.168.128.0/24": [],
                    "fd00::/8": [],
                },
            }
        ),
    )


@pytest.fixture
def provider_bypass_login(opp, store):
    """Mock provider with allow_bypass_login config."""
    return tn_auth.TrustedNetworksAuthProvider(
        opp,
        store,
        tn_auth.CONFIG_SCHEMA(
            {
                "type": "trusted_networks",
                "trusted_networks": [
                    "192.168.0.1",
                    "192.168.128.0/24",
                    "::1",
                    "fd00::/8",
                ],
                "allow_bypass_login": True,
            }
        ),
    )


@pytest.fixture
def manager(opp, store, provider):
    """Mock manager."""
    return auth.AuthManager(opp, store, {(provider.type, provider.id): provider}, {})


@pytest.fixture
def manager_with_user(opp, store, provider_with_user):
    """Mock manager with trusted user."""
    return auth.AuthManager(
        opp,
        store,
        {(provider_with_user.type, provider_with_user.id): provider_with_user},
        {},
    )


@pytest.fixture
def manager_bypass_login(opp, store, provider_bypass_login):
    """Mock manager with allow bypass login."""
    return auth.AuthManager(
        opp,
        store,
        {(provider_bypass_login.type, provider_bypass_login.id): provider_bypass_login},
        {},
    )


async def test_trusted_networks_credentials(manager, provider):
    """Test trusted_networks credentials related functions."""
    owner = await manager.async_create_user("test-owner")
    tn_owner_cred = await provider.async_get_or_create_credentials({"user": owner.id})
    assert tn_owner_cred.is_new is False
    assert any(cred.id == tn_owner_cred.id for cred in owner.credentials)

    user = await manager.async_create_user("test-user")
    tn_user_cred = await provider.async_get_or_create_credentials({"user": user.id})
    assert tn_user_cred.id != tn_owner_cred.id
    assert tn_user_cred.is_new is False
    assert any(cred.id == tn_user_cred.id for cred in user.credentials)

    with pytest.raises(tn_auth.InvalidUserError):
        await provider.async_get_or_create_credentials({"user": "invalid-user"})


async def test_validate_access(provider):
    """Test validate access from trusted networks."""
    provider.async_validate_access(ip_address("192.168.0.1"))
    provider.async_validate_access(ip_address("192.168.128.10"))
    provider.async_validate_access(ip_address("::1"))
    provider.async_validate_access(ip_address("fd01:db8::ff00:42:8329"))

    with pytest.raises(tn_auth.InvalidAuthError):
        provider.async_validate_access(ip_address("192.168.0.2"))
    with pytest.raises(tn_auth.InvalidAuthError):
        provider.async_validate_access(ip_address("127.0.0.1"))
    with pytest.raises(tn_auth.InvalidAuthError):
        provider.async_validate_access(ip_address("2001:db8::ff00:42:8329"))


async def test_validate_refresh_token(provider):
    """Verify re-validation of refresh token."""
    with patch.object(provider, "async_validate_access") as mock:
        with pytest.raises(tn_auth.InvalidAuthError):
            provider.async_validate_refresh_token(Mock(), None)

        provider.async_validate_refresh_token(Mock(), "127.0.0.1")
        mock.assert_called_once_with(ip_address("127.0.0.1"))


async def test_login_flow(manager, provider):
    """Test login flow."""
    owner = await manager.async_create_user("test-owner")
    user = await manager.async_create_user("test-user")

    # not from trusted network
    flow = await provider.async_login_flow({"ip_address": ip_address("127.0.0.1")})
    step = await flow.async_step_init()
    assert step["type"] == "abort"
    assert step["reason"] == "not_allowed"

    # from trusted network, list users
    flow = await provider.async_login_flow({"ip_address": ip_address("192.168.0.1")})
    step = await flow.async_step_init()
    assert step["step_id"] == "init"

    schema = step["data_schema"]
    assert schema({"user": owner.id})
    with pytest.raises(vol.Invalid):
        assert schema({"user": "invalid-user"})

    # login with valid user
    step = await flow.async_step_init({"user": user.id})
    assert step["type"] == "create_entry"
    assert step["data"]["user"] == user.id


async def test_trusted_users_login(manager_with_user, provider_with_user):
    """Test available user list changed per different IP."""
    owner = await manager_with_user.async_create_user("test-owner")
    sys_user = await manager_with_user.async_create_system_user(
        "test-sys-user"
    )  # system user will not be available to select
    user = await manager_with_user.async_create_user("test-user")

    # change the trusted users config
    config = provider_with_user.config["trusted_users"]
    assert ip_network("192.168.0.1") in config
    config[ip_network("192.168.0.1")] = [owner.id]
    assert ip_network("192.168.128.0/24") in config
    config[ip_network("192.168.128.0/24")] = [sys_user.id, user.id]

    # not from trusted network
    flow = await provider_with_user.async_login_flow(
        {"ip_address": ip_address("127.0.0.1")}
    )
    step = await flow.async_step_init()
    assert step["type"] == "abort"
    assert step["reason"] == "not_allowed"

    # from trusted network, list users intersect trusted_users
    flow = await provider_with_user.async_login_flow(
        {"ip_address": ip_address("192.168.0.1")}
    )
    step = await flow.async_step_init()
    assert step["step_id"] == "init"

    schema = step["data_schema"]
    # only owner listed
    assert schema({"user": owner.id})
    with pytest.raises(vol.Invalid):
        assert schema({"user": user.id})

    # from trusted network, list users intersect trusted_users
    flow = await provider_with_user.async_login_flow(
        {"ip_address": ip_address("192.168.128.1")}
    )
    step = await flow.async_step_init()
    assert step["step_id"] == "init"

    schema = step["data_schema"]
    # only user listed
    assert schema({"user": user.id})
    with pytest.raises(vol.Invalid):
        assert schema({"user": owner.id})
    with pytest.raises(vol.Invalid):
        assert schema({"user": sys_user.id})

    # from trusted network, list users intersect trusted_users
    flow = await provider_with_user.async_login_flow({"ip_address": ip_address("::1")})
    step = await flow.async_step_init()
    assert step["step_id"] == "init"

    schema = step["data_schema"]
    # both owner and user listed
    assert schema({"user": owner.id})
    assert schema({"user": user.id})
    with pytest.raises(vol.Invalid):
        assert schema({"user": sys_user.id})

    # from trusted network, list users intersect trusted_users
    flow = await provider_with_user.async_login_flow(
        {"ip_address": ip_address("fd00::1")}
    )
    step = await flow.async_step_init()
    assert step["step_id"] == "init"

    schema = step["data_schema"]
    # no user listed
    with pytest.raises(vol.Invalid):
        assert schema({"user": owner.id})
    with pytest.raises(vol.Invalid):
        assert schema({"user": user.id})
    with pytest.raises(vol.Invalid):
        assert schema({"user": sys_user.id})


async def test_trusted_group_login(manager_with_user, provider_with_user):
    """Test config trusted_user with group_id."""
    owner = await manager_with_user.async_create_user("test-owner")
    # create a user in user group
    user = await manager_with_user.async_create_user("test-user")
    await manager_with_user.async_update_user(
        user, group_ids=[auth.const.GROUP_ID_USER]
    )

    # change the trusted users config
    config = provider_with_user.config["trusted_users"]
    assert ip_network("192.168.0.1") in config
    config[ip_network("192.168.0.1")] = [{"group": [auth.const.GROUP_ID_USER]}]
    assert ip_network("192.168.128.0/24") in config
    config[ip_network("192.168.128.0/24")] = [
        owner.id,
        {"group": [auth.const.GROUP_ID_USER]},
    ]

    # not from trusted network
    flow = await provider_with_user.async_login_flow(
        {"ip_address": ip_address("127.0.0.1")}
    )
    step = await flow.async_step_init()
    assert step["type"] == "abort"
    assert step["reason"] == "not_allowed"

    # from trusted network, list users intersect trusted_users
    flow = await provider_with_user.async_login_flow(
        {"ip_address": ip_address("192.168.0.1")}
    )
    step = await flow.async_step_init()
    assert step["step_id"] == "init"

    schema = step["data_schema"]
    # only user listed
    assert schema({"user": user.id})
    with pytest.raises(vol.Invalid):
        assert schema({"user": owner.id})

    # from trusted network, list users intersect trusted_users
    flow = await provider_with_user.async_login_flow(
        {"ip_address": ip_address("192.168.128.1")}
    )
    step = await flow.async_step_init()
    assert step["step_id"] == "init"

    schema = step["data_schema"]
    # both owner and user listed
    assert schema({"user": owner.id})
    assert schema({"user": user.id})


async def test_bypass_login_flow(manager_bypass_login, provider_bypass_login):
    """Test login flow can be bypass if only one user available."""
    owner = await manager_bypass_login.async_create_user("test-owner")

    # not from trusted network
    flow = await provider_bypass_login.async_login_flow(
        {"ip_address": ip_address("127.0.0.1")}
    )
    step = await flow.async_step_init()
    assert step["type"] == "abort"
    assert step["reason"] == "not_allowed"

    # from trusted network, only one available user, bypass the login flow
    flow = await provider_bypass_login.async_login_flow(
        {"ip_address": ip_address("192.168.0.1")}
    )
    step = await flow.async_step_init()
    assert step["type"] == "create_entry"
    assert step["data"]["user"] == owner.id

    user = await manager_bypass_login.async_create_user("test-user")

    # from trusted network, two available user, show up login form
    flow = await provider_bypass_login.async_login_flow(
        {"ip_address": ip_address("192.168.0.1")}
    )
    step = await flow.async_step_init()
    schema = step["data_schema"]
    # both owner and user listed
    assert schema({"user": owner.id})
    assert schema({"user": user.id})
