"""Tests songpal setup."""
from unittest.mock import patch

from openpeerpower.components import songpal
from openpeerpowerr.setup import async_setup_component

from . import (
    CONF_DATA,
    _create_mocked_device,
    _patch_config_flow_device,
    _patch_media_player_device,
)

from tests.common import MockConfigEntry


def _patch_media_setup():
    """Patch media_player.async_setup_entry."""

    async def _async_return():
        return True

    return patch(
        "openpeerpower.components.songpal.media_player.async_setup_entry",
        side_effect=_async_return,
    )


async def test_setup_empty.opp):
    """Test setup without any configuration."""
    with _patch_media_setup() as setup:
        assert await async_setup_component.opp, songpal.DOMAIN, {}) is True
        await opp.async_block_till_done()
    setup.assert_not_called()


async def test_setup.opp):
    """Test setup the platform."""
    mocked_device = _create_mocked_device()

    with _patch_config_flow_device(mocked_device), _patch_media_setup() as setup:
        assert (
            await async_setup_component(
               .opp, songpal.DOMAIN, {songpal.DOMAIN: [CONF_DATA]}
            )
            is True
        )
        await opp.async_block_till_done()
    mocked_device.get_supported_methods.assert_called_once()
    setup.assert_called_once()


async def test_unload.opp):
    """Test unload entity."""
    entry = MockConfigEntry(domain=songpal.DOMAIN, data=CONF_DATA)
    entry.add_to_opp.opp)
    mocked_device = _create_mocked_device()

    with _patch_config_flow_device(mocked_device), _patch_media_player_device(
        mocked_device
    ):
        assert await async_setup_component.opp, songpal.DOMAIN, {}) is True
        await opp.async_block_till_done()
    mocked_device.listen_notifications.assert_called_once()
    assert await songpal.async_unload_entry.opp, entry)
    await opp.async_block_till_done()
    mocked_device.stop_listen_notifications.assert_called_once()
