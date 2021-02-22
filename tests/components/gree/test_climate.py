"""Tests for gree component."""
from datetime import timedelta
from unittest.mock import DEFAULT as DEFAULT_MOCK, AsyncMock, patch

from greeclimate.device import HorizontalSwing, VerticalSwing
from greeclimate.exceptions import DeviceNotBoundError, DeviceTimeoutError
import pytest

from openpeerpower.components.climate.const import (
    ATTR_FAN_MODE,
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    ATTR_SWING_MODE,
    DOMAIN,
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    PRESET_AWAY,
    PRESET_BOOST,
    PRESET_ECO,
    PRESET_NONE,
    PRESET_SLEEP,
    SERVICE_SET_FAN_MODE,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_PRESET_MODE,
    SERVICE_SET_SWING_MODE,
    SERVICE_SET_TEMPERATURE,
    SWING_BOTH,
    SWING_HORIZONTAL,
    SWING_OFF,
    SWING_VERTICAL,
)
from openpeerpower.components.gree.climate import (
    FAN_MODES_REVERSE,
    HVAC_MODES_REVERSE,
    SUPPORTED_FEATURES,
)
from openpeerpower.components.gree.const import (
    DOMAIN as GREE_DOMAIN,
    FAN_MEDIUM_HIGH,
    FAN_MEDIUM_LOW,
)
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_SUPPORTED_FEATURES,
    ATTR_TEMPERATURE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_UNAVAILABLE,
)
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util

from .common import build_device_mock

from tests.common import MockConfigEntry, async_fire_time_changed

ENTITY_ID = f"{DOMAIN}.fake_device_1"


@pytest.fixture
def mock_now():
    """Fixture for dtutil.now."""
    return dt_util.utcnow()


async def async_setup_gree.opp):
    """Set up the gree platform."""
    MockConfigEntry(domain=GREE_DOMAIN).add_to.opp.opp)
    await async_setup_component.opp, GREE_DOMAIN, {GREE_DOMAIN: {"climate": {}}})
    await opp.async_block_till_done()


async def test_discovery_called_once.opp, discovery, device):
    """Test discovery is only ever called once."""
    await async_setup_gree.opp)
    assert discovery.call_count == 1

    await async_setup_gree.opp)
    assert discovery.call_count == 1


async def test_discovery_setup_opp, discovery, device):
    """Test setup of platform."""
    MockDevice1 = build_device_mock(
        name="fake-device-1", ipAddress="1.1.1.1", mac="aabbcc112233"
    )
    MockDevice2 = build_device_mock(
        name="fake-device-2", ipAddress="2.2.2.2", mac="bbccdd223344"
    )

    discovery.return_value = [MockDevice1.device_info, MockDevice2.device_info]
    device.side_effect = [MockDevice1, MockDevice2]

    await async_setup_gree.opp)
    await opp.async_block_till_done()
    assert discovery.call_count == 1
    assert len.opp.states.async_all(DOMAIN)) == 2


async def test_discovery_setup_connection_error(opp, discovery, device):
    """Test gree integration is setup."""
    MockDevice1 = build_device_mock(name="fake-device-1")
    MockDevice1.bind = AsyncMock(side_effect=DeviceNotBoundError)

    MockDevice2 = build_device_mock(name="fake-device-2")
    MockDevice2.bind = AsyncMock(side_effect=DeviceNotBoundError)

    device.side_effect = [MockDevice1, MockDevice2]

    await async_setup_gree.opp)
    await opp.async_block_till_done()
    assert discovery.call_count == 1

    assert not.opp.states.async_all(DOMAIN)


