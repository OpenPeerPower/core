"""Test the SRP Energy config flow."""
from unittest.mock import patch

from openpeerpower import config_entries, data_entry_flow
from openpeerpower.components.srp_energy.const import CONF_IS_TOU, SRP_ENERGY_DOMAIN

from . import ENTRY_CONFIG, init_integration


async def test_form(opp):
    """Test user config."""
    # First get the form
    result = await opp.config_entries.flow.async_init(
        SRP_ENERGY_DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    # Fill submit form data for config entry
    with patch(
        "openpeerpower.components.srp_energy.config_flow.SrpEnergyClient"
    ), patch(
        "openpeerpower.components.srp_energy.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:

        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=ENTRY_CONFIG,
        )

        assert result["type"] == "create_entry"
        assert result["title"] == "Test"
        assert result["data"][CONF_IS_TOU] is False

    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth(opp):
    """Test user config with invalid auth."""
    result = await opp.config_entries.flow.async_init(
        SRP_ENERGY_DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.srp_energy.config_flow.SrpEnergyClient.validate",
        return_value=False,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=ENTRY_CONFIG,
        )

        assert result["errors"]["base"] == "invalid_auth"


async def test_form_value_error(opp):
    """Test user config that throws a value error."""
    result = await opp.config_entries.flow.async_init(
        SRP_ENERGY_DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.srp_energy.config_flow.SrpEnergyClient",
        side_effect=ValueError(),
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=ENTRY_CONFIG,
        )

        assert result["errors"]["base"] == "invalid_account"


async def test_form_unknown_exception(opp):
    """Test user config that throws an unknown exception."""
    result = await opp.config_entries.flow.async_init(
        SRP_ENERGY_DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.srp_energy.config_flow.SrpEnergyClient",
        side_effect=Exception(),
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=ENTRY_CONFIG,
        )

        assert result["errors"]["base"] == "unknown"


async def test_config(opp):
    """Test handling of configuration imported."""
    with patch("openpeerpower.components.srp_energy.config_flow.SrpEnergyClient"):
        result = await opp.config_entries.flow.async_init(
            SRP_ENERGY_DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=ENTRY_CONFIG,
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY


async def test_integration_already_configured(opp):
    """Test integration is already configured."""
    await init_integration(opp)
    result = await opp.config_entries.flow.async_init(
        SRP_ENERGY_DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "single_instance_allowed"
