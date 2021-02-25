"""The tests for the Canary component."""
from unittest.mock import patch

from requests import ConnectTimeout

from openpeerpower.components.camera.const import DOMAIN as CAMERA_DOMAIN
from openpeerpower.components.canary.const import CONF_FFMPEG_ARGUMENTS, DOMAIN
from openpeerpower.config_entries import (
    ENTRY_STATE_LOADED,
    ENTRY_STATE_NOT_LOADED,
    ENTRY_STATE_SETUP_RETRY,
)
from openpeerpower.const import CONF_PASSWORD, CONF_TIMEOUT, CONF_USERNAME
from openpeerpower.setup import async_setup_component

from . import YAML_CONFIG, init_integration


async def test_import_from_yaml(opp, canary) -> None:
    """Test import from YAML."""
    with patch(
        "openpeerpower.components.canary.async_setup_entry",
        return_value=True,
    ):
        assert await async_setup_component(opp, DOMAIN, {DOMAIN: YAML_CONFIG})
        await opp.async_block_till_done()

    entries = opp.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1

    assert entries[0].data[CONF_USERNAME] == "test-username"
    assert entries[0].data[CONF_PASSWORD] == "test-password"
    assert entries[0].data[CONF_TIMEOUT] == 5


async def test_import_from_yaml_ffmpeg(opp, canary) -> None:
    """Test import from YAML with ffmpeg arguments."""
    with patch(
        "openpeerpower.components.canary.async_setup_entry",
        return_value=True,
    ):
        assert await async_setup_component(
            opp,
            DOMAIN,
            {
                DOMAIN: YAML_CONFIG,
                CAMERA_DOMAIN: [{"platform": DOMAIN, CONF_FFMPEG_ARGUMENTS: "-v"}],
            },
        )
        await opp.async_block_till_done()

    entries = opp.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1

    assert entries[0].data[CONF_USERNAME] == "test-username"
    assert entries[0].data[CONF_PASSWORD] == "test-password"
    assert entries[0].data[CONF_TIMEOUT] == 5
    assert entries[0].data.get(CONF_FFMPEG_ARGUMENTS) == "-v"


async def test_unload_entry(opp, canary):
    """Test successful unload of entry."""
    entry = await init_integration.opp)

    assert entry
    assert len.opp.config_entries.async_entries(DOMAIN)) == 1
    assert entry.state == ENTRY_STATE_LOADED

    assert await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    assert entry.state == ENTRY_STATE_NOT_LOADED
    assert not.opp.data.get(DOMAIN)


async def test_async_setup_raises_entry_not_ready(opp, canary):
    """Test that it throws ConfigEntryNotReady when exception occurs during setup."""
    canary.side_effect = ConnectTimeout()

    entry = await init_integration.opp)
    assert entry
    assert entry.state == ENTRY_STATE_SETUP_RETRY
