"""Tests for AVM Fritz!Box sensor component."""
from datetime import timedelta
from unittest.mock import Mock

from requests.exceptions import HTTPError

from openpeerpower.components.fritzbox.const import (
    ATTR_STATE_DEVICE_LOCKED,
    ATTR_STATE_LOCKED,
    DOMAIN as FB_DOMAIN,
)
from openpeerpower.components.sensor import DOMAIN
from openpeerpower.const import (
    ATTR_FRIENDLY_NAME,
    ATTR_UNIT_OF_MEASUREMENT,
    TEMP_CELSIUS,
)
from openpeerpower.helpers.typing import OpenPeerPowerType
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util

from . import MOCK_CONFIG, FritzDeviceSensorMock

from tests.common import async_fire_time_changed

ENTITY_ID = f"{DOMAIN}.fake_name"


async def setup_fritzbox.opp: OpenPeerPowerType, config: dict):
    """Set up mock AVM Fritz!Box."""
    assert await async_setup_component.opp, FB_DOMAIN, config)
    await.opp.async_block_till_done()


async def test_setup_opp: OpenPeerPowerType, fritz: Mock):
    """Test setup of platform."""
    device = FritzDeviceSensorMock()
    fritz().get_devices.return_value = [device]

    await setup_fritzbox.opp, MOCK_CONFIG)
    state =.opp.states.get(ENTITY_ID)

    assert state
    assert state.state == "1.23"
    assert state.attributes[ATTR_FRIENDLY_NAME] == "fake_name"
    assert state.attributes[ATTR_STATE_DEVICE_LOCKED] == "fake_locked_device"
    assert state.attributes[ATTR_STATE_LOCKED] == "fake_locked"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == TEMP_CELSIUS


async def test_update.opp: OpenPeerPowerType, fritz: Mock):
    """Test update with error."""
    device = FritzDeviceSensorMock()
    fritz().get_devices.return_value = [device]

    await setup_fritzbox.opp, MOCK_CONFIG)
    assert device.update.call_count == 0
    assert fritz().login.call_count == 1

    next_update = dt_util.utcnow() + timedelta(seconds=200)
    async_fire_time_changed.opp, next_update)
    await.opp.async_block_till_done()

    assert device.update.call_count == 1
    assert fritz().login.call_count == 1


async def test_update_error(opp: OpenPeerPowerType, fritz: Mock):
    """Test update with error."""
    device = FritzDeviceSensorMock()
    device.update.side_effect = HTTPError("Boom")
    fritz().get_devices.return_value = [device]

    await setup_fritzbox.opp, MOCK_CONFIG)
    assert device.update.call_count == 0
    assert fritz().login.call_count == 1

    next_update = dt_util.utcnow() + timedelta(seconds=200)
    async_fire_time_changed.opp, next_update)
    await.opp.async_block_till_done()

    assert device.update.call_count == 1
    assert fritz().login.call_count == 2
