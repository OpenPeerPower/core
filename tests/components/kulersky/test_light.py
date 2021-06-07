"""Test the Kuler Sky lights."""
from unittest.mock import MagicMock, patch

import pykulersky
import pytest

from openpeerpower import setup
from openpeerpower.components.kulersky.const import (
    DATA_ADDRESSES,
    DATA_DISCOVERY_SUBSCRIPTION,
    DOMAIN,
)
from openpeerpower.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_MODE,
    ATTR_HS_COLOR,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_SUPPORTED_COLOR_MODES,
    ATTR_WHITE_VALUE,
    ATTR_XY_COLOR,
    COLOR_MODE_HS,
    COLOR_MODE_RGBW,
    SCAN_INTERVAL,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    SUPPORT_WHITE_VALUE,
)
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_SUPPORTED_FEATURES,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
import openpeerpower.util.dt as dt_util

from tests.common import MockConfigEntry, async_fire_time_changed


@pytest.fixture
async def mock_entry(opp):
    """Create a mock light entity."""
    return MockConfigEntry(domain=DOMAIN)


@pytest.fixture
async def mock_light(opp, mock_entry):
    """Create a mock light entity."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    light = MagicMock(spec=pykulersky.Light)
    light.address = "AA:BB:CC:11:22:33"
    light.name = "Bedroom"
    light.connect.return_value = True
    light.get_color.return_value = (0, 0, 0, 0)
    with patch(
        "openpeerpower.components.kulersky.light.pykulersky.discover",
        return_value=[light],
    ):
        mock_entry.add_to_opp(opp)
        await opp.config_entries.async_setup(mock_entry.entry_id)
        await opp.async_block_till_done()

        assert light.connect.called

        yield light


async def test_init(opp, mock_light):
    """Test platform setup."""
    state = opp.states.get("light.bedroom")
    assert state.state == STATE_OFF
    assert state.attributes == {
        ATTR_FRIENDLY_NAME: "Bedroom",
        ATTR_SUPPORTED_COLOR_MODES: [COLOR_MODE_HS, COLOR_MODE_RGBW],
        ATTR_SUPPORTED_FEATURES: SUPPORT_BRIGHTNESS
        | SUPPORT_COLOR
        | SUPPORT_WHITE_VALUE,
    }

    with patch.object(opp.loop, "stop"):
        await opp.async_stop()
        await opp.async_block_till_done()

    assert mock_light.disconnect.called


async def test_remove_entry(opp, mock_light, mock_entry):
    """Test platform setup."""
    assert opp.data[DOMAIN][DATA_ADDRESSES] == {"AA:BB:CC:11:22:33"}
    assert DATA_DISCOVERY_SUBSCRIPTION in opp.data[DOMAIN]

    await opp.config_entries.async_remove(mock_entry.entry_id)

    assert mock_light.disconnect.called
    assert DOMAIN not in opp.data


async def test_remove_entry_exceptions_caught(opp, mock_light, mock_entry):
    """Assert that disconnect exceptions are caught."""
    mock_light.disconnect.side_effect = pykulersky.PykulerskyException("Mock error")
    await opp.config_entries.async_remove(mock_entry.entry_id)

    assert mock_light.disconnect.called


async def test_update_exception(opp, mock_light):
    """Test platform setup."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    mock_light.get_color.side_effect = pykulersky.PykulerskyException
    await opp.helpers.entity_component.async_update_entity("light.bedroom")
    state = opp.states.get("light.bedroom")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE


