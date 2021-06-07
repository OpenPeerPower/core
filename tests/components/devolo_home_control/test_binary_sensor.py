"""Tests for the devolo Home Control binary sensors."""
from unittest.mock import patch

import pytest

from openpeerpower.components.binary_sensor import DOMAIN
from openpeerpower.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from openpeerpower.core import OpenPeerPower

from . import configure_integration
from .mocks import (
    DeviceMock,
    HomeControlMock,
    HomeControlMockBinarySensor,
    HomeControlMockDisabledBinarySensor,
    HomeControlMockRemoteControl,
)


@pytest.mark.usefixtures("mock_zeroconf")
async def test_binary_sensor(opp: OpenPeerPower):
    """Test setup and state change of a binary sensor device."""
    entry = configure_integration(opp)
    DeviceMock.available = True
    with patch(
        "openpeerpower.components.devolo_home_control.HomeControl",
        side_effect=[HomeControlMockBinarySensor, HomeControlMock],
    ):
        await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()

    state = opp.states.get(f"{DOMAIN}.test")
    assert state is not None
    assert state.state == STATE_OFF

    # Emulate websocket message: sensor turned on
    HomeControlMockBinarySensor.publisher.dispatch("Test", ("Test", True))
    await opp.async_block_till_done()
    assert opp.states.get(f"{DOMAIN}.test").state == STATE_ON

    # Emulate websocket message: device went offline
    DeviceMock.available = False
    HomeControlMockBinarySensor.publisher.dispatch("Test", ("Status", False, "status"))
    await opp.async_block_till_done()
    assert opp.states.get(f"{DOMAIN}.test").state == STATE_UNAVAILABLE


@pytest.mark.usefixtures("mock_zeroconf")
async def test_remote_control(opp: OpenPeerPower):
    """Test setup and state change of a remote control device."""
    entry = configure_integration(opp)
    DeviceMock.available = True
    with patch(
        "openpeerpower.components.devolo_home_control.HomeControl",
        side_effect=[HomeControlMockRemoteControl, HomeControlMock],
    ):
        await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()

    state = opp.states.get(f"{DOMAIN}.test")
    assert state is not None
    assert state.state == STATE_OFF

    # Emulate websocket message: button pressed
    HomeControlMockRemoteControl.publisher.dispatch("Test", ("Test", 1))
    await opp.async_block_till_done()
    assert opp.states.get(f"{DOMAIN}.test").state == STATE_ON

    # Emulate websocket message: button released
    HomeControlMockRemoteControl.publisher.dispatch("Test", ("Test", 0))
    await opp.async_block_till_done()
    assert opp.states.get(f"{DOMAIN}.test").state == STATE_OFF

    # Emulate websocket message: device went offline
    DeviceMock.available = False
    HomeControlMockRemoteControl.publisher.dispatch("Test", ("Status", False, "status"))
    await opp.async_block_till_done()
    assert opp.states.get(f"{DOMAIN}.test").state == STATE_UNAVAILABLE


@pytest.mark.usefixtures("mock_zeroconf")
async def test_disabled(opp: OpenPeerPower):
    """Test setup of a disabled device."""
    entry = configure_integration(opp)
    with patch(
        "openpeerpower.components.devolo_home_control.HomeControl",
        side_effect=[HomeControlMockDisabledBinarySensor, HomeControlMock],
    ):
        await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()

    assert opp.states.get(f"{DOMAIN}.devolo.WarningBinaryFI:Test") is None


@pytest.mark.usefixtures("mock_zeroconf")
async def test_remove_from_opp(opp: OpenPeerPower):
    """Test removing entity."""
    entry = configure_integration(opp)
    with patch(
        "openpeerpower.components.devolo_home_control.HomeControl",
        side_effect=[HomeControlMockBinarySensor, HomeControlMock],
    ):
        await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()

    state = opp.states.get(f"{DOMAIN}.test")
    assert state is not None
    await opp.config_entries.async_remove(entry.entry_id)
    await opp.async_block_till_done()

    assert len(opp.states.async_all()) == 0
    HomeControlMockBinarySensor.publisher.unregister.assert_called_once()
