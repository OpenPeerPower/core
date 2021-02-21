"""Tests for the local_ip config_flow."""
from openpeerpower import data_entry_flow
from openpeerpower.components.local_ip.const import DOMAIN
from openpeerpower.config_entries import SOURCE_USER

from tests.common import MockConfigEntry


async def test_config_flow.opp):
    """Test we can finish a config flow."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

    result = await.opp.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY

    await.opp.async_block_till_done()
    state = opp.states.get(f"sensor.{DOMAIN}")
    assert state


async def test_already_setup.opp):
    """Test we abort if already setup."""
    MockConfigEntry(
        domain=DOMAIN,
        data={},
    ).add_to_opp.opp)

    # Should fail, same NAME
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "single_instance_allowed"
