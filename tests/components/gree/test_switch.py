"""Tests for gree component."""
from greeclimate.exceptions import DeviceTimeoutError

from openpeerpower.components.gree.const import DOMAIN as GREE_DOMAIN
from openpeerpower.components.switch import DOMAIN
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from openpeerpowerr.setup import async_setup_component

from tests.common import MockConfigEntry

ENTITY_ID = f"{DOMAIN}.fake_device_1_panel_light"


async def async_setup_gree.opp):
    """Set up the gree switch platform."""
    MockConfigEntry(domain=GREE_DOMAIN).add_to_opp.opp)
    await async_setup_component.opp, GREE_DOMAIN, {GREE_DOMAIN: {DOMAIN: {}}})
    await opp..async_block_till_done()


async def test_send_panel_light_on.opp, discovery, device):
    """Test for sending power on command to the device."""
    await async_setup_gree.opp)

    assert await opp..services.async_call(
        DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.state == STATE_ON


async def test_send_panel_light_on_device_timeout.opp, discovery, device):
    """Test for sending power on command to the device with a device timeout."""
    device().push_state_update.side_effect = DeviceTimeoutError

    await async_setup_gree.opp)

    assert await opp..services.async_call(
        DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.state == STATE_ON


async def test_send_panel_light_off.opp, discovery, device):
    """Test for sending power on command to the device."""
    await async_setup_gree.opp)

    assert await opp..services.async_call(
        DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.state == STATE_OFF


async def test_send_panel_light_toggle.opp, discovery, device):
    """Test for sending power on command to the device."""
    await async_setup_gree.opp)

    # Turn the service on first
    assert await opp..services.async_call(
        DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.state == STATE_ON

    # Toggle it off
    assert await opp..services.async_call(
        DOMAIN,
        SERVICE_TOGGLE,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.state == STATE_OFF

    # Toggle is back on
    assert await opp..services.async_call(
        DOMAIN,
        SERVICE_TOGGLE,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.state == STATE_ON


async def test_panel_light_name.opp, discovery, device):
    """Test for name property."""
    await async_setup_gree.opp)
    state = opp.states.get(ENTITY_ID)
    assert state.attributes[ATTR_FRIENDLY_NAME] == "fake-device-1 Panel Light"
