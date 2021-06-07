"""The tests for the Modbus sensor component."""
import logging

import pytest

from openpeerpower.components.modbus.const import (
    CALL_TYPE_REGISTER_HOLDING,
    CALL_TYPE_REGISTER_INPUT,
    CONF_DATA_TYPE,
    CONF_INPUT_TYPE,
    CONF_PRECISION,
    CONF_REGISTERS,
    CONF_REVERSE_ORDER,
    CONF_SCALE,
    CONF_SWAP,
    CONF_SWAP_BYTE,
    CONF_SWAP_NONE,
    CONF_SWAP_WORD,
    CONF_SWAP_WORD_BYTE,
    DATA_TYPE_CUSTOM,
    DATA_TYPE_FLOAT,
    DATA_TYPE_INT,
    DATA_TYPE_STRING,
    DATA_TYPE_UINT,
)
from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.const import (
    CONF_ADDRESS,
    CONF_COUNT,
    CONF_DEVICE_CLASS,
    CONF_NAME,
    CONF_OFFSET,
    CONF_SENSORS,
    CONF_SLAVE,
    CONF_STRUCTURE,
    STATE_UNAVAILABLE,
)
from openpeerpower.core import State

from .conftest import ReadResult, base_config_test, base_test, prepare_service_update

from tests.common import mock_restore_cache


@pytest.mark.parametrize(
    "do_config",
    [
        {
            CONF_ADDRESS: 51,
        },
        {
            CONF_ADDRESS: 51,
            CONF_SLAVE: 10,
            CONF_COUNT: 1,
            CONF_DATA_TYPE: "int",
            CONF_PRECISION: 0,
            CONF_SCALE: 1,
            CONF_REVERSE_ORDER: False,
            CONF_OFFSET: 0,
            CONF_INPUT_TYPE: CALL_TYPE_REGISTER_HOLDING,
            CONF_DEVICE_CLASS: "battery",
        },
        {
            CONF_ADDRESS: 51,
            CONF_SLAVE: 10,
            CONF_COUNT: 1,
            CONF_DATA_TYPE: "int",
            CONF_PRECISION: 0,
            CONF_SCALE: 1,
            CONF_REVERSE_ORDER: False,
            CONF_OFFSET: 0,
            CONF_INPUT_TYPE: CALL_TYPE_REGISTER_INPUT,
            CONF_DEVICE_CLASS: "battery",
        },
        {
            CONF_ADDRESS: 51,
            CONF_COUNT: 1,
            CONF_SWAP: CONF_SWAP_NONE,
        },
        {
            CONF_ADDRESS: 51,
            CONF_COUNT: 1,
            CONF_SWAP: CONF_SWAP_BYTE,
        },
        {
            CONF_ADDRESS: 51,
            CONF_COUNT: 2,
            CONF_SWAP: CONF_SWAP_WORD,
        },
        {
            CONF_ADDRESS: 51,
            CONF_COUNT: 2,
            CONF_SWAP: CONF_SWAP_WORD_BYTE,
        },
    ],
)
async def test_config_sensor(opp, do_config):
    """Run test for sensor."""
    sensor_name = "test_sensor"
    config_sensor = {
        CONF_NAME: sensor_name,
        **do_config,
    }
    await base_config_test(
        opp,
        config_sensor,
        sensor_name,
        SENSOR_DOMAIN,
        CONF_SENSORS,
        CONF_REGISTERS,
        method_discovery=True,
    )


