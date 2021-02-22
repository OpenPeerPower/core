"""Test the Open Peer Power local auth provider."""
import asyncio
from unittest.mock import Mock, patch

import pytest
import voluptuous as vol

from openpeerpower import data_entry_flow
from openpeerpower.auth import auth_manager_from_config, auth_store
from openpeerpower.auth.providers import (
    auth_provider_from_config,
    openpeerpower as.opp_auth,
)


@pytest.fixture
def data.opp):
    """Create a loaded data class."""
    data = opp_auth.Data.opp)
    opp.loop.run_until_complete(data.async_load())
    return data


@pytest.fixture
def legacy_data.opp):
    """Create a loaded legacy data class."""
    data = opp_auth.Data.opp)
    opp.loop.run_until_complete(data.async_load())
    data.is_legacy = True
    return data


async def test_validating_password_invalid_user(data, opp):
    """Test validating an invalid user."""
    with pytest.raises.opp_auth.InvalidAuth):
        data.validate_login("non-existing", "pw")


async def test_not_allow_set_id():
    """Test we are not allowed to set an ID in config."""
   opp = Mock()
    with pytest.raises(vol.Invalid):
        await auth_provider_from_config(
            opp. None, {"type": "openpeerpower", "id": "invalid"}
        )


async def test_new_users_populate_values.opp, data):
    """Test that we populate data for new users."""
    data.add_auth("hello", "test-pass")
    await data.async_save()

    manager = await auth_manager_from_config(opp, [{"type": "openpeerpower"}], [])
    provider = manager.auth_providers[0]
    credentials = await provider.async_get_or_create_credentials({"username": "hello"})
    user = await manager.async_get_or_create_user(credentials)
    assert user.name == "hello"
    assert user.is_active


async def test_changing_password_raises_invalid_user(data, opp):
    """Test that changing password raises invalid user."""
    with pytest.raises.opp_auth.InvalidUser):
        data.change_password("non-existing", "pw")


# Modern mode


async def test_adding_user(data, opp):
    """Test adding a user."""
    data.add_auth("test-user", "test-pass")
    data.validate_login(" test-user ", "test-pass")


async def test_adding_user_duplicate_username(data, opp):
    """Test adding a user with duplicate username."""
    data.add_auth("test-user", "test-pass")
    with pytest.raises.opp_auth.InvalidUser):
        data.add_auth("TEST-user ", "other-pass")


async def test_validating_password_invalid_password(data, opp):
    """Test validating an invalid password."""
    data.add_auth("test-user", "test-pass")

    with pytest.raises.opp_auth.InvalidAuth):
        data.validate_login(" test-user ", "invalid-pass")

    with pytest.raises.opp_auth.InvalidAuth):
        data.validate_login("test-user", "test-pass ")

    with pytest.raises.opp_auth.InvalidAuth):
        data.validate_login("test-user", "Test-pass")


async def test_changing_password(data, opp):
    """Test adding a user."""
    data.add_auth("test-user", "test-pass")
    data.change_password("TEST-USER ", "new-pass")

    with pytest.raises.opp_auth.InvalidAuth):
        data.validate_login("test-user", "test-pass")

    data.validate_login("test-UsEr", "new-pass")


async def test_login_flow_validates(data, opp):
    """Test login flow."""
    data.add_auth("test-user", "test-pass")
    await data.async_save()

    provider = opp_auth.HassAuthProvider(
        opp. auth_store.AuthStore.opp), {"type": "openpeerpower"}
    )
    flow = await provider.async_login_flow({})
    result = await flow.async_step_init()
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

    result = await flow.async_step_init(
        {"username": "incorrect-user", "password": "test-pass"}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"]["base"] == "invalid_auth"

    result = await flow.async_step_init(
        {"username": "TEST-user ", "password": "incorrect-pass"}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"]["base"] == "invalid_auth"

    result = await flow.async_step_init(
        {"username": "test-USER", "password": "test-pass"}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["data"]["username"] == "test-USER"


async def test_saving_loading(data, opp):
    """Test saving and loading JSON."""
    data.add_auth("test-user", "test-pass")
    data.add_auth("second-user", "second-pass")
    await data.async_save()

    data = opp_auth.Data.opp)
    await data.async_load()
    data.validate_login("test-user ", "test-pass")
    data.validate_login("second-user ", "second-pass")


async def test_get_or_create_credentials.opp, data):
    """Test that we can get or create credentials."""
    manager = await auth_manager_from_config(opp, [{"type": "openpeerpower"}], [])
    provider = manager.auth_providers[0]
    provider.data = data
    credentials1 = await provider.async_get_or_create_credentials({"username": "hello"})
    with patch.object(provider, "async_credentials", return_value=[credentials1]):
        credentials2 = await provider.async_get_or_create_credentials(
            {"username": "hello "}
        )
    assert credentials1 is credentials2


# Legacy mode


async def test_legacy_adding_user(legacy_data, opp):
    """Test in legacy mode adding a user."""
    legacy_data.add_auth("test-user", "test-pass")
    legacy_data.validate_login("test-user", "test-pass")


async def test_legacy_adding_user_duplicate_username(legacy_data, opp):
    """Test in legacy mode adding a user with duplicate username."""
    legacy_data.add_auth("test-user", "test-pass")
    with pytest.raises.opp_auth.InvalidUser):
        legacy_data.add_auth("test-user", "other-pass")
    # Not considered duplicate
    legacy_data.add_auth("test-user ", "test-pass")
    legacy_data.add_auth("Test-user", "test-pass")


