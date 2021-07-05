"""The tests for the Modbus sensor component."""
import pytest

from openpeerpower.components.binary_sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.components.modbus.const import (
    CALL_TYPE_COIL,
    CALL_TYPE_DISCRETE,
    CONF_INPUT_TYPE,
    CONF_INPUTS,
)
from openpeerpower.const import (
    CONF_ADDRESS,
    CONF_BINARY_SENSORS,
    CONF_DEVICE_CLASS,
    CONF_NAME,
    CONF_SLAVE,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from openpeerpower.core import State

from .conftest import ReadResult, base_config_test, base_test, prepare_service_update

from tests.common import mock_restore_cache


@pytest.mark.parametrize("do_discovery", [False, True])
@pytest.mark.parametrize(
    "do_options",
    [
        {},
        {
            CONF_SLAVE: 10,
            CONF_INPUT_TYPE: CALL_TYPE_DISCRETE,
            CONF_DEVICE_CLASS: "door",
        },
    ],
)
async def test_config_binary_sensor(opp, do_discovery, do_options):
    """Run test for binary sensor."""
    sensor_name = "test_sensor"
    config_sensor = {
        CONF_NAME: sensor_name,
        CONF_ADDRESS: 51,
        **do_options,
    }
    await base_config_test(
        opp,
        config_sensor,
        sensor_name,
        SENSOR_DOMAIN,
        CONF_BINARY_SENSORS,
        CONF_INPUTS,
        method_discovery=do_discovery,
    )


@pytest.mark.parametrize("do_type", [CALL_TYPE_COIL, CALL_TYPE_DISCRETE])
@pytest.mark.parametrize(
    "regs,expected",
    [
        (
            [0xFF],
            STATE_ON,
        ),
        (
            [0x01],
            STATE_ON,
        ),
        (
            [0x00],
            STATE_OFF,
        ),
        (
            [0x80],
            STATE_OFF,
        ),
        (
            [0xFE],
            STATE_OFF,
        ),
        (
            None,
            STATE_UNAVAILABLE,
        ),
    ],
)
async def test_all_binary_sensor(opp, do_type, regs, expected):
    """Run test for given config."""
    sensor_name = "modbus_test_binary_sensor"
    state = await base_test(
        opp,
        {CONF_NAME: sensor_name, CONF_ADDRESS: 1234, CONF_INPUT_TYPE: do_type},
        sensor_name,
        SENSOR_DOMAIN,
        CONF_BINARY_SENSORS,
        CONF_INPUTS,
        regs,
        expected,
        method_discovery=True,
        scan_interval=5,
    )
    assert state == expected


async def test_service_binary_sensor_update(opp, mock_pymodbus):
    """Run test for service openpeerpower.update_entity."""

    entity_id = "binary_sensor.test"
    config = {
        CONF_BINARY_SENSORS: [
            {
                CONF_NAME: "test",
                CONF_ADDRESS: 1234,
                CONF_INPUT_TYPE: CALL_TYPE_COIL,
            }
        ]
    }
    mock_pymodbus.read_coils.return_value = ReadResult([0x00])
    await prepare_service_update(
        opp,
        config,
    )
    await opp.services.async_call(
        "openpeerpower", "update_entity", {"entity_id": entity_id}, blocking=True
    )
    await opp.async_block_till_done()
    assert opp.states.get(entity_id).state == STATE_OFF

    mock_pymodbus.read_coils.return_value = ReadResult([0x01])
    await opp.services.async_call(
        "openpeerpower", "update_entity", {"entity_id": entity_id}, blocking=True
    )
    assert opp.states.get(entity_id).state == STATE_ON


async def test_restore_state_binary_sensor(opp):
    """Run test for binary sensor restore state."""

    sensor_name = "test_binary_sensor"
    test_value = STATE_ON
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
        CONF_BINARY_SENSORS,
        None,
        method_discovery=True,
    )
    entity_id = f"{SENSOR_DOMAIN}.{sensor_name}"
    assert opp.states.get(entity_id).state == test_value
