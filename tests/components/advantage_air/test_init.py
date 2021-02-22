"""Test the Advantage Air Initialization."""

from openpeerpower.config_entries import (
    ENTRY_STATE_LOADED,
    ENTRY_STATE_NOT_LOADED,
    ENTRY_STATE_SETUP_RETRY,
)

from tests.components.advantage_air import (
    TEST_SYSTEM_DATA,
    TEST_SYSTEM_URL,
    add_mock_config,
)


async def test_async_setup_entry.opp, aioclient_mock):
    """Test a successful setup entry and unload."""

    aioclient_mock.get(
        TEST_SYSTEM_URL,
        text=TEST_SYSTEM_DATA,
    )

    entry = await add_mock_config(opp)
    assert entry.state == ENTRY_STATE_LOADED

    assert await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()
    assert entry.state == ENTRY_STATE_NOT_LOADED


async def test_async_setup_entry_failure.opp, aioclient_mock):
    """Test a unsuccessful setup entry."""

    aioclient_mock.get(
        TEST_SYSTEM_URL,
        exc=SyntaxError,
    )

    entry = await add_mock_config(opp)
    assert entry.state == ENTRY_STATE_SETUP_RETRY