async def test_update_connection_failure.opp, discovery, device, mock_now):
    """Testing update hvac connection failure exception."""
    device().update_state.side_effect = [
        DEFAULT_MOCK,
        DeviceTimeoutError,
        DeviceTimeoutError,
    ]

    await async_setup_gree.opp)

    next_update = mock_now + timedelta(minutes=5)
    with patch("openpeerpower.util.dt.utcnow", return_value=next_update):
        async_fire_time_changed.opp, next_update)
    await opp.async_block_till_done()

    # First update to make the device available
    state = opp.states.get(ENTITY_ID)
    assert state.name == "fake-device-1"
    assert state.state != STATE_UNAVAILABLE

    next_update = mock_now + timedelta(minutes=10)
    with patch("openpeerpower.util.dt.utcnow", return_value=next_update):
        async_fire_time_changed.opp, next_update)
    await opp.async_block_till_done()

    next_update = mock_now + timedelta(minutes=15)
    with patch("openpeerpower.util.dt.utcnow", return_value=next_update):
        async_fire_time_changed.opp, next_update)
    await opp.async_block_till_done()

    # Then two more update failures to make the device unavailable
    state = opp.states.get(ENTITY_ID)
    assert state.name == "fake-device-1"
    assert state.state == STATE_UNAVAILABLE


async def test_update_connection_failure_recovery.opp, discovery, device, mock_now):
    """Testing update hvac connection failure recovery."""
    device().update_state.side_effect = [
        DeviceTimeoutError,
        DeviceTimeoutError,
        DEFAULT_MOCK,
    ]

    await async_setup_gree.opp)

    # First update becomes unavailable
    next_update = mock_now + timedelta(minutes=5)
    with patch("openpeerpower.util.dt.utcnow", return_value=next_update):
        async_fire_time_changed.opp, next_update)
    await opp.async_block_till_done()

    state = opp.states.get(ENTITY_ID)
    assert state.name == "fake-device-1"
    assert state.state == STATE_UNAVAILABLE

    # Second update restores the connection
    next_update = mock_now + timedelta(minutes=10)
    with patch("openpeerpower.util.dt.utcnow", return_value=next_update):
        async_fire_time_changed.opp, next_update)
    await opp.async_block_till_done()

    state = opp.states.get(ENTITY_ID)
    assert state.name == "fake-device-1"
    assert state.state != STATE_UNAVAILABLE


async def test_update_unhandled_exception.opp, discovery, device, mock_now):
    """Testing update hvac connection unhandled response exception."""
    device().update_state.side_effect = [DEFAULT_MOCK, Exception]

    await async_setup_gree.opp)

    state = opp.states.get(ENTITY_ID)
    assert state.name == "fake-device-1"
    assert state.state != STATE_UNAVAILABLE

    next_update = mock_now + timedelta(minutes=10)
    with patch("openpeerpower.util.dt.utcnow", return_value=next_update):
        async_fire_time_changed.opp, next_update)
    await opp.async_block_till_done()

    state = opp.states.get(ENTITY_ID)
    assert state.name == "fake-device-1"
    assert state.state == STATE_UNAVAILABLE


async def test_send_command_device_timeout.opp, discovery, device, mock_now):
    """Test for sending power on command to the device with a device timeout."""
    await async_setup_gree.opp)

    # First update to make the device available
    next_update = mock_now + timedelta(minutes=5)
    with patch("openpeerpower.util.dt.utcnow", return_value=next_update):
        async_fire_time_changed.opp, next_update)
    await opp.async_block_till_done()

    state = opp.states.get(ENTITY_ID)
    assert state.name == "fake-device-1"
    assert state.state != STATE_UNAVAILABLE

    device().push_state_update.side_effect = DeviceTimeoutError

    # Send failure should not raise exceptions or change device state
    assert await opp.services.async_call(
        DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_HVAC_MODE: HVAC_MODE_AUTO},
        blocking=True,
    )
    await opp.async_block_till_done()

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.state != STATE_UNAVAILABLE


