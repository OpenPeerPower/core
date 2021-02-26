"""Test the Kuler Sky lights."""
import asyncio
from unittest.mock import MagicMock, patch

import pykulersky
import pytest

from openpeerpower import setup
from openpeerpower.components.kulersky.light import DOMAIN
from openpeerpower.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_HS_COLOR,
    ATTR_RGB_COLOR,
    ATTR_WHITE_VALUE,
    ATTR_XY_COLOR,
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
async def mock_entry.opp):
    """Create a mock light entity."""
    return MockConfigEntry(domain=DOMAIN)


@pytest.fixture
async def mock_light(opp, mock_entry):
    """Create a mock light entity."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    light = MagicMock(spec=pykulersky.Light)
    light.address = "AA:BB:CC:11:22:33"
    light.name = "Bedroom"
    light.connected = False
    with patch(
        "openpeerpower.components.kulersky.light.pykulersky.discover_bluetooth_devices",
        return_value=[
            {
                "address": "AA:BB:CC:11:22:33",
                "name": "Bedroom",
            }
        ],
    ):
        with patch(
            "openpeerpower.components.kulersky.light.pykulersky.Light",
            return_value=light,
        ), patch.object(light, "connect") as mock_connect, patch.object(
            light, "get_color", return_value=(0, 0, 0, 0)
        ):
            mock_entry.add_to_opp(opp)
            await opp.config_entries.async_setup(mock_entry.entry_id)
            await opp.async_block_till_done()

        assert mock_connect.called
        light.connected = True

        yield light


async def test_init(opp, mock_light):
    """Test platform setup."""
    state = opp.states.get("light.bedroom")
    assert state.state == STATE_OFF
    assert state.attributes == {
        ATTR_FRIENDLY_NAME: "Bedroom",
        ATTR_SUPPORTED_FEATURES: SUPPORT_BRIGHTNESS
        | SUPPORT_COLOR
        | SUPPORT_WHITE_VALUE,
    }

    with patch.object(opp.loop, "stop"), patch.object(
        mock_light, "disconnect"
    ) as mock_disconnect:
        await opp.async_stop()
        await opp.async_block_till_done()

    assert mock_disconnect.called


async def test_discovery_lock(opp, mock_entry):
    """Test discovery lock."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    discovery_finished = None
    first_discovery_started = asyncio.Event()

    async def mock_discovery(*args):
        """Block to simulate multiple discovery calls while one still running."""
        nonlocal discovery_finished
        if discovery_finished:
            first_discovery_started.set()
            await discovery_finished.wait()
        return []

    with patch(
        "openpeerpower.components.kulersky.light.pykulersky.discover_bluetooth_devices",
        return_value=[],
    ), patch(
        "openpeerpower.components.kulersky.light.async_track_time_interval",
    ) as mock_track_time_interval:
        mock_entry.add_to_opp(opp)
        await opp.config_entries.async_setup(mock_entry.entry_id)
        await opp.async_block_till_done()

        with patch.object(
            opp. "async_add_executor_job", side_effect=mock_discovery
        ) as mock_run_discovery:
            discovery_coroutine = mock_track_time_interval.call_args[0][1]

            discovery_finished = asyncio.Event()

            # Schedule multiple discoveries
            opp.async_create_task(discovery_coroutine())
            opp.async_create_task(discovery_coroutine())
            opp.async_create_task(discovery_coroutine())

            # Wait until the first discovery call is blocked
            await first_discovery_started.wait()

            # Unblock the first discovery
            discovery_finished.set()

            # Flush the remaining jobs
            await opp.async_block_till_done()

            # The discovery method should only have been called once
            mock_run_discovery.assert_called_once()


async def test_discovery_connection_error(opp, mock_entry):
    """Test that invalid devices are skipped."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    light = MagicMock(spec=pykulersky.Light)
    light.address = "AA:BB:CC:11:22:33"
    light.name = "Bedroom"
    light.connected = False
    with patch(
        "openpeerpower.components.kulersky.light.pykulersky.discover_bluetooth_devices",
        return_value=[
            {
                "address": "AA:BB:CC:11:22:33",
                "name": "Bedroom",
            }
        ],
    ):
        with patch(
            "openpeerpower.components.kulersky.light.pykulersky.Light"
        ) as mockdevice, patch.object(
            light, "connect", side_effect=pykulersky.PykulerskyException
        ):
            mockdevice.return_value = light
            mock_entry.add_to_opp(opp)
            await opp.config_entries.async_setup(mock_entry.entry_id)
            await opp.async_block_till_done()

    # Assert entity was not added
    state = opp.states.get("light.bedroom")
    assert state is None


async def test_remove_entry(opp, mock_light, mock_entry):
    """Test platform setup."""
    with patch.object(mock_light, "disconnect") as mock_disconnect:
        await opp.config_entries.async_remove(mock_entry.entry_id)

    assert mock_disconnect.called


async def test_update_exception(opp, mock_light):
    """Test platform setup."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    with patch.object(
        mock_light, "get_color", side_effect=pykulersky.PykulerskyException
    ):
        await opp.helpers.entity_component.async_update_entity("light.bedroom")
    state = opp.states.get("light.bedroom")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE


