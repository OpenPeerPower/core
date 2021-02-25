"""Define tests for the SimpliSafe config flow."""
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

from simplipy.errors import (
    InvalidCredentialsError,
    PendingAuthorizationError,
    SimplipyError,
)

from openpeerpower import data_entry_flow
from openpeerpower.components.simplisafe import DOMAIN
from openpeerpower.config_entries import SOURCE_USER
from openpeerpower.const import CONF_CODE, CONF_PASSWORD, CONF_TOKEN, CONF_USERNAME

from tests.common import MockConfigEntry


def mock_api():
    """Mock SimpliSafe API class."""
    api = MagicMock()
    type(api).refresh_token = PropertyMock(return_value="12345abc")
    return api


async def test_duplicate_error(opp):
    """Test that errors are shown when duplicates are added."""
    conf = {
        CONF_USERNAME: "user@email.com",
        CONF_PASSWORD: "password",
        CONF_CODE: "1234",
    }

    MockConfigEntry(
        domain=DOMAIN,
        unique_id="user@email.com",
        data={CONF_USERNAME: "user@email.com", CONF_TOKEN: "12345", CONF_CODE: "1234"},
    ).add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=conf
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_invalid_credentials(opp):
    """Test that invalid credentials throws an error."""
    conf = {CONF_USERNAME: "user@email.com", CONF_PASSWORD: "password"}

    with patch(
        "simplipy.API.login_via_credentials",
        new=AsyncMock(side_effect=InvalidCredentialsError),
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=conf
        )
        assert result["errors"] == {"base": "invalid_auth"}


async def test_options_flow(opp):
    """Test config flow options."""
    conf = {CONF_USERNAME: "user@email.com", CONF_PASSWORD: "password"}

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="abcde12345",
        data=conf,
        options={CONF_CODE: "1234"},
    )
    config_entry.add_to_opp(opp)

    with patch(
        "openpeerpower.components.simplisafe.async_setup_entry", return_value=True
    ):
        await opp.config_entries.async_setup(config_entry.entry_id)
        result = await opp.config_entries.options.async_init(config_entry.entry_id)

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "init"

        result = await opp.config_entries.options.async_configure(
            result["flow_id"], user_input={CONF_CODE: "4321"}
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert config_entry.options == {CONF_CODE: "4321"}


async def test_show_form(opp):
    """Test that the form is served with no input."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"


async def test_step_reauth(opp):
    """Test that the reauth step works."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id="user@email.com",
        data={CONF_USERNAME: "user@email.com", CONF_TOKEN: "12345", CONF_CODE: "1234"},
    ).add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "reauth"},
        data={CONF_CODE: "1234", CONF_USERNAME: "user@email.com"},
    )
    assert result["step_id"] == "reauth_confirm"

    result = await opp.config_entries.flow.async_configure(result["flow_id"])
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "reauth_confirm"

    with patch(
        "openpeerpower.components.simplisafe.async_setup_entry", return_value=True
    ), patch(
        "simplipy.API.login_via_credentials", new=AsyncMock(return_value=mock_api())
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_PASSWORD: "password"}
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result["reason"] == "reauth_successful"

    assert len(opp.config_entries.async_entries()) == 1


async def test_step_user(opp):
    """Test that the user step works (without MFA)."""
    conf = {
        CONF_USERNAME: "user@email.com",
        CONF_PASSWORD: "password",
        CONF_CODE: "1234",
    }

    with patch(
        "openpeerpower.components.simplisafe.async_setup_entry", return_value=True
    ), patch(
        "simplipy.API.login_via_credentials", new=AsyncMock(return_value=mock_api())
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=conf
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == "user@email.com"
        assert result["data"] == {
            CONF_USERNAME: "user@email.com",
            CONF_TOKEN: "12345abc",
            CONF_CODE: "1234",
        }


async def test_step_user_mfa(opp):
    """Test that the user step works when MFA is in the middle."""
    conf = {
        CONF_USERNAME: "user@email.com",
        CONF_PASSWORD: "password",
        CONF_CODE: "1234",
    }

    with patch(
        "simplipy.API.login_via_credentials",
        new=AsyncMock(side_effect=PendingAuthorizationError),
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=conf
        )
        assert result["step_id"] == "mfa"

    with patch(
        "simplipy.API.login_via_credentials",
        new=AsyncMock(side_effect=PendingAuthorizationError),
    ):
        # Simulate the user pressing the MFA submit button without having clicked
        # the link in the MFA email:
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        assert result["step_id"] == "mfa"

    with patch(
        "openpeerpower.components.simplisafe.async_setup_entry", return_value=True
    ), patch(
        "simplipy.API.login_via_credentials", new=AsyncMock(return_value=mock_api())
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == "user@email.com"
        assert result["data"] == {
            CONF_USERNAME: "user@email.com",
            CONF_TOKEN: "12345abc",
            CONF_CODE: "1234",
        }


async def test_unknown_error(opp):
    """Test that an unknown error raises the correct error."""
    conf = {CONF_USERNAME: "user@email.com", CONF_PASSWORD: "password"}

    with patch(
        "simplipy.API.login_via_credentials",
        new=AsyncMock(side_effect=SimplipyError),
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=conf
        )
        assert result["errors"] == {"base": "unknown"}
