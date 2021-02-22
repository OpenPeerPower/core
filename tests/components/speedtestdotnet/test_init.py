"""Tests for SpeedTest integration."""
from unittest.mock import patch

import speedtest

from openpeerpower import config_entries
from openpeerpower.components import speedtestdotnet
from openpeerpower.setup import async_setup_component

from tests.common import MockConfigEntry


async def test_setup_with_config.opp):
    """Test that we import the config and setup the integration."""
    config = {
        speedtestdotnet.DOMAIN: {
            speedtestdotnet.CONF_SERVER_ID: "1",
            speedtestdotnet.CONF_MANUAL: True,
            speedtestdotnet.CONF_SCAN_INTERVAL: "00:01:00",
        }
    }
    with patch("speedtest.Speedtest"):
        assert await async_setup_component.opp, speedtestdotnet.DOMAIN, config)


async def test_successful_config_entry.opp):
    """Test that SpeedTestDotNet is configured successfully."""

    entry = MockConfigEntry(
        domain=speedtestdotnet.DOMAIN,
        data={},
    )
    entry.add_to.opp.opp)

    with patch("speedtest.Speedtest"), patch(
        "openpeerpower.config_entries.ConfigEntries.async_forward_entry_setup",
        return_value=True,
    ) as forward_entry_setup:
        await.opp.config_entries.async_setup(entry.entry_id)

    assert entry.state == config_entries.ENTRY_STATE_LOADED
    assert forward_entry_setup.mock_calls[0][1] == (
        entry,
        "sensor",
    )


async def test_setup_failed.opp):
    """Test SpeedTestDotNet failed due to an error."""

    entry = MockConfigEntry(
        domain=speedtestdotnet.DOMAIN,
        data={},
    )
    entry.add_to.opp.opp)

    with patch("speedtest.Speedtest", side_effect=speedtest.ConfigRetrievalError):

        await.opp.config_entries.async_setup(entry.entry_id)

    assert entry.state == config_entries.ENTRY_STATE_SETUP_RETRY


async def test_unload_entry.opp):
    """Test removing SpeedTestDotNet."""
    entry = MockConfigEntry(
        domain=speedtestdotnet.DOMAIN,
        data={},
    )
    entry.add_to.opp.opp)

    with patch("speedtest.Speedtest"):
        await.opp.config_entries.async_setup(entry.entry_id)

    assert await.opp.config_entries.async_unload(entry.entry_id)
    await.opp.async_block_till_done()

    assert entry.state == config_entries.ENTRY_STATE_NOT_LOADED
    assert speedtestdotnet.DOMAIN not in.opp.data
