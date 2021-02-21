"""Tests for the WiLight integration."""
from unittest.mock import patch

import pytest
import pywilight
from pywilight.const import DOMAIN

from openpeerpower.config_entries import (
    ENTRY_STATE_LOADED,
    ENTRY_STATE_NOT_LOADED,
    ENTRY_STATE_SETUP_RETRY,
)
from openpeerpowerr.helpers.typing import OpenPeerPowerType

from tests.components.wilight import (
    HOST,
    UPNP_MAC_ADDRESS,
    UPNP_MODEL_NAME_P_B,
    UPNP_MODEL_NUMBER,
    UPNP_SERIAL,
    setup_integration,
)


@pytest.fixture(name="dummy_device_from_host")
def mock_dummy_device_from_host():
    """Mock a valid api_devce."""

    device = pywilight.wilight_from_discovery(
        f"http://{HOST}:45995/wilight.xml",
        UPNP_MAC_ADDRESS,
        UPNP_MODEL_NAME_P_B,
        UPNP_SERIAL,
        UPNP_MODEL_NUMBER,
    )

    device.set_dummy(True)

    with patch(
        "pywilight.device_from_host",
        return_value=device,
    ):
        yield device


async def test_config_entry_not_ready.opp: OpenPeerPowerType) -> None:
    """Test the WiLight configuration entry not ready."""
    entry = await setup_integration.opp)

    assert entry.state == ENTRY_STATE_SETUP_RETRY


async def test_unload_config_entry(
   .opp: OpenPeerPowerType, dummy_device_from_host
) -> None:
    """Test the WiLight configuration entry unloading."""
    entry = await setup_integration.opp)

    assert entry.entry_id in.opp.data[DOMAIN]
    assert entry.state == ENTRY_STATE_LOADED

    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    if DOMAIN in.opp.data:
        assert entry.entry_id not in.opp.data[DOMAIN]
        assert entry.state == ENTRY_STATE_NOT_LOADED
