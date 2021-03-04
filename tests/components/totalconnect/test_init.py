"""Tests for the TotalConnect init process."""
from unittest.mock import patch

from openpeerpower.components.totalconnect.const import DOMAIN
from openpeerpower.config_entries import ENTRY_STATE_SETUP_ERROR
from openpeerpower.setup import async_setup_component

from .common import CONFIG_DATA

from tests.common import MockConfigEntry


async def test_reauth_started(opp):
    """Test that reauth is started when we have login errors."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG_DATA,
    )
    mock_entry.add_to_opp(opp)

    with patch(
        "openpeerpower.components.totalconnect.TotalConnectClient.TotalConnectClient",
        autospec=True,
    ) as mock_client:
        mock_client.return_value.is_valid_credentials.return_value = False
        assert await async_setup_component(opp, DOMAIN, {})
        await opp.async_block_till_done()

    assert mock_entry.state == ENTRY_STATE_SETUP_ERROR
