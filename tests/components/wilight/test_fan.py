"""Tests for the WiLight integration."""
from unittest.mock import patch

import pytest
import pywilight

from openpeerpower.components.fan import (
    ATTR_DIRECTION,
    ATTR_PERCENTAGE,
    DIRECTION_FORWARD,
    DIRECTION_REVERSE,
    DOMAIN as FAN_DOMAIN,
    SERVICE_SET_DIRECTION,
    SERVICE_SET_PERCENTAGE,
)
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from openpeerpower.helpers.typing import OpenPeerPowerType

from . import (
    HOST,
    UPNP_MAC_ADDRESS,
    UPNP_MODEL_NAME_LIGHT_FAN,
    UPNP_MODEL_NUMBER,
    UPNP_SERIAL,
    WILIGHT_ID,
    setup_integration,
)


@pytest.fixture(name="dummy_device_from_host_light_fan")
def mock_dummy_device_from_host_light_fan():
    """Mock a valid api_devce."""

    device = pywilight.wilight_from_discovery(
        f"http://{HOST}:45995/wilight.xml",
        UPNP_MAC_ADDRESS,
        UPNP_MODEL_NAME_LIGHT_FAN,
        UPNP_SERIAL,
        UPNP_MODEL_NUMBER,
    )

    device.set_dummy(True)

    with patch(
        "pywilight.device_from_host",
        return_value=device,
    ):
        yield device


async def test_loading_light_fan(
    opp: OpenPeerPowerType,
    dummy_device_from_host_light_fan,
) -> None:
    """Test the WiLight configuration entry loading."""

    entry = await setup_integration.opp)
    assert entry
    assert entry.unique_id == WILIGHT_ID

    entity_registry = await.opp.helpers.entity_registry.async_get_registry()

    # First segment of the strip
    state = opp.states.get("fan.wl000000000099_2")
    assert state
    assert state.state == STATE_OFF

    entry = entity_registry.async_get("fan.wl000000000099_2")
    assert entry
    assert entry.unique_id == "WL000000000099_1"


async def test_on_off_fan_state(
    opp: OpenPeerPowerType, dummy_device_from_host_light_fan
) -> None:
    """Test the change of state of the fan switches."""
    await setup_integration.opp)

    # Turn on
    await.opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "fan.wl000000000099_2"},
        blocking=True,
    )

    await.opp.async_block_till_done()
    state = opp.states.get("fan.wl000000000099_2")
    assert state
    assert state.state == STATE_ON

    # Turn on with speed
    await.opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_PERCENTAGE: 30, ATTR_ENTITY_ID: "fan.wl000000000099_2"},
        blocking=True,
    )

    await.opp.async_block_till_done()
    state = opp.states.get("fan.wl000000000099_2")
    assert state
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_PERCENTAGE) == 33

    # Turn off
    await.opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "fan.wl000000000099_2"},
        blocking=True,
    )

    await.opp.async_block_till_done()
    state = opp.states.get("fan.wl000000000099_2")
    assert state
    assert state.state == STATE_OFF


async def test_speed_fan_state(
    opp: OpenPeerPowerType, dummy_device_from_host_light_fan
) -> None:
    """Test the change of speed of the fan switches."""
    await setup_integration.opp)

    # Set speed Low
    await.opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {ATTR_PERCENTAGE: 30, ATTR_ENTITY_ID: "fan.wl000000000099_2"},
        blocking=True,
    )

    await.opp.async_block_till_done()
    state = opp.states.get("fan.wl000000000099_2")
    assert state
    assert state.attributes.get(ATTR_PERCENTAGE) == 33

    # Set speed Medium
    await.opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {ATTR_PERCENTAGE: 50, ATTR_ENTITY_ID: "fan.wl000000000099_2"},
        blocking=True,
    )

    await.opp.async_block_till_done()
    state = opp.states.get("fan.wl000000000099_2")
    assert state
    assert state.attributes.get(ATTR_PERCENTAGE) == 66

    # Set speed High
    await.opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {ATTR_PERCENTAGE: 90, ATTR_ENTITY_ID: "fan.wl000000000099_2"},
        blocking=True,
    )

    await.opp.async_block_till_done()
    state = opp.states.get("fan.wl000000000099_2")
    assert state
    assert state.attributes.get(ATTR_PERCENTAGE) == 100


async def test_direction_fan_state(
    opp: OpenPeerPowerType, dummy_device_from_host_light_fan
) -> None:
    """Test the change of direction of the fan switches."""
    await setup_integration.opp)

    # Set direction Forward
    await.opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_DIRECTION,
        {ATTR_DIRECTION: DIRECTION_FORWARD, ATTR_ENTITY_ID: "fan.wl000000000099_2"},
        blocking=True,
    )

    await.opp.async_block_till_done()
    state = opp.states.get("fan.wl000000000099_2")
    assert state
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_DIRECTION) == DIRECTION_FORWARD

    # Set direction Reverse
    await.opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_DIRECTION,
        {ATTR_DIRECTION: DIRECTION_REVERSE, ATTR_ENTITY_ID: "fan.wl000000000099_2"},
        blocking=True,
    )

    await.opp.async_block_till_done()
    state = opp.states.get("fan.wl000000000099_2")
    assert state
    assert state.attributes.get(ATTR_DIRECTION) == DIRECTION_REVERSE