async def test_light_turn_on(opp, mock_light):
    """Test KulerSkyLight turn_on."""
    mock_light.get_color.return_value = (255, 255, 255, 255)
    await opp.services.async_call(
        "light",
        "turn_on",
        {ATTR_ENTITY_ID: "light.bedroom"},
        blocking=True,
    )
    await opp.async_block_till_done()
    mock_light.set_color.assert_called_with(255, 255, 255, 255)

    mock_light.get_color.return_value = (50, 50, 50, 255)
    await opp.services.async_call(
        "light",
        "turn_on",
        {ATTR_ENTITY_ID: "light.bedroom", ATTR_BRIGHTNESS: 50},
        blocking=True,
    )
    await opp.async_block_till_done()
    mock_light.set_color.assert_called_with(50, 50, 50, 255)

    mock_light.get_color.return_value = (50, 45, 25, 255)
    await opp.services.async_call(
        "light",
        "turn_on",
        {ATTR_ENTITY_ID: "light.bedroom", ATTR_HS_COLOR: (50, 50)},
        blocking=True,
    )
    await opp.async_block_till_done()

    mock_light.set_color.assert_called_with(50, 45, 25, 255)

    mock_light.get_color.return_value = (220, 201, 110, 180)
    await opp.services.async_call(
        "light",
        "turn_on",
        {ATTR_ENTITY_ID: "light.bedroom", ATTR_WHITE_VALUE: 180},
        blocking=True,
    )
    await opp.async_block_till_done()
    mock_light.set_color.assert_called_with(50, 45, 25, 180)


async def test_light_turn_off(opp, mock_light):
    """Test KulerSkyLight turn_on."""
    mock_light.get_color.return_value = (0, 0, 0, 0)
    await opp.services.async_call(
        "light",
        "turn_off",
        {ATTR_ENTITY_ID: "light.bedroom"},
        blocking=True,
    )
    await opp.async_block_till_done()
    mock_light.set_color.assert_called_with(0, 0, 0, 0)


async def test_light_update(opp, mock_light):
    """Test KulerSkyLight update."""
    utcnow = dt_util.utcnow()

    state = opp.states.get("light.bedroom")
    assert state.state == STATE_OFF
    assert state.attributes == {
        ATTR_FRIENDLY_NAME: "Bedroom",
        ATTR_SUPPORTED_COLOR_MODES: [COLOR_MODE_HS, COLOR_MODE_RGBW],
        ATTR_SUPPORTED_FEATURES: SUPPORT_BRIGHTNESS
        | SUPPORT_COLOR
        | SUPPORT_WHITE_VALUE,
    }

    # Test an exception during discovery
    mock_light.get_color.side_effect = pykulersky.PykulerskyException("TEST")
    utcnow = utcnow + SCAN_INTERVAL
    async_fire_time_changed(opp, utcnow)
    await opp.async_block_till_done()

    state = opp.states.get("light.bedroom")
    assert state.state == STATE_UNAVAILABLE
    assert state.attributes == {
        ATTR_FRIENDLY_NAME: "Bedroom",
        ATTR_SUPPORTED_COLOR_MODES: [COLOR_MODE_HS, COLOR_MODE_RGBW],
        ATTR_SUPPORTED_FEATURES: SUPPORT_BRIGHTNESS
        | SUPPORT_COLOR
        | SUPPORT_WHITE_VALUE,
    }

    mock_light.get_color.side_effect = None
    mock_light.get_color.return_value = (80, 160, 200, 240)
    utcnow = utcnow + SCAN_INTERVAL
    async_fire_time_changed(opp, utcnow)
    await opp.async_block_till_done()

    state = opp.states.get("light.bedroom")
    assert state.state == STATE_ON
    assert state.attributes == {
        ATTR_FRIENDLY_NAME: "Bedroom",
        ATTR_SUPPORTED_COLOR_MODES: [COLOR_MODE_HS, COLOR_MODE_RGBW],
        ATTR_SUPPORTED_FEATURES: SUPPORT_BRIGHTNESS
        | SUPPORT_COLOR
        | SUPPORT_WHITE_VALUE,
        ATTR_COLOR_MODE: COLOR_MODE_RGBW,
        ATTR_BRIGHTNESS: 200,
        ATTR_HS_COLOR: (200, 60),
        ATTR_RGB_COLOR: (102, 203, 255),
        ATTR_RGBW_COLOR: (102, 203, 255, 240),
        ATTR_WHITE_VALUE: 240,
        ATTR_XY_COLOR: (0.184, 0.261),
    }
