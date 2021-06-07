"""Tests for the devolo Home Control integration."""
from unittest.mock import patch

from devolo_home_control_api.exceptions.gateway import GatewayOfflineError
import pytest

from openpeerpower.config_entries import ConfigEntryState
from openpeerpower.core import OpenPeerPower

from tests.components.devolo_home_control import configure_integration


async def test_setup_entry(opp: OpenPeerPower):
    """Test setup entry."""
    entry = configure_integration(opp)
    with patch("openpeerpower.components.devolo_home_control.HomeControl"):
        await opp.config_entries.async_setup(entry.entry_id)
        assert entry.state is ConfigEntryState.LOADED


@pytest.mark.credentials_invalid
async def test_setup_entry_credentials_invalid(opp: OpenPeerPower):
    """Test setup entry fails if credentials are invalid."""
    entry = configure_integration(opp)
    await opp.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_ERROR


@pytest.mark.maintenance
async def test_setup_entry_maintenance(opp: OpenPeerPower):
    """Test setup entry fails if mydevolo is in maintenance mode."""
    entry = configure_integration(opp)
    await opp.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_setup_gateway_offline(opp: OpenPeerPower):
    """Test setup entry fails on gateway offline."""
    entry = configure_integration(opp)
    with patch(
        "openpeerpower.components.devolo_home_control.HomeControl",
        side_effect=GatewayOfflineError,
    ):
        await opp.config_entries.async_setup(entry.entry_id)
        assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_entry(opp: OpenPeerPower):
    """Test unload entry."""
    entry = configure_integration(opp)
    with patch("openpeerpower.components.devolo_home_control.HomeControl"):
        await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()
        await opp.config_entries.async_unload(entry.entry_id)
        assert entry.state is ConfigEntryState.NOT_LOADED
