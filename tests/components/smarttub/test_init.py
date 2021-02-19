"""Test smarttub setup process."""

import asyncio
from unittest.mock import patch

import pytest
from smarttub import LoginFailed

from openpeerpower.components import smarttub
from openpeerpowerr.exceptions import ConfigEntryNotReady
from openpeerpowerr.setup import async_setup_component


async def test_setup_with_no_config.opp):
    """Test that we do not discover anything."""
    assert await async_setup_component.opp, smarttub.DOMAIN, {}) is True

    # No flows started
    assert len.opp.config_entries.flow.async_progress()) == 0

    assert smarttub.const.SMARTTUB_CONTROLLER not in.opp.data[smarttub.DOMAIN]


async def test_setup_entry_not_ready.opp, config_entry, smarttub_api):
    """Test setup when the entry is not ready."""
    assert await async_setup_component.opp, smarttub.DOMAIN, {}) is True
    smarttub_api.login.side_effect = asyncio.TimeoutError

    with pytest.raises(ConfigEntryNotReady):
        await smarttub.async_setup_entry.opp, config_entry)


async def test_setup_auth_failed.opp, config_entry, smarttub_api):
    """Test setup when the credentials are invalid."""
    assert await async_setup_component.opp, smarttub.DOMAIN, {}) is True
    smarttub_api.login.side_effect = LoginFailed

    assert await smarttub.async_setup_entry.opp, config_entry) is False


async def test_config_passed_to_config_entry.opp, config_entry, config_data):
    """Test that configured options are loaded via config entry."""
    config_entry.add_to_opp.opp)
    ret = await async_setup_component.opp, smarttub.DOMAIN, config_data)
    assert ret is True


async def test_unload_entry.opp, config_entry, smarttub_api):
    """Test being able to unload an entry."""
    config_entry.add_to_opp.opp)

    assert await async_setup_component.opp, smarttub.DOMAIN, {}) is True

    assert await smarttub.async_unload_entry.opp, config_entry)

    # test failure of platform unload
    assert await async_setup_component.opp, smarttub.DOMAIN, {}) is True
    with patch.object.opp.config_entries, "async_forward_entry_unload") as mock:
        mock.return_value = False
        assert await smarttub.async_unload_entry.opp, config_entry) is False
