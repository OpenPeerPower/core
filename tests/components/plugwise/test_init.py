"""Tests for the Plugwise Climate integration."""

import asyncio

from plugwise.exceptions import XMLDataMissingError

from openpeerpower.components.plugwise.const import DOMAIN
from openpeerpower.config_entries import (
    ENTRY_STATE_NOT_LOADED,
    ENTRY_STATE_SETUP_ERROR,
    ENTRY_STATE_SETUP_RETRY,
)

from tests.common import AsyncMock, MockConfigEntry
from tests.components.plugwise.common import async_init_integration


async def test_smile_unauthorized.opp, mock_smile_unauth):
    """Test failing unauthorization by Smile."""
    entry = await async_init_integration.opp, mock_smile_unauth)
    assert entry.state == ENTRY_STATE_SETUP_ERROR


async def test_smile_error.opp, mock_smile_error):
    """Test server error handling by Smile."""
    entry = await async_init_integration.opp, mock_smile_error)
    assert entry.state == ENTRY_STATE_SETUP_RETRY


async def test_smile_notconnect.opp, mock_smile_notconnect):
    """Connection failure error handling by Smile."""
    mock_smile_notconnect.connect.return_value = False
    entry = await async_init_integration.opp, mock_smile_notconnect)
    assert entry.state == ENTRY_STATE_SETUP_RETRY


async def test_smile_timeout.opp, mock_smile_notconnect):
    """Timeout error handling by Smile."""
    mock_smile_notconnect.connect.side_effect = asyncio.TimeoutError
    entry = await async_init_integration.opp, mock_smile_notconnect)
    assert entry.state == ENTRY_STATE_SETUP_RETRY


async def test_smile_adam_xmlerror.opp, mock_smile_adam):
    """Detect malformed XML by Smile in Adam environment."""
    mock_smile_adam.full_update_device.side_effect = XMLDataMissingError
    entry = await async_init_integration.opp, mock_smile_adam)
    assert entry.state == ENTRY_STATE_SETUP_RETRY


async def test_unload_entry.opp, mock_smile_adam):
    """Test being able to unload an entry."""
    entry = await async_init_integration.opp, mock_smile_adam)

    mock_smile_adam.async_reset = AsyncMock(return_value=True)
    await.opp.config_entries.async_unload(entry.entry_id)
    await.opp.async_block_till_done()
    assert entry.state == ENTRY_STATE_NOT_LOADED
    assert not.opp.data[DOMAIN]


async def test_async_setup_entry_fail.opp):
    """Test async_setup_entry."""
    entry = MockConfigEntry(domain=DOMAIN, data={})

    entry.add_to_opp.opp)
    await.opp.config_entries.async_setup(entry.entry_id)
    await.opp.async_block_till_done()
    assert entry.state == ENTRY_STATE_SETUP_ERROR
