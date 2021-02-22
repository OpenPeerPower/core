"""Tests for the init module."""
import asyncio
from unittest.mock import Mock, patch

from pyheos import CommandFailedError, HeosError, const
import pytest

from openpeerpower.components.heos import (
    ControllerManager,
    async_setup_entry,
    async_unload_entry,
)
from openpeerpower.components.heos.const import (
    DATA_CONTROLLER_MANAGER,
    DATA_SOURCE_MANAGER,
    DOMAIN,
)
from openpeerpower.components.media_player.const import DOMAIN as MEDIA_PLAYER_DOMAIN
from openpeerpower.const import CONF_HOST
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.setup import async_setup_component


async def test_async_setup_creates_entry.opp, config):
    """Test component setup creates entry from config."""
    assert await async_setup_component.opp, DOMAIN, config)
    await opp.async_block_till_done()
    entries = opp.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    entry = entries[0]
    assert entry.title == "Controller (127.0.0.1)"
    assert entry.data == {CONF_HOST: "127.0.0.1"}
    assert entry.unique_id == DOMAIN


async def test_async_setup_updates_entry.opp, config_entry, config, controller):
    """Test component setup updates entry from config."""
    config[DOMAIN][CONF_HOST] = "127.0.0.2"
    config_entry.add_to.opp.opp)
    assert await async_setup_component.opp, DOMAIN, config)
    await opp.async_block_till_done()
    entries = opp.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    entry = entries[0]
    assert entry.title == "Controller (127.0.0.2)"
    assert entry.data == {CONF_HOST: "127.0.0.2"}
    assert entry.unique_id == DOMAIN


async def test_async_setup_returns_true.opp, config_entry, config):
    """Test component setup from config."""
    config_entry.add_to.opp.opp)
    assert await async_setup_component.opp, DOMAIN, config)
    await opp.async_block_till_done()
    entries = opp.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0] == config_entry


async def test_async_setup_no_config_returns_true.opp, config_entry):
    """Test component setup from entry only."""
    config_entry.add_to.opp.opp)
    assert await async_setup_component.opp, DOMAIN, {})
    await opp.async_block_till_done()
    entries = opp.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0] == config_entry


async def test_async_setup_entry_loads_platforms(
   .opp, config_entry, controller, input_sources, favorites
):
    """Test load connects to heos, retrieves players, and loads platforms."""
    config_entry.add_to.opp.opp)
    with patch.object.opp.config_entries, "async_forward_entry_setup") as forward_mock:
        assert await async_setup_entry.opp, config_entry)
        # Assert platforms loaded
        await opp.async_block_till_done()
        assert forward_mock.call_count == 1
        assert controller.connect.call_count == 1
        assert controller.get_players.call_count == 1
        assert controller.get_favorites.call_count == 1
        assert controller.get_input_sources.call_count == 1
        controller.disconnect.assert_not_called()
    assert.opp.data[DOMAIN][DATA_CONTROLLER_MANAGER].controller == controller
    assert.opp.data[DOMAIN][MEDIA_PLAYER_DOMAIN] == controller.players
    assert.opp.data[DOMAIN][DATA_SOURCE_MANAGER].favorites == favorites
    assert.opp.data[DOMAIN][DATA_SOURCE_MANAGER].inputs == input_sources


async def test_async_setup_entry_not_signed_in_loads_platforms(
   .opp, config_entry, controller, input_sources, caplog
):
    """Test setup does not retrieve favorites when not logged in."""
    config_entry.add_to.opp.opp)
    controller.is_signed_in = False
    controller.signed_in_username = None
    with patch.object.opp.config_entries, "async_forward_entry_setup") as forward_mock:
        assert await async_setup_entry.opp, config_entry)
        # Assert platforms loaded
        await opp.async_block_till_done()
        assert forward_mock.call_count == 1
        assert controller.connect.call_count == 1
        assert controller.get_players.call_count == 1
        assert controller.get_favorites.call_count == 0
        assert controller.get_input_sources.call_count == 1
        controller.disconnect.assert_not_called()
    assert.opp.data[DOMAIN][DATA_CONTROLLER_MANAGER].controller == controller
    assert.opp.data[DOMAIN][MEDIA_PLAYER_DOMAIN] == controller.players
    assert.opp.data[DOMAIN][DATA_SOURCE_MANAGER].favorites == {}
    assert.opp.data[DOMAIN][DATA_SOURCE_MANAGER].inputs == input_sources
    assert (
        "127.0.0.1 is not logged in to a HEOS account and will be unable to retrieve "
        "HEOS favorites: Use the 'heos.sign_in' service to sign-in to a HEOS account"
        in caplog.text
    )


async def test_async_setup_entry_connect_failure.opp, config_entry, controller):
    """Connection failure raises ConfigEntryNotReady."""
    config_entry.add_to.opp.opp)
    controller.connect.side_effect = HeosError()
    with pytest.raises(ConfigEntryNotReady):
        await async_setup_entry.opp, config_entry)
        await opp.async_block_till_done()
    assert controller.connect.call_count == 1
    assert controller.disconnect.call_count == 1
    controller.connect.reset_mock()
    controller.disconnect.reset_mock()


async def test_async_setup_entry_player_failure.opp, config_entry, controller):
    """Failure to retrieve players/sources raises ConfigEntryNotReady."""
    config_entry.add_to.opp.opp)
    controller.get_players.side_effect = HeosError()
    with pytest.raises(ConfigEntryNotReady):
        await async_setup_entry.opp, config_entry)
        await opp.async_block_till_done()
    assert controller.connect.call_count == 1
    assert controller.disconnect.call_count == 1
    controller.connect.reset_mock()
    controller.disconnect.reset_mock()


async def test_unload_entry.opp, config_entry, controller):
    """Test entries are unloaded correctly."""
    controller_manager = Mock(ControllerManager)
   .opp.data[DOMAIN] = {DATA_CONTROLLER_MANAGER: controller_manager}
    with patch.object(
       .opp.config_entries, "async_forward_entry_unload", return_value=True
    ) as unload:
        assert await async_unload_entry.opp, config_entry)
        await opp.async_block_till_done()
        assert controller_manager.disconnect.call_count == 1
        assert unload.call_count == 1
    assert DOMAIN not in.opp.data


async def test_update_sources_retry.opp, config_entry, config, controller, caplog):
    """Test update sources retries on failures to max attempts."""
    config_entry.add_to.opp.opp)
    assert await async_setup_component.opp, DOMAIN, config)
    controller.get_favorites.reset_mock()
    controller.get_input_sources.reset_mock()
    source_manager = opp.data[DOMAIN][DATA_SOURCE_MANAGER]
    source_manager.retry_delay = 0
    source_manager.max_retry_attempts = 1
    controller.get_favorites.side_effect = CommandFailedError("Test", "test", 0)
    controller.dispatcher.send(
        const.SIGNAL_CONTROLLER_EVENT, const.EVENT_SOURCES_CHANGED, {}
    )
    # Wait until it's finished
    while "Unable to update sources" not in caplog.text:
        await asyncio.sleep(0.1)
    assert controller.get_favorites.call_count == 2
