"""Tests for the Gree Integration."""
from openpeerpower import config_entries, data_entry_flow
from openpeerpower.components.gree.const import DOMAIN as GREE_DOMAIN


async def test_creating_entry_sets_up_climate.opp, discovery, device, setup):
    """Test setting up Gree creates the climate components."""
    result = await.opp.config_entries.flow.async_init(
        GREE_DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Confirmation form
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

    result = await.opp.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY

    await opp.async_block_till_done()

    assert len(setup.mock_calls) == 1
