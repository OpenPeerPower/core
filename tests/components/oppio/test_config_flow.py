"""Test the Open Peer Power Supervisor config flow."""
from unittest.mock import patch

from openpeerpower import setup
from openpeerpower.components.oppio import DOMAIN


async def test_config_flow(opp):
    """Test we get the form."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    with patch(
        "openpeerpower.components.oppio.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.oppio.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "system"}
        )
        assert result["type"] == "create_entry"
        assert result["title"] == DOMAIN.title()
        assert result["data"] == {}
        await opp.async_block_till_done()

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_multiple_entries(opp):
    """Test creating multiple oppio entries."""
    await test_config_flow(opp)
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": "system"}
    )
    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
