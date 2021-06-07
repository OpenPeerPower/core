"""Tests for AVM Fritz!Box binary sensor component."""
from datetime import timedelta
from unittest import mock
from unittest.mock import Mock

from requests.exceptions import HTTPError

from openpeerpower.components.binary_sensor import DOMAIN
from openpeerpower.components.fritzbox.const import DOMAIN as FB_DOMAIN
from openpeerpower.const import (
    ATTR_DEVICE_CLASS,
    ATTR_FRIENDLY_NAME,
    CONF_DEVICES,
    STATE_OFF,
    STATE_ON,
)
from openpeerpower.core import OpenPeerPower
import openpeerpower.util.dt as dt_util

from . import MOCK_CONFIG, FritzDeviceBinarySensorMock, setup_config_entry

from tests.common import async_fire_time_changed

ENTITY_ID = f"{DOMAIN}.fake_name"


async def test_setup(opp: OpenPeerPower, fritz: Mock):
    """Test setup of platform."""
    device = FritzDeviceBinarySensorMock()
    assert await setup_config_entry(
        opp, MOCK_CONFIG[FB_DOMAIN][CONF_DEVICES][0], ENTITY_ID, device, fritz
    )

    state = opp.states.get(ENTITY_ID)
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_FRIENDLY_NAME] == "fake_name"
    assert state.attributes[ATTR_DEVICE_CLASS] == "window"


async def test_is_off(opp: OpenPeerPower, fritz: Mock):
    """Test state of platform."""
    device = FritzDeviceBinarySensorMock()
    device.present = False
    assert await setup_config_entry(
        opp, MOCK_CONFIG[FB_DOMAIN][CONF_DEVICES][0], ENTITY_ID, device, fritz
    )

    state = opp.states.get(ENTITY_ID)
    assert state
    assert state.state == STATE_OFF


async def test_update(opp: OpenPeerPower, fritz: Mock):
    """Test update without error."""
    device = FritzDeviceBinarySensorMock()
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
    device = FritzDeviceBinarySensorMock()
    device.update.side_effect = [mock.DEFAULT, HTTPError("Boom")]
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