@pytest.mark.parametrize(
    "do_config,error_message",
    [
        (
            {
                CONF_ADDRESS: 1234,
                CONF_COUNT: 8,
                CONF_PRECISION: 2,
                CONF_DATA_TYPE: DATA_TYPE_INT,
            },
            "Unable to detect data type for test_sensor sensor, try a custom type",
        ),
        (
            {
                CONF_ADDRESS: 1234,
                CONF_COUNT: 8,
                CONF_PRECISION: 2,
                CONF_DATA_TYPE: DATA_TYPE_CUSTOM,
                CONF_STRUCTURE: ">no struct",
            },
            "Error in sensor test_sensor structure: bad char in struct format",
        ),
        (
            {
                CONF_ADDRESS: 1234,
                CONF_COUNT: 2,
                CONF_PRECISION: 2,
                CONF_DATA_TYPE: DATA_TYPE_CUSTOM,
                CONF_STRUCTURE: ">4f",
            },
            "Structure request 16 bytes, but 2 registers have a size of 4 bytes",
        ),
        (
            {
                CONF_ADDRESS: 1234,
                CONF_DATA_TYPE: DATA_TYPE_CUSTOM,
                CONF_COUNT: 4,
                CONF_SWAP: CONF_SWAP_NONE,
                CONF_STRUCTURE: "invalid",
            },
            "Error in sensor test_sensor structure: bad char in struct format",
        ),
        (
            {
                CONF_ADDRESS: 1234,
                CONF_DATA_TYPE: DATA_TYPE_CUSTOM,
                CONF_COUNT: 4,
                CONF_SWAP: CONF_SWAP_NONE,
                CONF_STRUCTURE: "",
            },
            "Error in sensor test_sensor. The `structure` field can not be empty if the parameter `data_type` is set to the `custom`",
        ),
        (
            {
                CONF_ADDRESS: 1234,
                CONF_DATA_TYPE: DATA_TYPE_CUSTOM,
                CONF_COUNT: 4,
                CONF_SWAP: CONF_SWAP_NONE,
                CONF_STRUCTURE: "1s",
            },
            "Structure request 1 bytes, but 4 registers have a size of 8 bytes",
        ),
        (
            {
                CONF_ADDRESS: 1234,
                CONF_DATA_TYPE: DATA_TYPE_CUSTOM,
                CONF_COUNT: 1,
                CONF_STRUCTURE: "2s",
                CONF_SWAP: CONF_SWAP_WORD,
            },
            "Error in sensor test_sensor swap(word) not possible due to the registers count: 1, needed: 2",
        ),
    ],
)
async def test_config_wrong_struct_sensor(
    opp, caplog, do_config, error_message, mock_pymodbus
):
    """Run test for sensor with wrong struct."""

    sensor_name = "test_sensor"
    config_sensor = {
        CONF_NAME: sensor_name,
        **do_config,
    }
    caplog.set_level(logging.WARNING)
    caplog.clear()

    await base_config_test(
        opp,
        config_sensor,
        sensor_name,
        SENSOR_DOMAIN,
        CONF_SENSORS,
        None,
        method_discovery=True,
        expect_setup_to_fail=True,
    )

    assert error_message in caplog.text


