"""Test the PoolSense config flow."""
from unittest.mock import patch

from openpeerpower import data_entry_flow
from openpeerpower.components.poolsense.const import DOMAIN
from openpeerpower.config_entries import SOURCE_USER
from openpeerpower.const import CONF_EMAIL, CONF_PASSWORD


async def test_show_form.opp):
    """Test that the form is served with no input."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == SOURCE_USER


async def test_invalid_credentials.opp):
    """Test we handle invalid credentials."""
    with patch(
        "poolsense.PoolSense.test_poolsense_credentials",
        return_value=False,
    ):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_EMAIL: "test-email", CONF_PASSWORD: "test-password"},
        )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "invalid_auth"}


async def test_valid_credentials.opp):
    """Test we handle invalid credentials."""
    with patch(
        "poolsense.PoolSense.test_poolsense_credentials", return_value=True
    ), patch(
        "openpeerpower.components.poolsense.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.poolsense.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_EMAIL: "test-email", CONF_PASSWORD: "test-password"},
        )
        await opp.async_block_till_done()

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "test-email"

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1
