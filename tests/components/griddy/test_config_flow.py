"""Test the Griddy Power config flow."""
import asyncio
from unittest.mock import MagicMock, patch

from openpeerpower import config_entries, setup
from openpeerpower.components.griddy.const import DOMAIN


async def test_form(opp):
    """Test we get the form."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.griddy.config_flow.AsyncGriddy.async_getnow",
        return_value=MagicMock(),
    ), patch(
        "openpeerpower.components.griddy.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.griddy.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"loadzone": "LZ_HOUSTON"},
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "Load Zone LZ_HOUSTON"
    assert result2["data"] == {"loadzone": "LZ_HOUSTON"}
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_cannot_connect(opp):
    """Test we handle cannot connect error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.griddy.config_flow.AsyncGriddy.async_getnow",
        side_effect=asyncio.TimeoutError,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"loadzone": "LZ_NORTH"},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}
