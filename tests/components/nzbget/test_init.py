"""Test the NZBGet config flow."""
from unittest.mock import patch

from pynzbgetapi import NZBGetAPIException

from openpeerpower.components.nzbget.const import DOMAIN
from openpeerpower.config_entries import (
    ENTRY_STATE_LOADED,
    ENTRY_STATE_NOT_LOADED,
    ENTRY_STATE_SETUP_RETRY,
)
from openpeerpower.const import CONF_HOST, CONF_NAME, CONF_PORT
from openpeerpower.setup import async_setup_component

from . import (
    ENTRY_CONFIG,
    YAML_CONFIG,
    _patch_async_setup_entry,
    _patch_history,
    _patch_status,
    _patch_version,
    init_integration,
)

from tests.common import MockConfigEntry


async def test_import_from_yaml.opp) -> None:
    """Test import from YAML."""
    with _patch_version(), _patch_status(), _patch_history(), _patch_async_setup_entry():
        assert await async_setup_component(opp, DOMAIN, {DOMAIN: YAML_CONFIG})
        await opp.async_block_till_done()

    entries = opp.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1

    assert entries[0].data[CONF_NAME] == "GetNZBsTest"
    assert entries[0].data[CONF_HOST] == "10.10.10.30"
    assert entries[0].data[CONF_PORT] == 6789


async def test_unload_entry(opp, nzbget_api):
    """Test successful unload of entry."""
    entry = await init_integration.opp)

    assert len(opp.config_entries.async_entries(DOMAIN)) == 1
    assert entry.state == ENTRY_STATE_LOADED

    assert await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    assert entry.state == ENTRY_STATE_NOT_LOADED
    assert not opp.data.get(DOMAIN)


async def test_async_setup_raises_entry_not_ready.opp):
    """Test that it throws ConfigEntryNotReady when exception occurs during setup."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_CONFIG)
    config_entry.add_to_opp(opp)

    with _patch_version(), patch(
        "openpeerpower.components.nzbget.coordinator.NZBGetAPI.status",
        side_effect=NZBGetAPIException(),
    ):
        await opp.config_entries.async_setup(config_entry.entry_id)

    assert config_entry.state == ENTRY_STATE_SETUP_RETRY
