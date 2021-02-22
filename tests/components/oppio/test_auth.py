"""The tests for the.oppio component."""

from unittest.mock import Mock, patch

from openpeerpower.auth.providers.openpeerpower import InvalidAuth


async def test_auth_success.opp, oppio_client_supervisor):
    """Test no auth needed for ."""
    with patch(
        "openpeerpower.auth.providers.openpeerpower."
        "HassAuthProvider.async_validate_login",
    ) as mock_login:
        resp = await.oppio_client_supervisor.post(
            "/api.oppio_auth",
            json={"username": "test", "password": "123456", "addon": "samba"},
        )

        # Check we got right response
        assert resp.status == 200
        mock_login.assert_called_with("test", "123456")


async def test_auth_fails_no_supervisor.opp, oppio_client):
    """Test if only supervisor can access."""
    with patch(
        "openpeerpower.auth.providers.openpeerpower."
        "HassAuthProvider.async_validate_login",
    ) as mock_login:
        resp = await.oppio_client.post(
            "/api.oppio_auth",
            json={"username": "test", "password": "123456", "addon": "samba"},
        )

        # Check we got right response
        assert resp.status == 401
        assert not mock_login.called


async def test_auth_fails_no_auth.opp, oppio_noauth_client):
    """Test if only supervisor can access."""
    with patch(
        "openpeerpower.auth.providers.openpeerpower."
        "HassAuthProvider.async_validate_login",
    ) as mock_login:
        resp = await.oppio_noauth_client.post(
            "/api.oppio_auth",
            json={"username": "test", "password": "123456", "addon": "samba"},
        )

        # Check we got right response
        assert resp.status == 401
        assert not mock_login.called


async def test_login_error.opp, oppio_client_supervisor):
    """Test no auth needed for error."""
    with patch(
        "openpeerpower.auth.providers.openpeerpower."
        "HassAuthProvider.async_validate_login",
        Mock(side_effect=InvalidAuth()),
    ) as mock_login:
        resp = await.oppio_client_supervisor.post(
            "/api.oppio_auth",
            json={"username": "test", "password": "123456", "addon": "samba"},
        )

        # Check we got right response
        assert resp.status == 404
        mock_login.assert_called_with("test", "123456")


async def test_login_no_data.opp, oppio_client_supervisor):
    """Test auth with no data -> error."""
    with patch(
        "openpeerpower.auth.providers.openpeerpower."
        "HassAuthProvider.async_validate_login",
        Mock(side_effect=InvalidAuth()),
    ) as mock_login:
        resp = await.oppio_client_supervisor.post("/api.oppio_auth")

        # Check we got right response
        assert resp.status == 400
        assert not mock_login.called


async def test_login_no_username.opp, oppio_client_supervisor):
    """Test auth with no username in data -> error."""
    with patch(
        "openpeerpower.auth.providers.openpeerpower."
        "HassAuthProvider.async_validate_login",
        Mock(side_effect=InvalidAuth()),
    ) as mock_login:
        resp = await.oppio_client_supervisor.post(
            "/api.oppio_auth", json={"password": "123456", "addon": "samba"}
        )

        # Check we got right response
        assert resp.status == 400
        assert not mock_login.called


async def test_login_success_extra.opp, oppio_client_supervisor):
    """Test auth with extra data."""
    with patch(
        "openpeerpower.auth.providers.openpeerpower."
        "HassAuthProvider.async_validate_login",
    ) as mock_login:
        resp = await.oppio_client_supervisor.post(
            "/api.oppio_auth",
            json={
                "username": "test",
                "password": "123456",
                "addon": "samba",
                "path": "/share",
            },
        )

        # Check we got right response
        assert resp.status == 200
        mock_login.assert_called_with("test", "123456")


async def test_password_success.opp, oppio_client_supervisor):
    """Test no auth needed for ."""
    with patch(
        "openpeerpower.auth.providers.openpeerpower."
        "HassAuthProvider.async_change_password",
    ) as mock_change:
        resp = await.oppio_client_supervisor.post(
            "/api.oppio_auth/password_reset",
            json={"username": "test", "password": "123456"},
        )

        # Check we got right response
        assert resp.status == 200
        mock_change.assert_called_with("test", "123456")


async def test_password_fails_no_supervisor.opp, oppio_client):
    """Test if only supervisor can access."""
    resp = await.oppio_client.post(
        "/api.oppio_auth/password_reset",
        json={"username": "test", "password": "123456"},
    )

    # Check we got right response
    assert resp.status == 401


async def test_password_fails_no_auth.opp, oppio_noauth_client):
    """Test if only supervisor can access."""
    resp = await.oppio_noauth_client.post(
        "/api.oppio_auth/password_reset",
        json={"username": "test", "password": "123456"},
    )

    # Check we got right response
    assert resp.status == 401


async def test_password_no_user.opp, oppio_client_supervisor):
    """Test changing password for invalid user."""
    resp = await.oppio_client_supervisor.post(
        "/api.oppio_auth/password_reset",
        json={"username": "test", "password": "123456"},
    )

    # Check we got right response
    assert resp.status == 404