@pytest.mark.parametrize(
    "cfg,regs,expected",
    [
        (
            {
                CONF_COUNT: 1,
                CONF_DATA_TYPE: DATA_TYPE_INT,
                CONF_SCALE: 1,
                CONF_OFFSET: 0,
                CONF_PRECISION: 0,
            },
            [0],
            "0",
        ),
        (
            {},
            [0x8000],
            "-32768",
        ),
        (
            {
                CONF_COUNT: 1,
                CONF_DATA_TYPE: DATA_TYPE_INT,
                CONF_SCALE: 1,
                CONF_OFFSET: 13,
                CONF_PRECISION: 0,
            },
            [7],
            "20",
        ),
        (
            {
                CONF_COUNT: 1,
                CONF_DATA_TYPE: DATA_TYPE_INT,
                CONF_SCALE: 3,
                CONF_OFFSET: 13,
                CONF_PRECISION: 0,
            },
            [7],
            "34",
        ),
        (
            {
                CONF_COUNT: 1,
                CONF_DATA_TYPE: DATA_TYPE_UINT,
                CONF_SCALE: 3,
                CONF_OFFSET: 13,
                CONF_PRECISION: 4,
            },
            [7],
            "34.0000",
        ),
        (
            {
                CONF_COUNT: 1,
                CONF_DATA_TYPE: DATA_TYPE_INT,
                CONF_SCALE: 1.5,
                CONF_OFFSET: 0,
                CONF_PRECISION: 0,
            },
            [1],
            "2",
        ),
        (
            {
                CONF_COUNT: 1,
                CONF_DATA_TYPE: DATA_TYPE_INT,
                CONF_SCALE: "1.5",
                CONF_OFFSET: "5",
                CONF_PRECISION: "1",
            },
            [9],
            "18.5",
        ),
        (
            {
                CONF_COUNT: 1,
                CONF_DATA_TYPE: DATA_TYPE_INT,
                CONF_SCALE: 2.4,
                CONF_OFFSET: 0,
                CONF_PRECISION: 2,
            },
            [1],
            "2.40",
        ),
        (
            {
                CONF_COUNT: 1,
                CONF_DATA_TYPE: DATA_TYPE_INT,
                CONF_SCALE: 1,
                CONF_OFFSET: -10.3,
                CONF_PRECISION: 1,
            },
            [2],
            "-8.3",
        ),
        (
            {
                CONF_COUNT: 2,
                CONF_DATA_TYPE: DATA_TYPE_INT,
                CONF_SCALE: 1,
                CONF_OFFSET: 0,
                CONF_PRECISION: 0,
            },
            [0x89AB, 0xCDEF],
            "-1985229329",
        ),
        (
            {
                CONF_COUNT: 2,
                CONF_DATA_TYPE: DATA_TYPE_UINT,
                CONF_SCALE: 1,
                CONF_OFFSET: 0,
                CONF_PRECISION: 0,
            },
            [0x89AB, 0xCDEF],
            str(0x89ABCDEF),
        ),
        (
            {
                CONF_COUNT: 2,
                CONF_DATA_TYPE: DATA_TYPE_UINT,
                CONF_REVERSE_ORDER: True,
            },
            [0x89AB, 0xCDEF],
            str(0xCDEF89AB),
        ),
        (
            {
                CONF_COUNT: 4,
                CONF_DATA_TYPE: DATA_TYPE_UINT,
                CONF_SCALE: 1,
                CONF_OFFSET: 0,
                CONF_PRECISION: 0,
            },
            [0x89AB, 0xCDEF, 0x0123, 0x4567],
            "9920249030613615975",
        ),
        (
            {
                CONF_COUNT: 4,
                CONF_DATA_TYPE: DATA_TYPE_UINT,
                CONF_SCALE: 2,
                CONF_OFFSET: 3,
                CONF_PRECISION: 0,
            },
            [0x0123, 0x4567, 0x89AB, 0xCDEF],
            "163971058432973793",
        ),
        (
            {
                CONF_COUNT: 4,
                CONF_DATA_TYPE: DATA_TYPE_UINT,
                CONF_SCALE: 2.0,
                CONF_OFFSET: 3.0,
                CONF_PRECISION: 0,
            },
            [0x0123, 0x4567, 0x89AB, 0xCDEF],
            "163971058432973792",
        ),
        (
            {
                CONF_COUNT: 2,
                CONF_INPUT_TYPE: CALL_TYPE_REGISTER_INPUT,
                CONF_DATA_TYPE: DATA_TYPE_UINT,
                CONF_SCALE: 1,
                CONF_OFFSET: 0,
                CONF_PRECISION: 0,
            },
            [0x89AB, 0xCDEF],
            str(0x89ABCDEF),
        ),
        (
            {
                CONF_COUNT: 2,
                CONF_INPUT_TYPE: CALL_TYPE_REGISTER_HOLDING,
                CONF_DATA_TYPE: DATA_TYPE_UINT,
                CONF_SCALE: 1,
                CONF_OFFSET: 0,
                CONF_PRECISION: 0,
            },
            [0x89AB, 0xCDEF],
            str(0x89ABCDEF),
        ),
        (
            {
                CONF_COUNT: 2,
                CONF_INPUT_TYPE: CALL_TYPE_REGISTER_HOLDING,
                CONF_DATA_TYPE: DATA_TYPE_FLOAT,
                CONF_SCALE: 1,
                CONF_OFFSET: 0,
                CONF_PRECISION: 5,
            },
            [16286, 1617],
            "1.23457",
        ),
        (
            {
                CONF_COUNT: 8,
                CONF_INPUT_TYPE: CALL_TYPE_REGISTER_HOLDING,
                CONF_DATA_TYPE: DATA_TYPE_STRING,
                CONF_SCALE: 1,
                CONF_OFFSET: 0,
                CONF_PRECISION: 0,
            },
            [0x3037, 0x2D30, 0x352D, 0x3230, 0x3230, 0x2031, 0x343A, 0x3335],
            "07-05-2020 14:35",
        ),
        (
            {
                CONF_COUNT: 8,
                CONF_INPUT_TYPE: CALL_TYPE_REGISTER_HOLDING,
                CONF_DATA_TYPE: DATA_TYPE_STRING,
                CONF_SCALE: 1,
                CONF_OFFSET: 0,
                CONF_PRECISION: 0,
            },
            None,
            STATE_UNAVAILABLE,
        ),
        (
            {
                CONF_COUNT: 2,
                CONF_INPUT_TYPE: CALL_TYPE_REGISTER_INPUT,
                CONF_DATA_TYPE: DATA_TYPE_UINT,
                CONF_SCALE: 1,
                CONF_OFFSET: 0,
                CONF_PRECISION: 0,
            },
            None,
            STATE_UNAVAILABLE,
        ),
        (
            {
                CONF_COUNT: 1,
                CONF_DATA_TYPE: DATA_TYPE_INT,
                CONF_SWAP: CONF_SWAP_NONE,
            },
            [0x0102],
            str(int(0x0102)),
        ),
        (
            {
                CONF_COUNT: 1,
                CONF_DATA_TYPE: DATA_TYPE_INT,
                CONF_SWAP: CONF_SWAP_BYTE,
            },
            [0x0201],
            str(int(0x0102)),
        ),
        (
            {
                CONF_COUNT: 2,
                CONF_DATA_TYPE: DATA_TYPE_INT,
                CONF_SWAP: CONF_SWAP_BYTE,
            },
            [0x0102, 0x0304],
            str(int(0x02010403)),
        ),
        (
            {
                CONF_COUNT: 2,
                CONF_DATA_TYPE: DATA_TYPE_INT,
                CONF_SWAP: CONF_SWAP_WORD,
            },
            [0x0102, 0x0304],
            str(int(0x03040102)),
        ),
        (
            {
                CONF_COUNT: 2,
                CONF_DATA_TYPE: DATA_TYPE_INT,
                CONF_SWAP: CONF_SWAP_WORD_BYTE,
            },
            [0x0102, 0x0304],
            str(int(0x04030201)),
        ),
    ],
)
async def test_all_sensor(opp, cfg, regs, expected):
    """Run test for sensor."""

    sensor_name = "modbus_test_sensor"
    state = await base_test(
        opp,
        {CONF_NAME: sensor_name, CONF_ADDRESS: 1234, **cfg},
        sensor_name,
        SENSOR_DOMAIN,
        CONF_SENSORS,
        CONF_REGISTERS,
        regs,
        expected,
        method_discovery=True,
        scan_interval=5,
    )
    assert state == expected


