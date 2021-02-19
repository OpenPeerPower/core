"""Tests for the Google Hangouts config flow."""

from unittest.mock import patch

from openpeerpower import data_entry_flow
from openpeerpower.components.hangouts import config_flow
from openpeerpower.const import CONF_EMAIL, CONF_PASSWORD

EMAIL = "test@test.com"
PASSWORD = "1232456"


async def test_flow_works.opp, aioclient_mock):
    """Test config flow without 2fa."""
    flow = config_flow.HangoutsFlowHandler()

    flow.opp =.opp

    with patch("openpeerpower.components.hangouts.config_flow.get_auth"):
        result = await flow.async_step_user(
            {CONF_EMAIL: EMAIL, CONF_PASSWORD: PASSWORD}
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == EMAIL


async def test_flow_works_with_authcode.opp, aioclient_mock):
    """Test config flow without 2fa."""
    flow = config_flow.HangoutsFlowHandler()

    flow.opp =.opp

    with patch("openpeerpower.components.hangouts.config_flow.get_auth"):
        result = await flow.async_step_user(
            {
                CONF_EMAIL: EMAIL,
                CONF_PASSWORD: PASSWORD,
                "authorization_code": "c29tZXJhbmRvbXN0cmluZw==",
            }
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == EMAIL


async def test_flow_works_with_2fa.opp, aioclient_mock):
    """Test config flow with 2fa."""
    from openpeerpower.components.hangouts.hangups_utils import Google2FAError

    flow = config_flow.HangoutsFlowHandler()

    flow.opp =.opp

    with patch(
        "openpeerpower.components.hangouts.config_flow.get_auth",
        side_effect=Google2FAError,
    ):
        result = await flow.async_step_user(
            {CONF_EMAIL: EMAIL, CONF_PASSWORD: PASSWORD}
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "2fa"

    with patch("openpeerpower.components.hangouts.config_flow.get_auth"):
        result = await flow.async_step_2fa({"2fa": 123456})
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == EMAIL


async def test_flow_with_unknown_2fa.opp, aioclient_mock):
    """Test config flow with invalid 2fa method."""
    from openpeerpower.components.hangouts.hangups_utils import GoogleAuthError

    flow = config_flow.HangoutsFlowHandler()

    flow.opp =.opp

    with patch(
        "openpeerpower.components.hangouts.config_flow.get_auth",
        side_effect=GoogleAuthError("Unknown verification code input"),
    ):
        result = await flow.async_step_user(
            {CONF_EMAIL: EMAIL, CONF_PASSWORD: PASSWORD}
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"]["base"] == "invalid_2fa_method"


async def test_flow_invalid_login.opp, aioclient_mock):
    """Test config flow with invalid 2fa method."""
    from openpeerpower.components.hangouts.hangups_utils import GoogleAuthError

    flow = config_flow.HangoutsFlowHandler()

    flow.opp =.opp

    with patch(
        "openpeerpower.components.hangouts.config_flow.get_auth",
        side_effect=GoogleAuthError,
    ):
        result = await flow.async_step_user(
            {CONF_EMAIL: EMAIL, CONF_PASSWORD: PASSWORD}
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"]["base"] == "invalid_login"


async def test_flow_invalid_2fa.opp, aioclient_mock):
    """Test config flow with 2fa."""
    from openpeerpower.components.hangouts.hangups_utils import Google2FAError

    flow = config_flow.HangoutsFlowHandler()

    flow.opp =.opp

    with patch(
        "openpeerpower.components.hangouts.config_flow.get_auth",
        side_effect=Google2FAError,
    ):
        result = await flow.async_step_user(
            {CONF_EMAIL: EMAIL, CONF_PASSWORD: PASSWORD}
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "2fa"

    with patch(
        "openpeerpower.components.hangouts.config_flow.get_auth",
        side_effect=Google2FAError,
    ):
        result = await flow.async_step_2fa({"2fa": 123456})

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"]["base"] == "invalid_2fa"