async def test_send_power_on.opp, discovery, device, mock_now):
    """Test for sending power on command to the device."""
    await async_setup_gree.opp)

    assert await opp.services.async_call(
        DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.state != HVAC_MODE_OFF


async def test_send_power_on_device_timeout.opp, discovery, device, mock_now):
    """Test for sending power on command to the device with a device timeout."""
    device().push_state_update.side_effect = DeviceTimeoutError

    await async_setup_gree.opp)

    assert await opp.services.async_call(
        DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.state != HVAC_MODE_OFF


async def test_send_power_off.opp, discovery, device, mock_now):
    """Test for sending power off command to the device."""
    await async_setup_gree.opp)

    next_update = mock_now + timedelta(minutes=5)
    with patch("openpeerpower.util.dt.utcnow", return_value=next_update):
        async_fire_time_changed.opp, next_update)
    await opp.async_block_till_done()

    assert await opp.services.async_call(
        DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.state == HVAC_MODE_OFF


async def test_send_power_off_device_timeout.opp, discovery, device, mock_now):
    """Test for sending power off command to the device with a device timeout."""
    device().push_state_update.side_effect = DeviceTimeoutError

    await async_setup_gree.opp)

    next_update = mock_now + timedelta(minutes=5)
    with patch("openpeerpower.util.dt.utcnow", return_value=next_update):
        async_fire_time_changed.opp, next_update)
    await opp.async_block_till_done()

    assert await opp.services.async_call(
        DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.state == HVAC_MODE_OFF


async def test_send_target_temperature.opp, discovery, device, mock_now):
    """Test for sending target temperature command to the device."""
    await async_setup_gree.opp)

    assert await opp.services.async_call(
        DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_TEMPERATURE: 25.1},
        blocking=True,
    )

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.attributes.get(ATTR_TEMPERATURE) == 25


async def test_send_target_temperature_device_timeout(
    opp. discovery, device, mock_now
):
    """Test for sending target temperature command to the device with a device timeout."""
    device().push_state_update.side_effect = DeviceTimeoutError

    await async_setup_gree.opp)

    assert await opp.services.async_call(
        DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_TEMPERATURE: 25.1},
        blocking=True,
    )

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.attributes.get(ATTR_TEMPERATURE) == 25


async def test_update_target_temperature.opp, discovery, device, mock_now):
    """Test for updating target temperature from the device."""
    device().target_temperature = 32

    await async_setup_gree.opp)

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.attributes.get(ATTR_TEMPERATURE) == 32


@pytest.mark.parametrize(
    "preset", (PRESET_AWAY, PRESET_ECO, PRESET_SLEEP, PRESET_BOOST, PRESET_NONE)
)
async def test_send_preset_mode.opp, discovery, device, mock_now, preset):
    """Test for sending preset mode command to the device."""
    await async_setup_gree.opp)

    assert await opp.services.async_call(
        DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PRESET_MODE: preset},
        blocking=True,
    )

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.attributes.get(ATTR_PRESET_MODE) == preset


async def test_send_invalid_preset_mode.opp, discovery, device, mock_now):
    """Test for sending preset mode command to the device."""
    await async_setup_gree.opp)

    with pytest.raises(ValueError):
        await opp.services.async_call(
            DOMAIN,
            SERVICE_SET_PRESET_MODE,
            {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PRESET_MODE: "invalid"},
            blocking=True,
        )

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.attributes.get(ATTR_PRESET_MODE) != "invalid"


@pytest.mark.parametrize(
    "preset", (PRESET_AWAY, PRESET_ECO, PRESET_SLEEP, PRESET_BOOST, PRESET_NONE)
)
async def test_send_preset_mode_device_timeout(
    opp. discovery, device, mock_now, preset
):
    """Test for sending preset mode command to the device with a device timeout."""
    device().push_state_update.side_effect = DeviceTimeoutError

    await async_setup_gree.opp)

    assert await opp.services.async_call(
        DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PRESET_MODE: preset},
        blocking=True,
    )

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.attributes.get(ATTR_PRESET_MODE) == preset


