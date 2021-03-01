"""The gateway tests for the august platform."""
from unittest.mock import MagicMock, patch

from august.authenticator_common import AuthenticationState

from openpeerpower.components.august.const import DOMAIN
from openpeerpower.components.august.gateway import AugustGateway

from tests.components.august.mocks import _mock_august_authentication, _mock_get_config


async def test_refresh_access_token(opp):
    """Test token refreshes."""
    await _patched_refresh_access_token(opp, "new_token", 5678)


@patch("openpeerpower.components.august.gateway.ApiAsync.async_get_operable_locks")
@patch("openpeerpower.components.august.gateway.AuthenticatorAsync.async_authenticate")
@patch("openpeerpower.components.august.gateway.AuthenticatorAsync.should_refresh")
@patch(
    "openpeerpower.components.august.gateway.AuthenticatorAsync.async_refresh_access_token"
)
async def _patched_refresh_access_token(
    opp,
    new_token,
    new_token_expire_time,
    refresh_access_token_mock,
    should_refresh_mock,
    authenticate_mock,
    async_get_operable_locks_mock,
):
    authenticate_mock.side_effect = MagicMock(
        return_value=_mock_august_authentication(
            "original_token", 1234, AuthenticationState.AUTHENTICATED
        )
    )
    august_gateway = AugustGateway(opp)
    mocked_config = _mock_get_config()
    await august_gateway.async_setup(mocked_config[DOMAIN])
    await august_gateway.async_authenticate()

    should_refresh_mock.return_value = False
    await august_gateway.async_refresh_access_token_if_needed()
    refresh_access_token_mock.assert_not_called()

    should_refresh_mock.return_value = True
    refresh_access_token_mock.return_value = _mock_august_authentication(
        new_token, new_token_expire_time, AuthenticationState.AUTHENTICATED
    )
    await august_gateway.async_refresh_access_token_if_needed()
    refresh_access_token_mock.assert_called()
    assert august_gateway.access_token == new_token
    assert august_gateway.authentication.access_token_expires == new_token_expire_time
