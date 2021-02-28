"""Tests for the Econet component."""
from unittest.mock import patch

from pyeconet.api import EcoNetApiInterface
from pyeconet.errors import InvalidCredentialsError, PyeconetError

from openpeerpower.components.econet import DOMAIN
from openpeerpower.config_entries import SOURCE_USER
from openpeerpower.const import CONF_EMAIL, CONF_PASSWORD
from openpeerpower.data_entry_flow import (
    RESULT_TYPE_ABORT,
    RESULT_TYPE_CREATE_ENTRY,
    RESULT_TYPE_FORM,
)

from tests.common import MockConfigEntry


async def test_bad_credentials(opp):
    """Test when provided credentials are rejected."""

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == SOURCE_USER

    with patch(
        "pyeconet.EcoNetApiInterface.login",
        side_effect=InvalidCredentialsError(),
    ), patch("openpeerpower.components.econet.async_setup", return_value=True), patch(
        "openpeerpower.components.econet.async_setup_entry", return_value=True
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_EMAIL: "admin@localhost.com",
                CONF_PASSWORD: "password0",
            },
        )

        assert result["type"] == RESULT_TYPE_FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {
            "base": "invalid_auth",
        }


async def test_generic_error_from_library(opp):
    """Test when connection fails."""

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == SOURCE_USER

    with patch(
        "pyeconet.EcoNetApiInterface.login",
        side_effect=PyeconetError(),
    ), patch("openpeerpower.components.econet.async_setup", return_value=True), patch(
        "openpeerpower.components.econet.async_setup_entry", return_value=True
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_EMAIL: "admin@localhost.com",
                CONF_PASSWORD: "password0",
            },
        )

        assert result["type"] == RESULT_TYPE_FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {
            "base": "cannot_connect",
        }


async def test_auth_worked(opp):
    """Test when provided credentials are accepted."""

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == SOURCE_USER

    with patch(
        "pyeconet.EcoNetApiInterface.login",
        return_value=EcoNetApiInterface,
    ), patch("openpeerpower.components.econet.async_setup", return_value=True), patch(
        "openpeerpower.components.econet.async_setup_entry", return_value=True
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_EMAIL: "admin@localhost.com",
                CONF_PASSWORD: "password0",
            },
        )

        assert result["type"] == RESULT_TYPE_CREATE_ENTRY
        assert result["data"] == {
            CONF_EMAIL: "admin@localhost.com",
            CONF_PASSWORD: "password0",
        }


async def test_already_configured(opp):
    """Test when provided credentials are already configured."""
    config = {
        CONF_EMAIL: "admin@localhost.com",
        CONF_PASSWORD: "password0",
    }
    MockConfigEntry(
        domain=DOMAIN, data=config, unique_id="admin@localhost.com"
    ).add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == SOURCE_USER

    with patch(
        "pyeconet.EcoNetApiInterface.login",
        return_value=EcoNetApiInterface,
    ), patch("openpeerpower.components.econet.async_setup", return_value=True), patch(
        "openpeerpower.components.econet.async_setup_entry", return_value=True
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_EMAIL: "admin@localhost.com",
                CONF_PASSWORD: "password0",
            },
        )

    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"