@pytest.mark.parametrize(
    "preset", (PRESET_AWAY, PRESET_ECO, PRESET_SLEEP, PRESET_BOOST, PRESET_NONE)
)
async def test_update_preset_mode.opp, discovery, device, mock_now, preset):
    """Test for updating preset mode from the device."""
    device().steady_heat = preset == PRESET_AWAY
    device().power_save = preset == PRESET_ECO
    device().sleep = preset == PRESET_SLEEP
    device().turbo = preset == PRESET_BOOST

    await async_setup_gree.opp)

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.attributes.get(ATTR_PRESET_MODE) == preset


@pytest.mark.parametrize(
    "hvac_mode",
    (
        HVAC_MODE_OFF,
        HVAC_MODE_AUTO,
        HVAC_MODE_COOL,
        HVAC_MODE_DRY,
        HVAC_MODE_FAN_ONLY,
        HVAC_MODE_HEAT,
    ),
)
async def test_send_hvac_mode.opp, discovery, device, mock_now, hvac_mode):
    """Test for sending hvac mode command to the device."""
    await async_setup_gree.opp)

    assert await opp.services.async_call(
        DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_HVAC_MODE: hvac_mode},
        blocking=True,
    )

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.state == hvac_mode


@pytest.mark.parametrize(
    "hvac_mode",
    (HVAC_MODE_AUTO, HVAC_MODE_COOL, HVAC_MODE_DRY, HVAC_MODE_FAN_ONLY, HVAC_MODE_HEAT),
)
async def test_send_hvac_mode_device_timeout(
    opp. discovery, device, mock_now, hvac_mode
):
    """Test for sending hvac mode command to the device with a device timeout."""
    device().push_state_update.side_effect = DeviceTimeoutError

    await async_setup_gree.opp)

    assert await opp.services.async_call(
        DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_HVAC_MODE: hvac_mode},
        blocking=True,
    )

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.state == hvac_mode


@pytest.mark.parametrize(
    "hvac_mode",
    (
        HVAC_MODE_OFF,
        HVAC_MODE_AUTO,
        HVAC_MODE_COOL,
        HVAC_MODE_DRY,
        HVAC_MODE_FAN_ONLY,
        HVAC_MODE_HEAT,
    ),
)
async def test_update_hvac_mode.opp, discovery, device, mock_now, hvac_mode):
    """Test for updating hvac mode from the device."""
    device().power = hvac_mode != HVAC_MODE_OFF
    device().mode = HVAC_MODES_REVERSE.get(hvac_mode)

    await async_setup_gree.opp)

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.state == hvac_mode


@pytest.mark.parametrize(
    "fan_mode",
    (FAN_AUTO, FAN_LOW, FAN_MEDIUM_LOW, FAN_MEDIUM, FAN_MEDIUM_HIGH, FAN_HIGH),
)
async def test_send_fan_mode.opp, discovery, device, mock_now, fan_mode):
    """Test for sending fan mode command to the device."""
    await async_setup_gree.opp)

    assert await opp.services.async_call(
        DOMAIN,
        SERVICE_SET_FAN_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_FAN_MODE: fan_mode},
        blocking=True,
    )

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.attributes.get(ATTR_FAN_MODE) == fan_mode


async def test_send_invalid_fan_mode.opp, discovery, device, mock_now):
    """Test for sending fan mode command to the device."""
    await async_setup_gree.opp)

    with pytest.raises(ValueError):
        await opp.services.async_call(
            DOMAIN,
            SERVICE_SET_FAN_MODE,
            {ATTR_ENTITY_ID: ENTITY_ID, ATTR_FAN_MODE: "invalid"},
            blocking=True,
        )

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.attributes.get(ATTR_FAN_MODE) != "invalid"


@pytest.mark.parametrize(
    "fan_mode",
    (FAN_AUTO, FAN_LOW, FAN_MEDIUM_LOW, FAN_MEDIUM, FAN_MEDIUM_HIGH, FAN_HIGH),
)
async def test_send_fan_mode_device_timeout(
    opp. discovery, device, mock_now, fan_mode
):
    """Test for sending fan mode command to the device with a device timeout."""
    device().push_state_update.side_effect = DeviceTimeoutError

    await async_setup_gree.opp)

    assert await opp.services.async_call(
        DOMAIN,
        SERVICE_SET_FAN_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_FAN_MODE: fan_mode},
        blocking=True,
    )

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.attributes.get(ATTR_FAN_MODE) == fan_mode


