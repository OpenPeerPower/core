"""Test smarttub setup process."""

import asyncio
from unittest.mock import patch

from smarttub import LoginFailed

from openpeerpower.components import smarttub
from openpeerpower.components.smarttub.const import DOMAIN
from openpeerpower.config_entries import SOURCE_REAUTH, ConfigEntryState
from openpeerpower.setup import async_setup_component


async def test_setup_with_no_config(setup_component, opp, smarttub_api):
    """Test that we do not discover anything."""

    # No flows started
    assert len(opp.config_entries.flow.async_progress()) == 0

    smarttub_api.login.assert_not_called()


async def test_setup_entry_not_ready(setup_component, opp, config_entry, smarttub_api):
    """Test setup when the entry is not ready."""
    smarttub_api.login.side_effect = asyncio.TimeoutError

    config_entry.add_to_opp(opp)
    await opp.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_setup_auth_failed(setup_component, opp, config_entry, smarttub_api):
    """Test setup when the credentials are invalid."""
    smarttub_api.login.side_effect = LoginFailed

    config_entry.add_to_opp(opp)
    with patch.object(opp.config_entries.flow, "async_init") as mock_flow_init:
        await opp.config_entries.async_setup(config_entry.entry_id)
        assert config_entry.state is ConfigEntryState.SETUP_ERROR
        mock_flow_init.assert_called_with(
            DOMAIN,
            context={
                "source": SOURCE_REAUTH,
                "entry_id": config_entry.entry_id,
                "unique_id": config_entry.unique_id,
            },
            data=config_entry.data,
        )


async def test_config_passed_to_config_entry(opp, config_entry, config_data):
    """Test that configured options are loaded via config entry."""
    config_entry.add_to_opp(opp)
    assert await async_setup_component(opp, smarttub.DOMAIN, config_data)


async def test_unload_entry(opp, config_entry):
    """Test being able to unload an entry."""
    config_entry.add_to_opp(opp)

    assert await async_setup_component(opp, smarttub.DOMAIN, {}) is True

    assert await opp.config_entries.async_unload(config_entry.entry_id)
