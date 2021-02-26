"""Tests for the GogoGate2 component."""
from unittest.mock import MagicMock, patch

from gogogate2_api import GogoGate2Api
import pytest

from openpeerpower.components.gogogate2 import DEVICE_TYPE_GOGOGATE2, async_setup_entry
from openpeerpower.components.gogogate2.common import DeviceDataUpdateCoordinator
from openpeerpower.components.gogogate2.const import DEVICE_TYPE_ISMARTGATE, DOMAIN
from openpeerpower.config_entries import SOURCE_USER
from openpeerpower.const import (
    CONF_DEVICE,
    CONF_IP_ADDRESS,
    CONF_PASSWORD,
    CONF_USERNAME,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady

from tests.common import MockConfigEntry


@patch("openpeerpower.components.gogogate2.common.GogoGate2Api")
async def test_config_update(gogogate2api_mock, opp: OpenPeerPower) -> None:
    """Test config setup where the config is updated."""

    api = MagicMock(GogoGate2Api)
    api.async_info.side_effect = Exception("Error")
    gogogate2api_mock.return_value = api

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data={
            CONF_IP_ADDRESS: "127.0.0.1",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
        },
    )
    config_entry.add_to_opp(opp)

    assert not await opp.config_entries.async_setup(entry_id=config_entry.entry_id)
    await opp.async_block_till_done()
    assert config_entry.data == {
        CONF_DEVICE: DEVICE_TYPE_GOGOGATE2,
        CONF_IP_ADDRESS: "127.0.0.1",
        CONF_USERNAME: "admin",
        CONF_PASSWORD: "password",
    }


@patch("openpeerpower.components.gogogate2.common.ISmartGateApi")
async def test_config_no_update(ismartgateapi_mock, opp: OpenPeerPower) -> None:
    """Test config setup where the data is not updated."""
    api = MagicMock(GogoGate2Api)
    api.async_info.side_effect = Exception("Error")
    ismartgateapi_mock.return_value = api

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data={
            CONF_DEVICE: DEVICE_TYPE_ISMARTGATE,
            CONF_IP_ADDRESS: "127.0.0.1",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
        },
    )
    config_entry.add_to_opp(opp)

    assert not await opp.config_entries.async_setup(entry_id=config_entry.entry_id)
    await opp.async_block_till_done()
    assert config_entry.data == {
        CONF_DEVICE: DEVICE_TYPE_ISMARTGATE,
        CONF_IP_ADDRESS: "127.0.0.1",
        CONF_USERNAME: "admin",
        CONF_PASSWORD: "password",
    }


async def test_auth_fail(opp: OpenPeerPower) -> None:
    """Test authorization failures."""

    coordinator_mock: DeviceDataUpdateCoordinator = MagicMock(
        spec=DeviceDataUpdateCoordinator
    )
    coordinator_mock.last_update_success = False

    config_entry = MockConfigEntry()
    config_entry.add_to_opp(opp)

    with patch(
        "openpeerpower.components.gogogate2.get_data_update_coordinator",
        return_value=coordinator_mock,
    ), pytest.raises(ConfigEntryNotReady):
        await async_setup_entry(opp, config_entry)
