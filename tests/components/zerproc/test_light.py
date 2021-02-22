"""Test the zerproc lights."""
from unittest.mock import MagicMock, patch

import pytest
import pyzerproc

from openpeerpower import setup
from openpeerpower.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_HS_COLOR,
    ATTR_RGB_COLOR,
    ATTR_XY_COLOR,
    SCAN_INTERVAL,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
)
from openpeerpower.components.zerproc.light import DOMAIN
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_ICON,
    ATTR_SUPPORTED_FEATURES,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
import openpeerpower.util.dt as dt_util

from tests.common import MockConfigEntry, async_fire_time_changed


@pytest.fixture
async def mock_entry.opp):
    """Create a mock light entity."""
    return MockConfigEntry(domain=DOMAIN)


@pytest.fixture
async def mock_light.opp, mock_entry):
    """Create a mock light entity."""
    await setup.async_setup_component.opp, "persistent_notification", {})

    mock_entry.add_to.opp.opp)

    light = MagicMock(spec=pyzerproc.Light)
    light.address = "AA:BB:CC:DD:EE:FF"
    light.name = "LEDBlue-CCDDEEFF"
    light.is_connected.return_value = False

    mock_state = pyzerproc.LightState(False, (0, 0, 0))

    with patch(
        "openpeerpower.components.zerproc.light.pyzerproc.discover",
        return_value=[light],
    ), patch.object(light, "connect"), patch.object(
        light, "get_state", return_value=mock_state
    ):
        await opp.config_entries.async_setup(mock_entry.entry_id)
        await opp.async_block_till_done()

    light.is_connected.return_value = True

    return light


async def test_init.opp, mock_entry):
    """Test platform setup."""
    await setup.async_setup_component.opp, "persistent_notification", {})

    mock_entry.add_to.opp.opp)

    mock_light_1 = MagicMock(spec=pyzerproc.Light)
    mock_light_1.address = "AA:BB:CC:DD:EE:FF"
    mock_light_1.name = "LEDBlue-CCDDEEFF"
    mock_light_1.is_connected.return_value = True

    mock_light_2 = MagicMock(spec=pyzerproc.Light)
    mock_light_2.address = "11:22:33:44:55:66"
    mock_light_2.name = "LEDBlue-33445566"
    mock_light_2.is_connected.return_value = True

    mock_state_1 = pyzerproc.LightState(False, (0, 0, 0))
    mock_state_2 = pyzerproc.LightState(True, (0, 80, 255))

    mock_light_1.get_state.return_value = mock_state_1
    mock_light_2.get_state.return_value = mock_state_2

    with patch(
        "openpeerpower.components.zerproc.light.pyzerproc.discover",
        return_value=[mock_light_1, mock_light_2],
    ):
        await opp.config_entries.async_setup(mock_entry.entry_id)
        await opp.async_block_till_done()

    state = opp.states.get("light.ledblue_ccddeeff")
    assert state.state == STATE_OFF
    assert state.attributes == {
        ATTR_FRIENDLY_NAME: "LEDBlue-CCDDEEFF",
        ATTR_SUPPORTED_FEATURES: SUPPORT_BRIGHTNESS | SUPPORT_COLOR,
        ATTR_ICON: "mdi:string-lights",
    }

    state = opp.states.get("light.ledblue_33445566")
    assert state.state == STATE_ON
    assert state.attributes == {
        ATTR_FRIENDLY_NAME: "LEDBlue-33445566",
        ATTR_SUPPORTED_FEATURES: SUPPORT_BRIGHTNESS | SUPPORT_COLOR,
        ATTR_ICON: "mdi:string-lights",
        ATTR_BRIGHTNESS: 255,
        ATTR_HS_COLOR: (221.176, 100.0),
        ATTR_RGB_COLOR: (0, 80, 255),
        ATTR_XY_COLOR: (0.138, 0.08),
    }

    with patch.object.opp.loop, "stop"):
        await opp.async_stop()

    assert mock_light_1.disconnect.called
    assert mock_light_2.disconnect.called


async def test_discovery_exception.opp, mock_entry):
    """Test platform setup."""
    await setup.async_setup_component.opp, "persistent_notification", {})

    mock_entry.add_to.opp.opp)

    with patch(
        "openpeerpower.components.zerproc.light.pyzerproc.discover",
        side_effect=pyzerproc.ZerprocException("TEST"),
    ):
        await opp.config_entries.async_setup(mock_entry.entry_id)
        await opp.async_block_till_done()

    # The exception should be captured and no entities should be added
    assert len.opp.data[DOMAIN]["addresses"]) == 0


