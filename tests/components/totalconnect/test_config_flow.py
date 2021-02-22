"""Tests for the iCloud config flow."""
from unittest.mock import patch

from openpeerpower import data_entry_flow
from openpeerpower.components.totalconnect.const import DOMAIN
from openpeerpower.config_entries import SOURCE_IMPORT, SOURCE_USER
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry

USERNAME = "username@me.com"
PASSWORD = "password"


async def test_user.opp):
    """Test user config."""
    # no data provided so show the form
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    # now data is provided, so check if login is correct and create the entry
    with patch(
        "openpeerpower.components.totalconnect.config_flow.TotalConnectClient.TotalConnectClient"
    ) as client_mock:
        client_mock.return_value.is_valid_credentials.return_value = True
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
        )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY


async def test_import.opp):
    """Test import step with good username and password."""
    with patch(
        "openpeerpower.components.totalconnect.config_flow.TotalConnectClient.TotalConnectClient"
    ) as client_mock:
        client_mock.return_value.is_valid_credentials.return_value = True
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
        )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY


async def test_abort_if_already_setup_opp):
    """Test abort if the account is already setup."""
    MockConfigEntry(
        domain=DOMAIN,
        data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
        unique_id=USERNAME,
    ).add_to.opp.opp)

    # Should fail, same USERNAME (import)
    with patch(
        "openpeerpower.components.totalconnect.config_flow.TotalConnectClient.TotalConnectClient"
    ) as client_mock:
        client_mock.return_value.is_valid_credentials.return_value = True
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
        )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"

    # Should fail, same USERNAME (flow)
    with patch(
        "openpeerpower.components.totalconnect.config_flow.TotalConnectClient.TotalConnectClient"
    ) as client_mock:
        client_mock.return_value.is_valid_credentials.return_value = True
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
        )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_login_failed.opp):
    """Test when we have errors during login."""
    with patch(
        "openpeerpower.components.totalconnect.config_flow.TotalConnectClient.TotalConnectClient"
    ) as client_mock:
        client_mock.return_value.is_valid_credentials.return_value = False
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
        )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {"base": "invalid_auth"}
