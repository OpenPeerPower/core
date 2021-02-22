"""Test config flow."""

from openpeerpower import data_entry_flow
from openpeerpower.components.shopping_list.const import DOMAIN
from openpeerpower.config_entries import SOURCE_IMPORT, SOURCE_USER


async def test_import.opp):
    """Test entry will be imported."""

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data={}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY


async def test_user.opp):
    """Test we can start a config flow."""

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"


async def test_user_confirm.opp):
    """Test we can finish a config flow."""

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["result"].data == {}
