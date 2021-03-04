"""Tests for the TotalConnect config flow."""
from unittest.mock import patch

from openpeerpower import data_entry_flow
from openpeerpower.components.totalconnect.const import CONF_LOCATION, DOMAIN
from openpeerpower.config_entries import SOURCE_USER
from openpeerpower.const import CONF_PASSWORD

from .common import (
    CONFIG_DATA,
    CONFIG_DATA_NO_USERCODES,
    RESPONSE_AUTHENTICATE,
    RESPONSE_DISARMED,
    RESPONSE_SUCCESS,
    RESPONSE_USER_CODE_INVALID,
    USERNAME,
)

from tests.common import MockConfigEntry


async def test_user(opp):
    """Test user step."""
    # user starts with no data entered, so show the user form
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=None,
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"


async def test_user_show_locations(opp):
    """Test user locations form."""
    # user/pass provided, so check if valid then ask for usercodes on locations form
    responses = [
        RESPONSE_AUTHENTICATE,
        RESPONSE_DISARMED,
        RESPONSE_USER_CODE_INVALID,
        RESPONSE_SUCCESS,
    ]

    with patch("zeep.Client", autospec=True), patch(
        "openpeerpower.components.totalconnect.TotalConnectClient.TotalConnectClient.request",
        side_effect=responses,
    ) as mock_request, patch(
        "openpeerpower.components.totalconnect.TotalConnectClient.TotalConnectClient.get_zone_details",
        return_value=True,
    ), patch(
        "openpeerpower.components.totalconnect.async_setup_entry", return_value=True
    ):

        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=CONFIG_DATA_NO_USERCODES,
        )

        # first it should show the locations form
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "locations"
        # client should have sent two requests, authenticate and get status
        assert mock_request.call_count == 2

        # user enters an invalid usercode
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_LOCATION: "bad"},
        )
        assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result2["step_id"] == "locations"
        # client should have sent 3rd request to validate usercode
        assert mock_request.call_count == 3

        # user enters a valid usercode
        result3 = await opp.config_entries.flow.async_configure(
            result2["flow_id"],
            user_input={CONF_LOCATION: "7890"},
        )
        assert result3["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        # client should have sent another request to validate usercode
        assert mock_request.call_count == 4


async def test_abort_if_already_setup(opp):
    """Test abort if the account is already setup."""
    MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG_DATA,
        unique_id=USERNAME,
    ).add_to_opp(opp)

    # Should fail, same USERNAME (flow)
    with patch(
        "openpeerpower.components.totalconnect.config_flow.TotalConnectClient.TotalConnectClient"
    ) as client_mock:
        client_mock.return_value.is_valid_credentials.return_value = True
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=CONFIG_DATA,
        )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_login_failed(opp):
    """Test when we have errors during login."""
    with patch(
        "openpeerpower.components.totalconnect.config_flow.TotalConnectClient.TotalConnectClient"
    ) as client_mock:
        client_mock.return_value.is_valid_credentials.return_value = False
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=CONFIG_DATA,
        )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_reauth(opp):
    """Test reauth."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG_DATA,
        unique_id=USERNAME,
    )
    entry.add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": "reauth"}, data=entry.data
    )
    assert result["step_id"] == "reauth_confirm"

    result = await opp.config_entries.flow.async_configure(result["flow_id"])
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "reauth_confirm"

    with patch(
        "openpeerpower.components.totalconnect.config_flow.TotalConnectClient.TotalConnectClient"
    ) as client_mock:
        # first test with an invalid password
        client_mock.return_value.is_valid_credentials.return_value = False

        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_PASSWORD: "password"}
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "reauth_confirm"
        assert result["errors"] == {"base": "invalid_auth"}

        # now test with the password valid
        client_mock.return_value.is_valid_credentials.return_value = True

        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_PASSWORD: "password"}
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result["reason"] == "reauth_successful"

    assert len(opp.config_entries.async_entries()) == 1
