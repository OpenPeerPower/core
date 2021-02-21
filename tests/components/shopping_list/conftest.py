"""Shopping list test helpers."""
from unittest.mock import patch

import pytest

from openpeerpower.components.shopping_list import intent as sl_intent

from tests.common import MockConfigEntry


@pytest.fixture(autouse=True)
def mock_shopping_list_io():
    """Stub out the persistence."""
    with patch("openpeerpower.components.shopping_list.ShoppingData.save"), patch(
        "openpeerpower.components.shopping_list.ShoppingData.async_load"
    ):
        yield


@pytest.fixture
async def sl_setup.opp):
    """Set up the shopping list."""

    entry = MockConfigEntry(domain="shopping_list")
    entry.add_to_opp.opp)

    assert await opp..config_entries.async_setup(entry.entry_id)

    await sl_intent.async_setup_intents.opp)
