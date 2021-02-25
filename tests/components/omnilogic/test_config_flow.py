"""Test the Omnilogic config flow."""
from unittest.mock import patch

from omnilogic import LoginException, OmniLogicException

from openpeerpower import config_entries, data_entry_flow, setup
from openpeerpower.components.omnilogic.const import DOMAIN

from tests.common import MockConfigEntry

DATA = {"username": "test-username", "password": "test-password"}


async def test_form.opp):
    """Test we get the form."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.omnilogic.config_flow.OmniLogic.connect",
        return_value=True,
    ), patch(
        "openpeerpower.components.omnilogic.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.omnilogic.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            DATA,
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "Omnilogic"
    assert result2["data"] == DATA
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_already_configured.opp):
    """Test config flow when Omnilogic component is already setup."""
    MockConfigEntry(domain="omnilogic", data=DATA).add_to_opp(opp)

    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "abort"
    assert result["reason"] == "single_instance_allowed"


async def test_with_invalid_credentials.opp):
    """Test with invalid credentials."""

    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.omnilogic.OmniLogic.connect",
        side_effect=LoginException,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            DATA,
        )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect.opp):
    """Test if invalid response or no connection returned from Hayward."""

    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.omnilogic.OmniLogic.connect",
        side_effect=OmniLogicException,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            DATA,
        )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_with_unknown_error(opp):
    """Test with unknown error response from Hayward."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.omnilogic.OmniLogic.connect",
        side_effect=Exception,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            DATA,
        )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "unknown"}


async def test_option_flow.opp):
    """Test option flow."""
    entry = MockConfigEntry(domain=DOMAIN, data=DATA)
    entry.add_to_opp(opp)

    assert not entry.options

    with patch(
        "openpeerpower.components.omnilogic.async_setup_entry", return_value=True
    ):
        result = await opp.config_entries.options.async_init(
            entry.entry_id,
            data=None,
        )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"polling_interval": 9},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == ""
    assert result["data"]["polling_interval"] == 9
