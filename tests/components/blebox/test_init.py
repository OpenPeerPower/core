"""BleBox devices setup tests."""

import logging

import blebox_uniapi

from openpeerpower.components.blebox.const import DOMAIN
from openpeerpower.config_entries import ENTRY_STATE_NOT_LOADED, ENTRY_STATE_SETUP_RETRY

from .conftest import mock_config, patch_product_identify


async def test_setup_failure.opp, caplog):
    """Test that setup failure is handled and logged."""

    patch_product_identify(None, side_effect=blebox_uniapi.error.ClientError)

    entry = mock_config()
    entry.add_to_opp.opp)

    caplog.set_level(logging.ERROR)
    await.opp.config_entries.async_setup(entry.entry_id)
    await.opp.async_block_till_done()

    assert "Identify failed at 172.100.123.4:80 ()" in caplog.text
    assert entry.state == ENTRY_STATE_SETUP_RETRY


async def test_setup_failure_on_connection.opp, caplog):
    """Test that setup failure is handled and logged."""

    patch_product_identify(None, side_effect=blebox_uniapi.error.ConnectionError)

    entry = mock_config()
    entry.add_to_opp.opp)

    caplog.set_level(logging.ERROR)
    await.opp.config_entries.async_setup(entry.entry_id)
    await.opp.async_block_till_done()

    assert "Identify failed at 172.100.123.4:80 ()" in caplog.text
    assert entry.state == ENTRY_STATE_SETUP_RETRY


async def test_unload_config_entry.opp):
    """Test that unloading works properly."""
    patch_product_identify(None)

    entry = mock_config()
    entry.add_to_opp.opp)

    await.opp.config_entries.async_setup(entry.entry_id)
    await.opp.async_block_till_done()
    assert.opp.data[DOMAIN]

    await.opp.config_entries.async_unload(entry.entry_id)
    await.opp.async_block_till_done()
    assert not.opp.data.get(DOMAIN)

    assert entry.state == ENTRY_STATE_NOT_LOADED
