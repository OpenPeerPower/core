"""Test SMHI component setup process."""
from unittest.mock import Mock

from openpeerpower.components import smhi

from .common import AsyncMock

TEST_CONFIG = {
    "config": {
        "name": "0123456789ABCDEF",
        "longitude": "62.0022",
        "latitude": "17.0022",
    }
}


async def test_setup_always_return_true() -> None:
    """Test async_setup always returns True."""
    opp = Mock()
    # Returns true with empty config
    assert await smhi.async_setup(opp, {}) is True

    # Returns true with a config provided
    assert await smhi.async_setup(opp, TEST_CONFIG) is True


async def test_forward_async_setup_entry() -> None:
    """Test that it will forward setup entry."""
    opp = Mock()

    assert await smhi.async_setup_entry(opp, {}) is True
    assert len(opp.config_entries.async_forward_entry_setup.mock_calls) == 1


async def test_forward_async_unload_entry() -> None:
    """Test that it will forward unload entry."""
    opp = AsyncMock()
    assert await smhi.async_unload_entry(opp, {}) is True
    assert len(opp.config_entries.async_forward_entry_unload.mock_calls) == 1