async def test_connect_exception.opp, mock_entry):
    """Test platform setup."""
    await setup.async_setup_component.opp, "persistent_notification", {})

    mock_entry.add_to.opp.opp)

    mock_light_1 = MagicMock(spec=pyzerproc.Light)
    mock_light_1.address = "AA:BB:CC:DD:EE:FF"
    mock_light_1.name = "LEDBlue-CCDDEEFF"
    mock_light_1.is_connected.return_value = False

    mock_light_2 = MagicMock(spec=pyzerproc.Light)
    mock_light_2.address = "11:22:33:44:55:66"
    mock_light_2.name = "LEDBlue-33445566"
    mock_light_2.is_connected.return_value = False

    with patch(
        "openpeerpower.components.zerproc.light.pyzerproc.discover",
        return_value=[mock_light_1, mock_light_2],
    ), patch.object(
        mock_light_1, "connect", side_effect=pyzerproc.ZerprocException("TEST")
    ):
        await opp.config_entries.async_setup(mock_entry.entry_id)
        await opp.async_block_till_done()

    # The exception connecting to light 1 should be captured, but light 2
    # should still be added
    assert len.opp.data[DOMAIN]["addresses"]) == 1


async def test_remove_entry.opp, mock_light, mock_entry):
    """Test platform setup."""
    with patch.object(mock_light, "disconnect") as mock_disconnect:
        await opp.config_entries.async_remove(mock_entry.entry_id)

    assert mock_disconnect.called


async def test_remove_entry_exceptions_caught.opp, mock_light, mock_entry):
    """Assert that disconnect exceptions are caught."""
    with patch.object(
        mock_light, "disconnect", side_effect=pyzerproc.ZerprocException("Mock error")
    ) as mock_disconnect:
        await opp.config_entries.async_remove(mock_entry.entry_id)

    assert mock_disconnect.called


async def test_light_turn_on.opp, mock_light):
    """Test ZerprocLight turn_on."""
    utcnow = dt_util.utcnow()
    with patch.object(mock_light, "turn_on") as mock_turn_on:
        await opp.services.async_call(
            "light",
            "turn_on",
            {ATTR_ENTITY_ID: "light.ledblue_ccddeeff"},
            blocking=True,
        )
        await opp.async_block_till_done()
    mock_turn_on.assert_called()

    with patch.object(mock_light, "set_color") as mock_set_color:
        await opp.services.async_call(
            "light",
            "turn_on",
            {ATTR_ENTITY_ID: "light.ledblue_ccddeeff", ATTR_BRIGHTNESS: 25},
            blocking=True,
        )
        await opp.async_block_till_done()
    mock_set_color.assert_called_with(25, 25, 25)

    # Make sure no discovery calls are made while we emulate time passing
    with patch("openpeerpower.components.zerproc.light.pyzerproc.discover"):
        with patch.object(
            mock_light,
            "get_state",
            return_value=pyzerproc.LightState(True, (175, 150, 220)),
        ):
            utcnow = utcnow + SCAN_INTERVAL
            async_fire_time_changed.opp, utcnow)
            await opp.async_block_till_done()

        with patch.object(mock_light, "set_color") as mock_set_color:
            await opp.services.async_call(
                "light",
                "turn_on",
                {ATTR_ENTITY_ID: "light.ledblue_ccddeeff", ATTR_BRIGHTNESS: 25},
                blocking=True,
            )
            await opp.async_block_till_done()

        mock_set_color.assert_called_with(19, 17, 25)

        with patch.object(mock_light, "set_color") as mock_set_color:
            await opp.services.async_call(
                "light",
                "turn_on",
                {ATTR_ENTITY_ID: "light.ledblue_ccddeeff", ATTR_HS_COLOR: (50, 50)},
                blocking=True,
            )
            await opp.async_block_till_done()

        mock_set_color.assert_called_with(220, 201, 110)

        with patch.object(
            mock_light,
            "get_state",
            return_value=pyzerproc.LightState(True, (75, 75, 75)),
        ):
            utcnow = utcnow + SCAN_INTERVAL
            async_fire_time_changed.opp, utcnow)
            await opp.async_block_till_done()

        with patch.object(mock_light, "set_color") as mock_set_color:
            await opp.services.async_call(
                "light",
                "turn_on",
                {ATTR_ENTITY_ID: "light.ledblue_ccddeeff", ATTR_HS_COLOR: (50, 50)},
                blocking=True,
            )
            await opp.async_block_till_done()

        mock_set_color.assert_called_with(75, 68, 37)

        with patch.object(mock_light, "set_color") as mock_set_color:
            await opp.services.async_call(
                "light",
                "turn_on",
                {
                    ATTR_ENTITY_ID: "light.ledblue_ccddeeff",
                    ATTR_BRIGHTNESS: 200,
                    ATTR_HS_COLOR: (75, 75),
                },
                blocking=True,
            )
            await opp.async_block_till_done()

        mock_set_color.assert_called_with(162, 200, 50)


