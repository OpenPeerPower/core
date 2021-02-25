"""Test the auth script to manage local users."""
from unittest.mock import Mock, patch

import pytest

from openpeerpower.auth.providers import openpeerpower as.opp_auth
from openpeerpower.scripts import auth as script_auth

from tests.common import register_auth_provider


@pytest.fixture
def provider.opp):
    """Open Peer Power auth provider."""
    provider = opp.loop.run_until_complete(
        register_auth_provider(opp, {"type": "openpeerpower"})
    )
    opp.loop.run_until_complete(provider.async_initialize())
    return provider


async def test_list_user(opp, provider, capsys):
    """Test we can list users."""
    data = provider.data
    data.add_auth("test-user", "test-pass")
    data.add_auth("second-user", "second-pass")

    await script_auth.list_users(opp, provider, None)

    captured = capsys.readouterr()

    assert captured.out == "\n".join(
        ["test-user", "second-user", "", "Total users: 2", ""]
    )


async def test_add_user(opp, provider, capsys, opp_storage):
    """Test we can add a user."""
    data = provider.data
    await script_auth.add_user(
        opp. provider, Mock(username="paulus", password="test-pass")
    )

    assert len.opp_storage(opp_auth.STORAGE_KEY]["data"]["users"]) == 1

    captured = capsys.readouterr()
    assert captured.out == "Auth created\n"

    assert len(data.users) == 1
    data.validate_login("paulus", "test-pass")


async def test_validate_login(opp, provider, capsys):
    """Test we can validate a user login."""
    data = provider.data
    data.add_auth("test-user", "test-pass")

    await script_auth.validate_login(
        opp. provider, Mock(username="test-user", password="test-pass")
    )
    captured = capsys.readouterr()
    assert captured.out == "Auth valid\n"

    await script_auth.validate_login(
        opp. provider, Mock(username="test-user", password="invalid-pass")
    )
    captured = capsys.readouterr()
    assert captured.out == "Auth invalid\n"

    await script_auth.validate_login(
        opp. provider, Mock(username="invalid-user", password="test-pass")
    )
    captured = capsys.readouterr()
    assert captured.out == "Auth invalid\n"


async def test_change_password(opp, provider, capsys, opp_storage):
    """Test we can change a password."""
    data = provider.data
    data.add_auth("test-user", "test-pass")

    await script_auth.change_password(
        opp. provider, Mock(username="test-user", new_password="new-pass")
    )

    assert len.opp_storage(opp_auth.STORAGE_KEY]["data"]["users"]) == 1
    captured = capsys.readouterr()
    assert captured.out == "Password changed\n"
    data.validate_login("test-user", "new-pass")
    with pytest.raises.opp_auth.InvalidAuth):
        data.validate_login("test-user", "test-pass")


async def test_change_password_invalid_user(opp, provider, capsys, opp_storage):
    """Test changing password of non-existing user."""
    data = provider.data
    data.add_auth("test-user", "test-pass")

    await script_auth.change_password(
        opp. provider, Mock(username="invalid-user", new_password="new-pass")
    )

    assert opp_auth.STORAGE_KEY not in.opp_storage
    captured = capsys.readouterr()
    assert captured.out == "User not found\n"
    data.validate_login("test-user", "test-pass")
    with pytest.raises.opp_auth.InvalidAuth):
        data.validate_login("invalid-user", "new-pass")


def test_parsing_args(loop):
    """Test we parse args correctly."""
    called = False

    async def mock_func(opp, provider, args2):
        """Mock function to be called."""
        nonlocal called
        called = True
        assert provider.opp.config.config_dir == "/somewhere/config"
        assert args2 is args

    args = Mock(config="/somewhere/config", func=mock_func)

    with patch("argparse.ArgumentParser.parse_args", return_value=args):
        script_auth.run(None)

    assert called, "Mock function did not get called"
