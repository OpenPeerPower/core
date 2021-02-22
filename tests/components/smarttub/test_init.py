"""Test smarttub setup process."""

import asyncio

from smarttub import LoginFailed

from openpeerpower.components import smarttub
from openpeerpower.config_entries import (
    ENTRY_STATE_SETUP_ERROR,
    ENTRY_STATE_SETUP_RETRY,
)
from openpeerpower.setup import async_setup_component


async def test_setup_with_no_config(setup_component,.opp, smarttub_api):
    """Test that we do not discover anything."""

    # No flows started
    assert len.opp.config_entries.flow.async_progress()) == 0

    smarttub_api.login.assert_not_called()


async def test_setup_entry_not_ready(setup_component,.opp, config_entry, smarttub_api):
    """Test setup when the entry is not ready."""
    smarttub_api.login.side_effect = asyncio.TimeoutError

    config_entry.add_to.opp.opp)
    await.opp.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state == ENTRY_STATE_SETUP_RETRY


async def test_setup_auth_failed(setup_component,.opp, config_entry, smarttub_api):
    """Test setup when the credentials are invalid."""
    smarttub_api.login.side_effect = LoginFailed

    config_entry.add_to.opp.opp)
    await.opp.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state == ENTRY_STATE_SETUP_ERROR


async def test_config_passed_to_config_entry.opp, config_entry, config_data):
    """Test that configured options are loaded via config entry."""
    config_entry.add_to.opp.opp)
    assert await async_setup_component.opp, smarttub.DOMAIN, config_data)


async def test_unload_entry.opp, config_entry):
    """Test being able to unload an entry."""
    config_entry.add_to.opp.opp)

    assert await async_setup_component.opp, smarttub.DOMAIN, {}) is True

    assert await.opp.config_entries.async_unload(config_entry.entry_id)