async def test_light_turn_off.opp, mock_light):
    """Test ZerprocLight turn_on."""
    with patch.object(mock_light, "turn_off") as mock_turn_off:
        await opp.services.async_call(
            "light",
            "turn_off",
            {ATTR_ENTITY_ID: "light.ledblue_ccddeeff"},
            blocking=True,
        )
        await opp.async_block_till_done()
    mock_turn_off.assert_called()


async def test_light_update.opp, mock_light):
    """Test ZerprocLight update."""
    utcnow = dt_util.utcnow()

    state = opp.states.get("light.ledblue_ccddeeff")
    assert state.state == STATE_OFF
    assert state.attributes == {
        ATTR_FRIENDLY_NAME: "LEDBlue-CCDDEEFF",
        ATTR_SUPPORTED_FEATURES: SUPPORT_BRIGHTNESS | SUPPORT_COLOR,
        ATTR_ICON: "mdi:string-lights",
    }

    # Make sure no discovery calls are made while we emulate time passing
    with patch("openpeerpower.components.zerproc.light.pyzerproc.discover"):
        # Test an exception during discovery
        with patch.object(
            mock_light, "get_state", side_effect=pyzerproc.ZerprocException("TEST")
        ):
            utcnow = utcnow + SCAN_INTERVAL
            async_fire_time_changed.opp, utcnow)
            await opp.async_block_till_done()

        state = opp.states.get("light.ledblue_ccddeeff")
        assert state.state == STATE_UNAVAILABLE
        assert state.attributes == {
            ATTR_FRIENDLY_NAME: "LEDBlue-CCDDEEFF",
            ATTR_SUPPORTED_FEATURES: SUPPORT_BRIGHTNESS | SUPPORT_COLOR,
            ATTR_ICON: "mdi:string-lights",
        }

        with patch.object(
            mock_light,
            "get_state",
            return_value=pyzerproc.LightState(False, (200, 128, 100)),
        ):
            utcnow = utcnow + SCAN_INTERVAL
            async_fire_time_changed.opp, utcnow)
            await opp.async_block_till_done()

        state = opp.states.get("light.ledblue_ccddeeff")
        assert state.state == STATE_OFF
        assert state.attributes == {
            ATTR_FRIENDLY_NAME: "LEDBlue-CCDDEEFF",
            ATTR_SUPPORTED_FEATURES: SUPPORT_BRIGHTNESS | SUPPORT_COLOR,
            ATTR_ICON: "mdi:string-lights",
        }

        with patch.object(
            mock_light,
            "get_state",
            return_value=pyzerproc.LightState(True, (175, 150, 220)),
        ):
            utcnow = utcnow + SCAN_INTERVAL
            async_fire_time_changed.opp, utcnow)
            await opp.async_block_till_done()

        state = opp.states.get("light.ledblue_ccddeeff")
        assert state.state == STATE_ON
        assert state.attributes == {
            ATTR_FRIENDLY_NAME: "LEDBlue-CCDDEEFF",
            ATTR_SUPPORTED_FEATURES: SUPPORT_BRIGHTNESS | SUPPORT_COLOR,
            ATTR_ICON: "mdi:string-lights",
            ATTR_BRIGHTNESS: 220,
            ATTR_HS_COLOR: (261.429, 31.818),
            ATTR_RGB_COLOR: (202, 173, 255),
            ATTR_XY_COLOR: (0.291, 0.232),
        }
