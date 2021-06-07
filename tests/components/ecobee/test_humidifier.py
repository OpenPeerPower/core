"""The test for the ecobee thermostat humidifier module."""
from unittest.mock import patch

import pytest

from openpeerpower.components.ecobee.humidifier import MODE_MANUAL, MODE_OFF
from openpeerpower.components.humidifier import DOMAIN as HUMIDIFIER_DOMAIN
from openpeerpower.components.humidifier.const import (
    ATTR_AVAILABLE_MODES,
    ATTR_HUMIDITY,
    ATTR_MAX_HUMIDITY,
    ATTR_MIN_HUMIDITY,
    DEFAULT_MAX_HUMIDITY,
    DEFAULT_MIN_HUMIDITY,
    DEVICE_CLASS_HUMIDIFIER,
    MODE_AUTO,
    SERVICE_SET_HUMIDITY,
    SERVICE_SET_MODE,
    SUPPORT_MODES,
)
from openpeerpower.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_MODE,
    ATTR_SUPPORTED_FEATURES,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
)

from .common import setup_platform

DEVICE_ID = "humidifier.ecobee"


async def test_attributes(opp):
    """Test the humidifier attributes are correct."""
    await setup_platform(opp, HUMIDIFIER_DOMAIN)

    state = opp.states.get(DEVICE_ID)
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_MIN_HUMIDITY) == DEFAULT_MIN_HUMIDITY
    assert state.attributes.get(ATTR_MAX_HUMIDITY) == DEFAULT_MAX_HUMIDITY
    assert state.attributes.get(ATTR_HUMIDITY) == 40
    assert state.attributes.get(ATTR_AVAILABLE_MODES) == [
        MODE_OFF,
        MODE_AUTO,
        MODE_MANUAL,
    ]
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "ecobee"
    assert state.attributes.get(ATTR_DEVICE_CLASS) == DEVICE_CLASS_HUMIDIFIER
    assert state.attributes.get(ATTR_SUPPORTED_FEATURES) == SUPPORT_MODES


async def test_turn_on(opp):
    """Test the humidifer can be turned on."""
    with patch("pyecobee.Ecobee.set_humidifier_mode") as mock_turn_on:
        await setup_platform(opp, HUMIDIFIER_DOMAIN)

        await opp.services.async_call(
            HUMIDIFIER_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: DEVICE_ID},
            blocking=True,
        )
        await opp.async_block_till_done()
        mock_turn_on.assert_called_once_with(0, "manual")


async def test_turn_off(opp):
    """Test the humidifer can be turned off."""
    with patch("pyecobee.Ecobee.set_humidifier_mode") as mock_turn_off:
        await setup_platform(opp, HUMIDIFIER_DOMAIN)

        await opp.services.async_call(
            HUMIDIFIER_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: DEVICE_ID},
            blocking=True,
        )
        await opp.async_block_till_done()
        mock_turn_off.assert_called_once_with(0, STATE_OFF)


async def test_set_mode(opp):
    """Test the humidifer can change modes."""
    with patch("pyecobee.Ecobee.set_humidifier_mode") as mock_set_mode:
        await setup_platform(opp, HUMIDIFIER_DOMAIN)

        await opp.services.async_call(
            HUMIDIFIER_DOMAIN,
            SERVICE_SET_MODE,
            {ATTR_ENTITY_ID: DEVICE_ID, ATTR_MODE: MODE_AUTO},
            blocking=True,
        )
        await opp.async_block_till_done()
        mock_set_mode.assert_called_once_with(0, MODE_AUTO)

        await opp.services.async_call(
            HUMIDIFIER_DOMAIN,
            SERVICE_SET_MODE,
            {ATTR_ENTITY_ID: DEVICE_ID, ATTR_MODE: MODE_MANUAL},
            blocking=True,
        )
        await opp.async_block_till_done()
        mock_set_mode.assert_called_with(0, MODE_MANUAL)

        with pytest.raises(ValueError):
            await opp.services.async_call(
                HUMIDIFIER_DOMAIN,
                SERVICE_SET_MODE,
                {ATTR_ENTITY_ID: DEVICE_ID, ATTR_MODE: "ModeThatDoesntExist"},
                blocking=True,
            )


async def test_set_humidity(opp):
    """Test the humidifer can set humidity level."""
    with patch("pyecobee.Ecobee.set_humidity") as mock_set_humidity:
        await setup_platform(opp, HUMIDIFIER_DOMAIN)

        await opp.services.async_call(
            HUMIDIFIER_DOMAIN,
            SERVICE_SET_HUMIDITY,
            {ATTR_ENTITY_ID: DEVICE_ID, ATTR_HUMIDITY: 60},
            blocking=True,
        )
        await opp.async_block_till_done()
        mock_set_humidity.assert_called_once_with(0, 60)
