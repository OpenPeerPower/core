"""Test the Advantage Air config flow."""

from unittest.mock import patch

from openpeerpower import config_entries, data_entry_flow
from openpeerpower.components.advantage_air.const import DOMAIN

from tests.components.advantage_air import TEST_SYSTEM_DATA, TEST_SYSTEM_URL, USER_INPUT


async def test_form.opp, aioclient_mock):
    """Test that form shows up."""

    aioclient_mock.get(
        TEST_SYSTEM_URL,
        text=TEST_SYSTEM_DATA,
    )

    result1 = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result1["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result1["step_id"] == "user"
    assert result1["errors"] == {}

    with patch(
        "openpeerpower.components.advantage_air.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await.opp.config_entries.flow.async_configure(
            result1["flow_id"],
            USER_INPUT,
        )

    assert len(aioclient_mock.mock_calls) == 1
    assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result2["title"] == "testname"
    assert result2["data"] == USER_INPUT
    await.opp.async_block_till_done()
    assert len(mock_setup_entry.mock_calls) == 1

    # Test Duplicate Config Flow
    result3 = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result4 = await.opp.config_entries.flow.async_configure(
        result3["flow_id"],
        USER_INPUT,
    )
    assert result4["type"] == data_entry_flow.RESULT_TYPE_ABORT


async def test_form_cannot_connect.opp, aioclient_mock):
    """Test we handle cannot connect error."""

    aioclient_mock.get(
        TEST_SYSTEM_URL,
        exc=SyntaxError,
    )

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await.opp.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": "cannot_connect"}
    assert len(aioclient_mock.mock_calls) == 1
