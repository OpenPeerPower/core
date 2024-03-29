"""Tests for the Abode light device."""
from unittest.mock import patch

from openpeerpower.components.abode import ATTR_DEVICE_ID
from openpeerpower.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_RGB_COLOR,
    DOMAIN as LIGHT_DOMAIN,
)
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_SUPPORTED_FEATURES,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_ON,
)
from openpeerpower.helpers import entity_registry as er

from .common import setup_platform

DEVICE_ID = "light.living_room_lamp"


async def test_entity_registry(opp):
    """Tests that the devices are registered in the entity registry."""
    await setup_platform(opp, LIGHT_DOMAIN)
    entity_registry = er.async_get(opp)

    entry = entity_registry.async_get(DEVICE_ID)
    assert entry.unique_id == "741385f4388b2637df4c6b398fe50581"


async def test_attributes(opp):
    """Test the light attributes are correct."""
    await setup_platform(opp, LIGHT_DOMAIN)

    state = opp.states.get(DEVICE_ID)
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_BRIGHTNESS) == 204
    assert state.attributes.get(ATTR_RGB_COLOR) == (0, 63, 255)
    assert state.attributes.get(ATTR_COLOR_TEMP) == 280
    assert state.attributes.get(ATTR_DEVICE_ID) == "ZB:db5b1a"
    assert not state.attributes.get("battery_low")
    assert not state.attributes.get("no_response")
    assert state.attributes.get("device_type") == "RGB Dimmer"
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "Living Room Lamp"
    assert state.attributes.get(ATTR_SUPPORTED_FEATURES) == 19


async def test_switch_off(opp):
    """Test the light can be turned off."""
    await setup_platform(opp, LIGHT_DOMAIN)

    with patch("abodepy.AbodeLight.switch_off") as mock_switch_off:
        assert await opp.services.async_call(
            LIGHT_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: DEVICE_ID}, blocking=True
        )
        await opp.async_block_till_done()
        mock_switch_off.assert_called_once()


async def test_switch_on(opp):
    """Test the light can be turned on."""
    await setup_platform(opp, LIGHT_DOMAIN)

    with patch("abodepy.AbodeLight.switch_on") as mock_switch_on:
        await opp.services.async_call(
            LIGHT_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: DEVICE_ID}, blocking=True
        )
        await opp.async_block_till_done()
        mock_switch_on.assert_called_once()


async def test_set_brightness(opp):
    """Test the brightness can be set."""
    await setup_platform(opp, LIGHT_DOMAIN)

    with patch("abodepy.AbodeLight.set_level") as mock_set_level:
        await opp.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: DEVICE_ID, "brightness": 100},
            blocking=True,
        )
        await opp.async_block_till_done()
        # Brightness is converted in abode.light.AbodeLight.turn_on
        mock_set_level.assert_called_once_with(39)


async def test_set_color(opp):
    """Test the color can be set."""
    await setup_platform(opp, LIGHT_DOMAIN)

    with patch("abodepy.AbodeLight.set_color") as mock_set_color:
        await opp.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: DEVICE_ID, "hs_color": [240, 100]},
            blocking=True,
        )
        await opp.async_block_till_done()
        mock_set_color.assert_called_once_with((240.0, 100.0))


async def test_set_color_temp(opp):
    """Test the color temp can be set."""
    await setup_platform(opp, LIGHT_DOMAIN)

    with patch("abodepy.AbodeLight.set_color_temp") as mock_set_color_temp:
        await opp.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: DEVICE_ID, "color_temp": 309},
            blocking=True,
        )
        await opp.async_block_till_done()
        # Color temp is converted in abode.light.AbodeLight.turn_on
        mock_set_color_temp.assert_called_once_with(3236)