@pytest.mark.parametrize(
    "cfg,regs,expected",
    [
        (
            {
                CONF_COUNT: 8,
                CONF_PRECISION: 2,
                CONF_DATA_TYPE: DATA_TYPE_CUSTOM,
                CONF_STRUCTURE: ">4f",
            },
            # floats: 7.931250095367432, 10.600000381469727,
            #         1.000879611487865e-28, 10.566553115844727
            [0x40FD, 0xCCCD, 0x4129, 0x999A, 0x10FD, 0xC0CD, 0x4129, 0x109A],
            "7.93,10.60,0.00,10.57",
        ),
        (
            {
                CONF_COUNT: 4,
                CONF_PRECISION: 0,
                CONF_DATA_TYPE: DATA_TYPE_CUSTOM,
                CONF_STRUCTURE: ">2i",
            },
            [0x0000, 0x0100, 0x0000, 0x0032],
            "256,50",
        ),
        (
            {
                CONF_COUNT: 1,
                CONF_PRECISION: 0,
                CONF_DATA_TYPE: DATA_TYPE_INT,
            },
            [0x0101],
            "257",
        ),
    ],
)
async def test_struct_sensor(opp, cfg, regs, expected):
    """Run test for sensor struct."""

    sensor_name = "modbus_test_sensor"
    state = await base_test(
        opp,
        {CONF_NAME: sensor_name, CONF_ADDRESS: 1234, **cfg},
        sensor_name,
        SENSOR_DOMAIN,
        CONF_SENSORS,
        None,
        regs,
        expected,
        method_discovery=True,
        scan_interval=5,
    )
    assert state == expected


