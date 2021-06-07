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
    CONF_DEVICES,
    PERCENTAGE,
    TEMP_CELSIUS,
)
from openpeerpower.core import OpenPeerPower
import openpeerpower.util.dt as dt_util

from . import MOCK_CONFIG, FritzDeviceSensorMock, setup_config_entry

from tests.common import async_fire_time_changed

ENTITY_ID = f"{DOMAIN}.fake_name"


async def test_setup(opp: OpenPeerPower, fritz: Mock):
    """Test setup of platform."""
    device = FritzDeviceSensorMock()
    assert await setup_config_entry(
        opp, MOCK_CONFIG[FB_DOMAIN][CONF_DEVICES][0], ENTITY_ID, device, fritz
    )

    state = opp.states.get(ENTITY_ID)
    assert state
    assert state.state == "1.23"
    assert state.attributes[ATTR_FRIENDLY_NAME] == "fake_name"
    assert state.attributes[ATTR_STATE_DEVICE_LOCKED] == "fake_locked_device"
    assert state.attributes[ATTR_STATE_LOCKED] == "fake_locked"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == TEMP_CELSIUS

    state = opp.states.get(f"{ENTITY_ID}_battery")
    assert state
    assert state.state == "23"
    assert state.attributes[ATTR_FRIENDLY_NAME] == "fake_name Battery"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == PERCENTAGE


async def test_update(opp: OpenPeerPower, fritz: Mock):
    """Test update without error."""
    device = FritzDeviceSensorMock()
    assert await setup_config_entry(
        opp, MOCK_CONFIG[FB_DOMAIN][CONF_DEVICES][0], ENTITY_ID, device, fritz
    )
    assert device.update.call_count == 1
    assert fritz().login.call_count == 1

    next_update = dt_util.utcnow() + timedelta(seconds=200)
    async_fire_time_changed(opp, next_update)
    await opp.async_block_till_done()

    assert device.update.call_count == 2
    assert fritz().login.call_count == 1


async def test_update_error(opp: OpenPeerPower, fritz: Mock):
    """Test update with error."""
    device = FritzDeviceSensorMock()
    device.update.side_effect = HTTPError("Boom")
    assert not await setup_config_entry(
        opp, MOCK_CONFIG[FB_DOMAIN][CONF_DEVICES][0], ENTITY_ID, device, fritz
    )
    assert device.update.call_count == 1
    assert fritz().login.call_count == 1

    next_update = dt_util.utcnow() + timedelta(seconds=200)
    async_fire_time_changed(opp, next_update)
    await opp.async_block_till_done()

    assert device.update.call_count == 2
    assert fritz().login.call_count == 2