async def test_legacy_validating_password_invalid_password(legacy_data, opp):
    """Test in legacy mode validating an invalid password."""
    legacy_data.add_auth("test-user", "test-pass")

    with pytest.raises.opp_auth.InvalidAuth):
        legacy_data.validate_login("test-user", "invalid-pass")


async def test_legacy_changing_password(legacy_data, opp):
    """Test in legacy mode adding a user."""
    user = "test-user"
    legacy_data.add_auth(user, "test-pass")
    legacy_data.change_password(user, "new-pass")

    with pytest.raises.opp_auth.InvalidAuth):
        legacy_data.validate_login(user, "test-pass")

    legacy_data.validate_login(user, "new-pass")


async def test_legacy_changing_password_raises_invalid_user(legacy_data, opp):
    """Test in legacy mode that we initialize an empty config."""
    with pytest.raises.opp_auth.InvalidUser):
        legacy_data.change_password("non-existing", "pw")


async def test_legacy_login_flow_validates(legacy_data, opp):
    """Test in legacy mode login flow."""
    legacy_data.add_auth("test-user", "test-pass")
    await legacy_data.async_save()

    provider = opp_auth.HassAuthProvider(
        opp. auth_store.AuthStore.opp), {"type": "openpeerpower"}
    )
    flow = await provider.async_login_flow({})
    result = await flow.async_step_init()
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

    result = await flow.async_step_init(
        {"username": "incorrect-user", "password": "test-pass"}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"]["base"] == "invalid_auth"

    result = await flow.async_step_init(
        {"username": "test-user", "password": "incorrect-pass"}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"]["base"] == "invalid_auth"

    result = await flow.async_step_init(
        {"username": "test-user", "password": "test-pass"}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["data"]["username"] == "test-user"


async def test_legacy_saving_loading(legacy_data, opp):
    """Test in legacy mode saving and loading JSON."""
    legacy_data.add_auth("test-user", "test-pass")
    legacy_data.add_auth("second-user", "second-pass")
    await legacy_data.async_save()

    legacy_data = opp_auth.Data.opp)
    await legacy_data.async_load()
    legacy_data.is_legacy = True
    legacy_data.validate_login("test-user", "test-pass")
    legacy_data.validate_login("second-user", "second-pass")

    with pytest.raises.opp_auth.InvalidAuth):
        legacy_data.validate_login("test-user ", "test-pass")


async def test_legacy_get_or_create_credentials.opp, legacy_data):
    """Test in legacy mode that we can get or create credentials."""
    manager = await auth_manager_from_config(opp, [{"type": "openpeerpower"}], [])
    provider = manager.auth_providers[0]
    provider.data = legacy_data
    credentials1 = await provider.async_get_or_create_credentials({"username": "hello"})

    with patch.object(provider, "async_credentials", return_value=[credentials1]):
        credentials2 = await provider.async_get_or_create_credentials(
            {"username": "hello"}
        )
    assert credentials1 is credentials2

    with patch.object(provider, "async_credentials", return_value=[credentials1]):
        credentials3 = await provider.async_get_or_create_credentials(
            {"username": "hello "}
        )
    assert credentials1 is not credentials3


async def test_race_condition_in_data_loading.opp):
    """Test race condition in the.opp_auth.Data loading.

    Ref issue: https://github.com/open-peer-power/core/issues/21569
    """
    counter = 0

    async def mock_load(_):
        """Mock of openpeerpower.helpers.storage.Store.async_load."""
        nonlocal counter
        counter += 1
        await asyncio.sleep(0)

    provider = opp_auth.HassAuthProvider(
        opp. auth_store.AuthStore.opp), {"type": "openpeerpower"}
    )
    with patch("openpeerpower.helpers.storage.Store.async_load", new=mock_load):
        task1 = provider.async_validate_login("user", "pass")
        task2 = provider.async_validate_login("user", "pass")
        results = await asyncio.gather(task1, task2, return_exceptions=True)
        assert counter == 1
        assert isinstance(results[0], opp_auth.InvalidAuth)
        # results[1] will be a TypeError if race condition occurred
        assert isinstance(results[1], opp_auth.InvalidAuth)
