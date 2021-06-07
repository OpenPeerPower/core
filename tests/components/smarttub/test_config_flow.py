"""Test the smarttub config flow."""
from unittest.mock import patch

from smarttub import LoginFailed

from openpeerpower import config_entries, data_entry_flow
from openpeerpower.components.smarttub.const import DOMAIN
from openpeerpower.const import CONF_EMAIL, CONF_PASSWORD

from tests.common import MockConfigEntry


async def test_form(opp):
    """Test we get the form."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.smarttub.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_EMAIL: "test-email", CONF_PASSWORD: "test-password"},
        )

        assert result["type"] == "create_entry"
        assert result["title"] == "test-email"
        assert result["data"] == {
            CONF_EMAIL: "test-email",
            CONF_PASSWORD: "test-password",
        }
        await opp.async_block_till_done()
        mock_setup_entry.assert_called_once()


async def test_form_invalid_auth(opp, smarttub_api):
    """Test we handle invalid auth."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    smarttub_api.login.side_effect = LoginFailed

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "test-email", CONF_PASSWORD: "test-password"},
    )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "invalid_auth"}


async def test_reauth_success(opp, smarttub_api, account):
    """Test reauthentication flow."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_EMAIL: "test-email", CONF_PASSWORD: "test-password"},
        unique_id=account.id,
    )
    mock_entry.add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "unique_id": mock_entry.unique_id,
            "entry_id": mock_entry.entry_id,
        },
        data=mock_entry.data,
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "reauth_confirm"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], {CONF_EMAIL: "test-email3", CONF_PASSWORD: "test-password3"}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_entry.data[CONF_EMAIL] == "test-email3"
    assert mock_entry.data[CONF_PASSWORD] == "test-password3"


async def test_reauth_wrong_account(opp, smarttub_api, account):
    """Test reauthentication flow if the user enters credentials for a different already-configured account."""
    mock_entry1 = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_EMAIL: "test-email1", CONF_PASSWORD: "test-password1"},
        unique_id=account.id,
    )
    mock_entry1.add_to_opp(opp)

    mock_entry2 = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_EMAIL: "test-email2", CONF_PASSWORD: "test-password2"},
        unique_id="mockaccount2",
    )
    mock_entry2.add_to_opp(opp)

    # we try to reauth account #2, and the user successfully authenticates to account #1
    account.id = mock_entry1.unique_id
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "unique_id": mock_entry2.unique_id,
            "entry_id": mock_entry2.entry_id,
        },
        data=mock_entry2.data,
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "reauth_confirm"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], {CONF_EMAIL: "test-email1", CONF_PASSWORD: "test-password1"}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"