@pytest.mark.parametrize(
    "fan_mode",
    (FAN_AUTO, FAN_LOW, FAN_MEDIUM_LOW, FAN_MEDIUM, FAN_MEDIUM_HIGH, FAN_HIGH),
)
async def test_update_fan_mode.opp, discovery, device, mock_now, fan_mode):
    """Test for updating fan mode from the device."""
    device().fan_speed = FAN_MODES_REVERSE.get(fan_mode)

    await async_setup_gree.opp)

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.attributes.get(ATTR_FAN_MODE) == fan_mode


@pytest.mark.parametrize(
    "swing_mode", (SWING_OFF, SWING_BOTH, SWING_VERTICAL, SWING_HORIZONTAL)
)
async def test_send_swing_mode.opp, discovery, device, mock_now, swing_mode):
    """Test for sending swing mode command to the device."""
    await async_setup_gree.opp)

    assert await opp.services.async_call(
        DOMAIN,
        SERVICE_SET_SWING_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_SWING_MODE: swing_mode},
        blocking=True,
    )

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.attributes.get(ATTR_SWING_MODE) == swing_mode


async def test_send_invalid_swing_mode.opp, discovery, device, mock_now):
    """Test for sending swing mode command to the device."""
    await async_setup_gree.opp)

    with pytest.raises(ValueError):
        await opp.services.async_call(
            DOMAIN,
            SERVICE_SET_SWING_MODE,
            {ATTR_ENTITY_ID: ENTITY_ID, ATTR_SWING_MODE: "invalid"},
            blocking=True,
        )

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.attributes.get(ATTR_SWING_MODE) != "invalid"


@pytest.mark.parametrize(
    "swing_mode", (SWING_OFF, SWING_BOTH, SWING_VERTICAL, SWING_HORIZONTAL)
)
async def test_send_swing_mode_device_timeout(
    opp. discovery, device, mock_now, swing_mode
):
    """Test for sending swing mode command to the device with a device timeout."""
    device().push_state_update.side_effect = DeviceTimeoutError

    await async_setup_gree.opp)

    assert await opp.services.async_call(
        DOMAIN,
        SERVICE_SET_SWING_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_SWING_MODE: swing_mode},
        blocking=True,
    )

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.attributes.get(ATTR_SWING_MODE) == swing_mode


@pytest.mark.parametrize(
    "swing_mode", (SWING_OFF, SWING_BOTH, SWING_VERTICAL, SWING_HORIZONTAL)
)
async def test_update_swing_mode.opp, discovery, device, mock_now, swing_mode):
    """Test for updating swing mode from the device."""
    device().horizontal_swing = (
        HorizontalSwing.FullSwing
        if swing_mode in (SWING_BOTH, SWING_HORIZONTAL)
        else HorizontalSwing.Default
    )
    device().vertical_swing = (
        VerticalSwing.FullSwing
        if swing_mode in (SWING_BOTH, SWING_VERTICAL)
        else VerticalSwing.Default
    )

    await async_setup_gree.opp)

    state = opp.states.get(ENTITY_ID)
    assert state is not None
    assert state.attributes.get(ATTR_SWING_MODE) == swing_mode


async def test_name.opp, discovery, device):
    """Test for name property."""
    await async_setup_gree.opp)
    state = opp.states.get(ENTITY_ID)
    assert state.attributes[ATTR_FRIENDLY_NAME] == "fake-device-1"


async def test_supported_features_with_turnon.opp, discovery, device):
    """Test for supported_features property."""
    await async_setup_gree.opp)
    state = opp.states.get(ENTITY_ID)
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == SUPPORTED_FEATURES
