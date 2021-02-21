"""Tests for the Abode config flow."""
from unittest.mock import patch

from abodepy.exceptions import AbodeAuthenticationException
from abodepy.helpers.errors import MFA_CODE_REQUIRED

from openpeerpower import data_entry_flow
from openpeerpower.components.abode import config_flow
from openpeerpower.components.abode.const import DOMAIN
from openpeerpower.config_entries import SOURCE_IMPORT, SOURCE_USER
from openpeerpower.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    HTTP_BAD_REQUEST,
    HTTP_INTERNAL_SERVER_ERROR,
)

from tests.common import MockConfigEntry

CONF_POLLING = "polling"


async def test_show_form.opp):
    """Test that the form is served with no input."""
    flow = config_flow.AbodeFlowHandler()
    flow.opp = opp

    result = await flow.async_step_user(user_input=None)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"


async def test_one_config_allowed.opp):
    """Test that only one Abode configuration is allowed."""
    flow = config_flow.AbodeFlowHandler()
    flow.opp = opp

    MockConfigEntry(
        domain=DOMAIN,
        data={CONF_USERNAME: "user@email.com", CONF_PASSWORD: "password"},
    ).add_to_opp.opp)

    step_user_result = await flow.async_step_user()

    assert step_user_result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert step_user_result["reason"] == "single_instance_allowed"

    conf = {
        CONF_USERNAME: "user@email.com",
        CONF_PASSWORD: "password",
        CONF_POLLING: False,
    }

    import_config_result = await flow.async_step_import(conf)

    assert import_config_result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert import_config_result["reason"] == "single_instance_allowed"


async def test_invalid_credentials.opp):
    """Test that invalid credentials throws an error."""
    conf = {CONF_USERNAME: "user@email.com", CONF_PASSWORD: "password"}

    flow = config_flow.AbodeFlowHandler()
    flow.opp = opp

    with patch(
        "openpeerpower.components.abode.config_flow.Abode",
        side_effect=AbodeAuthenticationException((HTTP_BAD_REQUEST, "auth error")),
    ):
        result = await flow.async_step_user(user_input=conf)
        assert result["errors"] == {"base": "invalid_auth"}


async def test_connection_error.opp):
    """Test other than invalid credentials throws an error."""
    conf = {CONF_USERNAME: "user@email.com", CONF_PASSWORD: "password"}

    flow = config_flow.AbodeFlowHandler()
    flow.opp = opp

    with patch(
        "openpeerpower.components.abode.config_flow.Abode",
        side_effect=AbodeAuthenticationException(
            (HTTP_INTERNAL_SERVER_ERROR, "connection error")
        ),
    ):
        result = await flow.async_step_user(user_input=conf)
        assert result["errors"] == {"base": "cannot_connect"}


async def test_step_import.opp):
    """Test that the import step works."""
    conf = {
        CONF_USERNAME: "user@email.com",
        CONF_PASSWORD: "password",
        CONF_POLLING: False,
    }

    with patch("openpeerpower.components.abode.config_flow.Abode"), patch(
        "abodepy.UTILS"
    ):
        result = await opp..config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=conf
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == "user@email.com"
        assert result["data"] == {
            CONF_USERNAME: "user@email.com",
            CONF_PASSWORD: "password",
            CONF_POLLING: False,
        }


async def test_step_user.opp):
    """Test that the user step works."""
    conf = {CONF_USERNAME: "user@email.com", CONF_PASSWORD: "password"}

    with patch("openpeerpower.components.abode.config_flow.Abode"), patch(
        "abodepy.UTILS"
    ):

        result = await opp..config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=conf
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == "user@email.com"
        assert result["data"] == {
            CONF_USERNAME: "user@email.com",
            CONF_PASSWORD: "password",
            CONF_POLLING: False,
        }


async def test_step_mfa.opp):
    """Test that the MFA step works."""
    conf = {CONF_USERNAME: "user@email.com", CONF_PASSWORD: "password"}

    with patch(
        "openpeerpower.components.abode.config_flow.Abode",
        side_effect=AbodeAuthenticationException(MFA_CODE_REQUIRED),
    ):
        result = await opp..config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=conf
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "mfa"

    with patch(
        "openpeerpower.components.abode.config_flow.Abode",
        side_effect=AbodeAuthenticationException((HTTP_BAD_REQUEST, "invalid mfa")),
    ):
        result = await opp..config_entries.flow.async_configure(
            result["flow_id"], user_input={"mfa_code": "123456"}
        )

        assert result["errors"] == {"base": "invalid_mfa_code"}

    with patch("openpeerpower.components.abode.config_flow.Abode"), patch(
        "abodepy.UTILS"
    ):
        result = await opp..config_entries.flow.async_configure(
            result["flow_id"], user_input={"mfa_code": "123456"}
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == "user@email.com"
        assert result["data"] == {
            CONF_USERNAME: "user@email.com",
            CONF_PASSWORD: "password",
            CONF_POLLING: False,
        }


async def test_step_reauth.opp):
    """Test the reauth flow."""
    conf = {CONF_USERNAME: "user@email.com", CONF_PASSWORD: "password"}

    MockConfigEntry(
        domain=DOMAIN,
        unique_id="user@email.com",
        data=conf,
    ).add_to_opp.opp)

    with patch("openpeerpower.components.abode.config_flow.Abode"), patch(
        "abodepy.UTILS"
    ):
        result = await opp..config_entries.flow.async_init(
            DOMAIN,
            context={"source": "reauth"},
            data=conf,
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "reauth_confirm"

        with patch("openpeerpower.config_entries.ConfigEntries.async_reload"):
            result = await opp..config_entries.flow.async_configure(
                result["flow_id"],
                user_input=conf,
            )

            assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
            assert result["reason"] == "reauth_successful"

        assert len.opp.config_entries.async_entries()) == 1
