"""NuHeat component tests."""
from unittest.mock import patch

from openpeerpower.components.nuheat.const import DOMAIN

from .mocks import MOCK_CONFIG_ENTRY, _get_mock_nuheat

from tests.common import MockConfigEntry

VALID_CONFIG = {
    "nuheat": {"username": "warm", "password": "feet", "devices": "thermostat123"}
}
INVALID_CONFIG = {"nuheat": {"username": "warm", "password": "feet"}}


async def test_init_success.opp):
    """Test that we can setup with valid config."""
    mock_nuheat = _get_mock_nuheat()

    with patch(
        "openpeerpower.components.nuheat.nuheat.NuHeat",
        return_value=mock_nuheat,
    ):
        config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ENTRY)
        config_entry.add_to.opp.opp)
        assert await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()
