"""Tests for the EE BrightBox device scanner."""
from datetime import datetime
from unittest.mock import patch

from eebrightbox import EEBrightBoxException
import pytest

from openpeerpower.components.device_tracker import DOMAIN
from openpeerpower.const import CONF_PASSWORD, CONF_PLATFORM
from openpeerpower.setup import async_setup_component


def _configure_mock_get_devices(eebrightbox_mock):
    eebrightbox_instance = eebrightbox_mock.return_value
    eebrightbox_instance.__enter__.return_value = eebrightbox_instance
    eebrightbox_instance.get_devices.return_value = [
        {
            "mac": "AA:BB:CC:DD:EE:FF",
            "ip": "192.168.1.10",
            "hostname": "hostnameAA",
            "activity_ip": True,
            "port": "eth0",
            "time_last_active": datetime(2019, 1, 20, 16, 4, 0),
        },
        {
            "mac": "11:22:33:44:55:66",
            "hostname": "hostname11",
            "ip": "192.168.1.11",
            "activity_ip": True,
            "port": "wl0",
            "time_last_active": datetime(2019, 1, 20, 11, 9, 0),
        },
        {
            "mac": "FF:FF:FF:FF:FF:FF",
            "hostname": "hostnameFF",
            "ip": "192.168.1.12",
            "activity_ip": False,
            "port": "wl1",
            "time_last_active": datetime(2019, 1, 15, 16, 9, 0),
        },
    ]


def _configure_mock_failed_config_check(eebrightbox_mock):
    eebrightbox_instance = eebrightbox_mock.return_value
    eebrightbox_instance.__enter__.side_effect = EEBrightBoxException(
        "Failed to connect to the router"
    )


@pytest.fixture(autouse=True)
def mock_dev_track(mock_device_tracker_conf):
    """Mock device tracker config loading."""
    pass


@patch("openpeerpower.components.ee_brightbox.device_tracker.EEBrightBox")
async def test_missing_credentials(eebrightbox_mock, opp):
    """Test missing credentials."""
    _configure_mock_get_devices(eebrightbox_mock)

    result = await async_setup_component(
        opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "ee_brightbox"}}
    )

    assert result

    await opp.async_block_till_done()

    assert opp.states.get("device_tracker.hostnameaa") is None
    assert opp.states.get("device_tracker.hostname11") is None
    assert opp.states.get("device_tracker.hostnameff") is None


@patch("openpeerpower.components.ee_brightbox.device_tracker.EEBrightBox")
async def test_invalid_credentials(eebrightbox_mock, opp):
    """Test invalid credentials."""
    _configure_mock_failed_config_check(eebrightbox_mock)

    result = await async_setup_component(
        opp,
        DOMAIN,
        {DOMAIN: {CONF_PLATFORM: "ee_brightbox", CONF_PASSWORD: "test_password"}},
    )

    assert result

    await opp.async_block_till_done()

    assert opp.states.get("device_tracker.hostnameaa") is None
    assert opp.states.get("device_tracker.hostname11") is None
    assert opp.states.get("device_tracker.hostnameff") is None


@patch("openpeerpower.components.ee_brightbox.device_tracker.EEBrightBox")
async def test_get_devices(eebrightbox_mock, opp):
    """Test valid configuration."""
    _configure_mock_get_devices(eebrightbox_mock)

    result = await async_setup_component(
        opp,
        DOMAIN,
        {DOMAIN: {CONF_PLATFORM: "ee_brightbox", CONF_PASSWORD: "test_password"}},
    )

    assert result

    await opp.async_block_till_done()

    assert opp.states.get("device_tracker.hostnameaa") is not None
    assert opp.states.get("device_tracker.hostname11") is not None
    assert opp.states.get("device_tracker.hostnameff") is None

    state = opp.states.get("device_tracker.hostnameaa")
    assert state.attributes["mac"] == "AA:BB:CC:DD:EE:FF"
    assert state.attributes["ip"] == "192.168.1.10"
    assert state.attributes["port"] == "eth0"
    assert state.attributes["last_active"] == datetime(2019, 1, 20, 16, 4, 0)
