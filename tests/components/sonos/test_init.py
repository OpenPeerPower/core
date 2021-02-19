"""Tests for the Sonos config flow."""
from unittest.mock import patch

from openpeerpower import config_entries, data_entry_flow
from openpeerpower.components import sonos
from openpeerpowerr.setup import async_setup_component

from tests.common import mock_coro


async def test_creating_entry_sets_up_media_player.opp):
    """Test setting up Sonos loads the media player."""
    with patch(
        "openpeerpower.components.sonos.media_player.async_setup_entry",
        return_value=mock_coro(True),
    ) as mock_setup, patch("pysonos.discover", return_value=True):
        result = await.opp.config_entries.flow.async_init(
            sonos.DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        # Confirmation form
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

        result = await.opp.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY

        await.opp.async_block_till_done()

    assert len(mock_setup.mock_calls) == 1


async def test_configuring_sonos_creates_entry.opp):
    """Test that specifying config will create an entry."""
    with patch(
        "openpeerpower.components.sonos.async_setup_entry", return_value=mock_coro(True)
    ) as mock_setup, patch("pysonos.discover", return_value=True):
        await async_setup_component(
           .opp,
            sonos.DOMAIN,
            {"sonos": {"media_player": {"interface_addr": "127.0.0.1"}}},
        )
        await.opp.async_block_till_done()

    assert len(mock_setup.mock_calls) == 1


async def test_not_configuring_sonos_not_creates_entry.opp):
    """Test that no config will not create an entry."""
    with patch(
        "openpeerpower.components.sonos.async_setup_entry", return_value=mock_coro(True)
    ) as mock_setup, patch("pysonos.discover", return_value=True):
        await async_setup_component.opp, sonos.DOMAIN, {})
        await.opp.async_block_till_done()

    assert len(mock_setup.mock_calls) == 0
