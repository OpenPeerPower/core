"""Fixtures for sma tests."""
from unittest.mock import patch

import pytest

from openpeerpower import config_entries
from openpeerpower.components.sma.const import DOMAIN

from . import MOCK_CUSTOM_SETUP_DATA, MOCK_DEVICE

from tests.common import MockConfigEntry


@pytest.fixture
def mock_config_entry():
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=MOCK_DEVICE["name"],
        unique_id=MOCK_DEVICE["serial"],
        data=MOCK_CUSTOM_SETUP_DATA,
        source=config_entries.SOURCE_IMPORT,
    )


@pytest.fixture
async def init_integration(opp, mock_config_entry):
    """Create a fake SMA Config Entry."""
    mock_config_entry.add_to_opp(opp)

    with patch("pysma.SMA.read"):
        await opp.config_entries.async_setup(mock_config_entry.entry_id)
    await opp.async_block_till_done()
    return mock_config_entry