async def test_restore_state_sensor(opp):
    """Run test for sensor restore state."""

    sensor_name = "test_sensor"
    test_value = "117"
    config_sensor = {CONF_NAME: sensor_name, CONF_ADDRESS: 17}
    mock_restore_cache(
        opp,
        (State(f"{SENSOR_DOMAIN}.{sensor_name}", test_value),),
    )
    await base_config_test(
        opp,
        config_sensor,
        sensor_name,
        SENSOR_DOMAIN,
        CONF_SENSORS,
        None,
        method_discovery=True,
    )
    entity_id = f"{SENSOR_DOMAIN}.{sensor_name}"
    assert opp.states.get(entity_id).state == test_value


@pytest.mark.parametrize(
    "swap_type, error_message",
    [
        (
            CONF_SWAP_WORD,
            "Error in sensor modbus_test_sensor swap(word) not possible due to the registers count: 1, needed: 2",
        ),
        (
            CONF_SWAP_WORD_BYTE,
            "Error in sensor modbus_test_sensor swap(word_byte) not possible due to the registers count: 1, needed: 2",
        ),
    ],
)
async def test_swap_sensor_wrong_config(
    opp, caplog, swap_type, error_message, mock_pymodbus
):
    """Run test for sensor swap."""
    sensor_name = "modbus_test_sensor"
    config = {
        CONF_NAME: sensor_name,
        CONF_ADDRESS: 1234,
        CONF_COUNT: 1,
        CONF_SWAP: swap_type,
        CONF_DATA_TYPE: DATA_TYPE_INT,
    }

    caplog.set_level(logging.ERROR)
    caplog.clear()
    await base_config_test(
        opp,
        config,
        sensor_name,
        SENSOR_DOMAIN,
        CONF_SENSORS,
        None,
        method_discovery=True,
        expect_setup_to_fail=True,
    )
    assert error_message in "".join(caplog.messages)


async def test_service_sensor_update(opp, mock_pymodbus):
    """Run test for service openpeerpower.update_entity."""

    entity_id = "sensor.test"
    config = {
        CONF_SENSORS: [
            {
                CONF_NAME: "test",
                CONF_ADDRESS: 1234,
                CONF_INPUT_TYPE: CALL_TYPE_REGISTER_INPUT,
            }
        ]
    }
    mock_pymodbus.read_input_registers.return_value = ReadResult([27])
    await prepare_service_update(
        opp,
        config,
    )
    await opp.services.async_call(
        "openpeerpower", "update_entity", {"entity_id": entity_id}, blocking=True
    )
    assert opp.states.get(entity_id).state == "27"
    mock_pymodbus.read_input_registers.return_value = ReadResult([32])
    await opp.services.async_call(
        "openpeerpower", "update_entity", {"entity_id": entity_id}, blocking=True
    )
    assert opp.states.get(entity_id).state == "32"
