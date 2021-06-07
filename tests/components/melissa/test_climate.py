"""Test for Melissa climate component."""
import json
from unittest.mock import AsyncMock, Mock, patch

from openpeerpower.components.climate.const import (
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from openpeerpower.components.fan import SPEED_HIGH, SPEED_LOW, SPEED_MEDIUM
from openpeerpower.components.melissa import DATA_MELISSA, climate as melissa
from openpeerpower.components.melissa.climate import MelissaClimate
from openpeerpower.const import ATTR_TEMPERATURE, TEMP_CELSIUS

from tests.common import load_fixture

_SERIAL = "12345678"


def melissa_mock():
    """Use this to mock the melissa api."""
    api = Mock()
    api.async_fetch_devices = AsyncMock(
        return_value=json.loads(load_fixture("melissa_fetch_devices.json"))
    )
    api.async_status = AsyncMock(
        return_value=json.loads(load_fixture("melissa_status.json"))
    )
    api.async_cur_settings = AsyncMock(
        return_value=json.loads(load_fixture("melissa_cur_settings.json"))
    )

    api.async_send = AsyncMock(return_value=True)

    api.STATE_OFF = 0
    api.STATE_ON = 1
    api.STATE_IDLE = 2

    api.MODE_AUTO = 0
    api.MODE_FAN = 1
    api.MODE_HEAT = 2
    api.MODE_COOL = 3
    api.MODE_DRY = 4

    api.FAN_AUTO = 0
    api.FAN_LOW = 1
    api.FAN_MEDIUM = 2
    api.FAN_HIGH = 3

    api.STATE = "state"
    api.MODE = "mode"
    api.FAN = "fan"
    api.TEMP = "temp"
    return api


async def test_setup_platform(opp):
    """Test setup_platform."""
    with patch(
        "openpeerpower.components.melissa.climate.MelissaClimate"
    ) as mocked_thermostat:
        api = melissa_mock()
        device = (await api.async_fetch_devices())[_SERIAL]
        thermostat = mocked_thermostat(api, device["serial_number"], device)
        thermostats = [thermostat]

        opp.data[DATA_MELISSA] = api

        config = {}
        add_entities = Mock()
        discovery_info = {}

        await melissa.async_setup_platform(opp, config, add_entities, discovery_info)
        add_entities.assert_called_once_with(thermostats)


async def test_get_name(opp):
    """Test name property."""
    with patch("openpeerpower.components.melissa"):
        api = melissa_mock()
        device = (await api.async_fetch_devices())[_SERIAL]
        thermostat = MelissaClimate(api, _SERIAL, device)
        assert thermostat.name == "Melissa 12345678"


async def test_current_fan_mode(opp):
    """Test current_fan_mode property."""
    with patch("openpeerpower.components.melissa"):
        api = melissa_mock()
        device = (await api.async_fetch_devices())[_SERIAL]
        thermostat = MelissaClimate(api, _SERIAL, device)
        await thermostat.async_update()
        assert thermostat.fan_mode == SPEED_LOW

        thermostat._cur_settings = None
        assert thermostat.fan_mode is None


async def test_current_temperature(opp):
    """Test current temperature."""
    with patch("openpeerpower.components.melissa"):
        api = melissa_mock()
        device = (await api.async_fetch_devices())[_SERIAL]
        thermostat = MelissaClimate(api, _SERIAL, device)
        assert thermostat.current_temperature == 27.4


async def test_current_temperature_no_data(opp):
    """Test current temperature without data."""
    with patch("openpeerpower.components.melissa"):
        api = melissa_mock()
        device = (await api.async_fetch_devices())[_SERIAL]
        thermostat = MelissaClimate(api, _SERIAL, device)
        thermostat._data = None
        assert thermostat.current_temperature is None


async def test_target_temperature_step(opp):
    """Test current target_temperature_step."""
    with patch("openpeerpower.components.melissa"):
        api = melissa_mock()
        device = (await api.async_fetch_devices())[_SERIAL]
        thermostat = MelissaClimate(api, _SERIAL, device)
        assert thermostat.target_temperature_step == 1


async def test_current_operation(opp):
    """Test current operation."""
    with patch("openpeerpower.components.melissa"):
        api = melissa_mock()
        device = (await api.async_fetch_devices())[_SERIAL]
        thermostat = MelissaClimate(api, _SERIAL, device)
        await thermostat.async_update()
        assert thermostat.state == HVAC_MODE_HEAT

        thermostat._cur_settings = None
        assert thermostat.hvac_action is None


async def test_operation_list(opp):
    """Test the operation list."""
    with patch("openpeerpower.components.melissa"):
        api = melissa_mock()
        device = (await api.async_fetch_devices())[_SERIAL]
        thermostat = MelissaClimate(api, _SERIAL, device)
        assert [
            HVAC_MODE_HEAT,
            HVAC_MODE_COOL,
            HVAC_MODE_DRY,
            HVAC_MODE_FAN_ONLY,
            HVAC_MODE_OFF,
        ] == thermostat.hvac_modes


async def test_fan_modes(opp):
    """Test the fan list."""
    with patch("openpeerpower.components.melissa"):
        api = melissa_mock()
        device = (await api.async_fetch_devices())[_SERIAL]
        thermostat = MelissaClimate(api, _SERIAL, device)
        assert ["auto", SPEED_HIGH, SPEED_MEDIUM, SPEED_LOW] == thermostat.fan_modes


async def test_target_temperature(opp):
    """Test target temperature."""
    with patch("openpeerpower.components.melissa"):
        api = melissa_mock()
        device = (await api.async_fetch_devices())[_SERIAL]
        thermostat = MelissaClimate(api, _SERIAL, device)
        await thermostat.async_update()
        assert thermostat.target_temperature == 16

        thermostat._cur_settings = None
        assert thermostat.target_temperature is None


async def test_state(opp):
    """Test state."""
    with patch("openpeerpower.components.melissa"):
        api = melissa_mock()
        device = (await api.async_fetch_devices())[_SERIAL]
        thermostat = MelissaClimate(api, _SERIAL, device)
        await thermostat.async_update()
        assert thermostat.state == HVAC_MODE_HEAT

        thermostat._cur_settings = None
        assert thermostat.state is None


async def test_temperature_unit(opp):
    """Test temperature unit."""
    with patch("openpeerpower.components.melissa"):
        api = melissa_mock()
        device = (await api.async_fetch_devices())[_SERIAL]
        thermostat = MelissaClimate(api, _SERIAL, device)
        assert thermostat.temperature_unit == TEMP_CELSIUS


async def test_min_temp(opp):
    """Test min temp."""
    with patch("openpeerpower.components.melissa"):
        api = melissa_mock()
        device = (await api.async_fetch_devices())[_SERIAL]
        thermostat = MelissaClimate(api, _SERIAL, device)
        assert thermostat.min_temp == 16


async def test_max_temp(opp):
    """Test max temp."""
    with patch("openpeerpower.components.melissa"):
        api = melissa_mock()
        device = (await api.async_fetch_devices())[_SERIAL]
        thermostat = MelissaClimate(api, _SERIAL, device)
        assert thermostat.max_temp == 30


async def test_supported_features(opp):
    """Test supported_features property."""
    with patch("openpeerpower.components.melissa"):
        api = melissa_mock()
        device = (await api.async_fetch_devices())[_SERIAL]
        thermostat = MelissaClimate(api, _SERIAL, device)
        features = SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE
        assert thermostat.supported_features == features


async def test_set_temperature(opp):
    """Test set_temperature."""
    with patch("openpeerpower.components.melissa"):
        api = melissa_mock()
        device = (await api.async_fetch_devices())[_SERIAL]
        thermostat = MelissaClimate(api, _SERIAL, device)
        await thermostat.async_update()
        await thermostat.async_set_temperature(**{ATTR_TEMPERATURE: 25})
        assert thermostat.target_temperature == 25


async def test_fan_mode(opp):
    """Test set_fan_mode."""
    with patch("openpeerpower.components.melissa"):
        api = melissa_mock()
        device = (await api.async_fetch_devices())[_SERIAL]
        thermostat = MelissaClimate(api, _SERIAL, device)
        await thermostat.async_update()
        await opp.async_block_till_done()
        await thermostat.async_set_fan_mode(SPEED_HIGH)
        await opp.async_block_till_done()
        assert thermostat.fan_mode == SPEED_HIGH


async def test_set_operation_mode(opp):
    """Test set_operation_mode."""
    with patch("openpeerpower.components.melissa"):
        api = melissa_mock()
        device = (await api.async_fetch_devices())[_SERIAL]
        thermostat = MelissaClimate(api, _SERIAL, device)
        await thermostat.async_update()
        await opp.async_block_till_done()
        await thermostat.async_set_hvac_mode(HVAC_MODE_COOL)
        await opp.async_block_till_done()
        assert thermostat.hvac_mode == HVAC_MODE_COOL


async def test_send(opp):
    """Test send."""
    with patch("openpeerpower.components.melissa"):
        api = melissa_mock()
        device = (await api.async_fetch_devices())[_SERIAL]
        thermostat = MelissaClimate(api, _SERIAL, device)
        await thermostat.async_update()
        await opp.async_block_till_done()
        await thermostat.async_send({"fan": api.FAN_MEDIUM})
        await opp.async_block_till_done()
        assert thermostat.fan_mode == SPEED_MEDIUM
        api.async_send.return_value = AsyncMock(return_value=False)
        thermostat._cur_settings = None
        await thermostat.async_send({"fan": api.FAN_LOW})
        await opp.async_block_till_done()
        assert SPEED_LOW != thermostat.fan_mode
        assert thermostat._cur_settings is None


async def test_update(opp):
    """Test update."""
    with patch(
        "openpeerpower.components.melissa.climate._LOGGER.warning"
    ) as mocked_warning, patch("openpeerpower.components.melissa"):
        api = melissa_mock()
        device = (await api.async_fetch_devices())[_SERIAL]
        thermostat = MelissaClimate(api, _SERIAL, device)
        await thermostat.async_update()
        assert thermostat.fan_mode == SPEED_LOW
        assert thermostat.state == HVAC_MODE_HEAT
        api.async_status = AsyncMock(side_effect=KeyError("boom"))
        await thermostat.async_update()
        mocked_warning.assert_called_once_with(
            "Unable to update entity %s", thermostat.entity_id
        )


async def test_melissa_op_to_opp(opp):
    """Test for translate melissa operations to opp."""
    with patch("openpeerpower.components.melissa"):
        api = melissa_mock()
        device = (await api.async_fetch_devices())[_SERIAL]
        thermostat = MelissaClimate(api, _SERIAL, device)
        assert thermostat.melissa_op_to_opp(1) == HVAC_MODE_FAN_ONLY
        assert thermostat.melissa_op_to_opp(2) == HVAC_MODE_HEAT
        assert thermostat.melissa_op_to_opp(3) == HVAC_MODE_COOL
        assert thermostat.melissa_op_to_opp(4) == HVAC_MODE_DRY
        assert thermostat.melissa_op_to_opp(5) is None


async def test_melissa_fan_to_opp(opp):
    """Test for translate melissa fan state to opp."""
    with patch("openpeerpower.components.melissa"):
        api = melissa_mock()
        device = (await api.async_fetch_devices())[_SERIAL]
        thermostat = MelissaClimate(api, _SERIAL, device)
        assert thermostat.melissa_fan_to_opp(0) == "auto"
        assert thermostat.melissa_fan_to_opp(1) == SPEED_LOW
        assert thermostat.melissa_fan_to_opp(2) == SPEED_MEDIUM
        assert thermostat.melissa_fan_to_opp(3) == SPEED_HIGH
        assert thermostat.melissa_fan_to_opp(4) is None


async def test_opp_mode_to_melissa(opp):
    """Test for opp.operations to melssa."""
    with patch(
        "openpeerpower.components.melissa.climate._LOGGER.warning"
    ) as mocked_warning, patch("openpeerpower.components.melissa"):
        api = melissa_mock()
        device = (await api.async_fetch_devices())[_SERIAL]
        thermostat = MelissaClimate(api, _SERIAL, device)
        assert thermostat.opp_mode_to_melissa(HVAC_MODE_FAN_ONLY) == 1
        assert thermostat.opp_mode_to_melissa(HVAC_MODE_HEAT) == 2
        assert thermostat.opp_mode_to_melissa(HVAC_MODE_COOL) == 3
        assert thermostat.opp_mode_to_melissa(HVAC_MODE_DRY) == 4
        thermostat.opp_mode_to_melissa("test")
        mocked_warning.assert_called_once_with(
            "Melissa have no setting for %s mode", "test"
        )


async def test_opp_fan_to_melissa(opp):
    """Test for translate melissa states to opp."""
    with patch(
        "openpeerpower.components.melissa.climate._LOGGER.warning"
    ) as mocked_warning, patch("openpeerpower.components.melissa"):
        api = melissa_mock()
        device = (await api.async_fetch_devices())[_SERIAL]
        thermostat = MelissaClimate(api, _SERIAL, device)
        assert thermostat.opp_fan_to_melissa("auto") == 0
        assert thermostat.opp_fan_to_melissa(SPEED_LOW) == 1
        assert thermostat.opp_fan_to_melissa(SPEED_MEDIUM) == 2
        assert thermostat.opp_fan_to_melissa(SPEED_HIGH) == 3
        thermostat.opp_fan_to_melissa("test")
        mocked_warning.assert_called_once_with(
            "Melissa have no setting for %s fan mode", "test"
        )
