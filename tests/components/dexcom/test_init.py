"""Test the Dexcom config flow."""
from unittest.mock import patch

from pydexcom import AccountError, SessionError

from openpeerpower.components.dexcom.const import DOMAIN
from openpeerpower.config_entries import ENTRY_STATE_LOADED, ENTRY_STATE_NOT_LOADED

from tests.common import MockConfigEntry
from tests.components.dexcom import CONFIG, init_integration


async def test_setup_entry_account_error(opp):
    """Test entry setup failed due to account error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test_username",
        unique_id="test_username",
        data=CONFIG,
        options=None,
    )
    with patch(
        "openpeerpower.components.dexcom.Dexcom",
        side_effect=AccountError,
    ):
        entry.add_to_opp(opp)
        result = await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()

    assert result is False


async def test_setup_entry_session_error(opp):
    """Test entry setup failed due to session error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test_username",
        unique_id="test_username",
        data=CONFIG,
        options=None,
    )
    with patch(
        "openpeerpower.components.dexcom.Dexcom",
        side_effect=SessionError,
    ):
        entry.add_to_opp(opp)
        result = await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()

    assert result is False


async def test_unload_entry(opp):
    """Test successful unload of entry."""
    entry = await init_integration(opp)

    assert len(opp.config_entries.async_entries(DOMAIN)) == 1
    assert entry.state == ENTRY_STATE_LOADED

    assert await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    assert entry.state == ENTRY_STATE_NOT_LOADED
    assert not opp.data.get(DOMAIN)