async def test_light_turn_on(opp, mock_light):
    """Test KulerSkyLight turn_on."""
    with patch.object(mock_light, "set_color") as mock_set_color, patch.object(
        mock_light, "get_color", return_value=(255, 255, 255, 255)
    ):
        await opp.services.async_call(
            "light",
            "turn_on",
            {ATTR_ENTITY_ID: "light.bedroom"},
            blocking=True,
        )
        await opp.async_block_till_done()
    mock_set_color.assert_called_with(255, 255, 255, 255)

    with patch.object(mock_light, "set_color") as mock_set_color, patch.object(
        mock_light, "get_color", return_value=(50, 50, 50, 255)
    ):
        await opp.services.async_call(
            "light",
            "turn_on",
            {ATTR_ENTITY_ID: "light.bedroom", ATTR_BRIGHTNESS: 50},
            blocking=True,
        )
        await opp.async_block_till_done()
    mock_set_color.assert_called_with(50, 50, 50, 255)

    with patch.object(mock_light, "set_color") as mock_set_color, patch.object(
        mock_light, "get_color", return_value=(50, 45, 25, 255)
    ):
        await opp.services.async_call(
            "light",
            "turn_on",
            {ATTR_ENTITY_ID: "light.bedroom", ATTR_HS_COLOR: (50, 50)},
            blocking=True,
        )
        await opp.async_block_till_done()

    mock_set_color.assert_called_with(50, 45, 25, 255)

    with patch.object(mock_light, "set_color") as mock_set_color, patch.object(
        mock_light, "get_color", return_value=(220, 201, 110, 180)
    ):
        await opp.services.async_call(
            "light",
            "turn_on",
            {ATTR_ENTITY_ID: "light.bedroom", ATTR_WHITE_VALUE: 180},
            blocking=True,
        )
        await opp.async_block_till_done()
    mock_set_color.assert_called_with(50, 45, 25, 180)


async def test_light_turn_off(opp, mock_light):
    """Test KulerSkyLight turn_on."""
    with patch.object(mock_light, "set_color") as mock_set_color, patch.object(
        mock_light, "get_color", return_value=(0, 0, 0, 0)
    ):
        await opp.services.async_call(
            "light",
            "turn_off",
            {ATTR_ENTITY_ID: "light.bedroom"},
            blocking=True,
        )
        await opp.async_block_till_done()
    mock_set_color.assert_called_with(0, 0, 0, 0)


async def test_light_update(opp, mock_light):
    """Test KulerSkyLight update."""
    utcnow = dt_util.utcnow()

    state = opp.states.get("light.bedroom")
    assert state.state == STATE_OFF
    assert state.attributes == {
        ATTR_FRIENDLY_NAME: "Bedroom",
        ATTR_SUPPORTED_FEATURES: SUPPORT_BRIGHTNESS
        | SUPPORT_COLOR
        | SUPPORT_WHITE_VALUE,
    }

    # Test an exception during discovery
    with patch.object(
        mock_light, "get_color", side_effect=pykulersky.PykulerskyException("TEST")
    ):
        utcnow = utcnow + SCAN_INTERVAL
        async_fire_time_changed(opp, utcnow)
        await opp.async_block_till_done()

    state = opp.states.get("light.bedroom")
    assert state.state == STATE_UNAVAILABLE
    assert state.attributes == {
        ATTR_FRIENDLY_NAME: "Bedroom",
        ATTR_SUPPORTED_FEATURES: SUPPORT_BRIGHTNESS
        | SUPPORT_COLOR
        | SUPPORT_WHITE_VALUE,
    }

    with patch.object(
        mock_light,
        "get_color",
        return_value=(80, 160, 200, 240),
    ):
        utcnow = utcnow + SCAN_INTERVAL
        async_fire_time_changed(opp, utcnow)
        await opp.async_block_till_done()

    state = opp.states.get("light.bedroom")
    assert state.state == STATE_ON
    assert state.attributes == {
        ATTR_FRIENDLY_NAME: "Bedroom",
        ATTR_SUPPORTED_FEATURES: SUPPORT_BRIGHTNESS
        | SUPPORT_COLOR
        | SUPPORT_WHITE_VALUE,
        ATTR_BRIGHTNESS: 200,
        ATTR_HS_COLOR: (200, 60),
        ATTR_RGB_COLOR: (102, 203, 255),
        ATTR_WHITE_VALUE: 240,
        ATTR_XY_COLOR: (0.184, 0.261),
    }
