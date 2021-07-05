"""The tests for the Modbus climate component."""
import pytest

from openpeerpower.components.climate import DOMAIN as CLIMATE_DOMAIN
from openpeerpower.components.climate.const import HVAC_MODE_AUTO
from openpeerpower.components.modbus.const import (
    CONF_CLIMATES,
    CONF_CURRENT_TEMP,
    CONF_DATA_COUNT,
    CONF_TARGET_TEMP,
)
from openpeerpower.const import (
    ATTR_TEMPERATURE,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_SLAVE,
)
from openpeerpower.core import State

from .conftest import ReadResult, base_config_test, base_test, prepare_service_update

from tests.common import mock_restore_cache


@pytest.mark.parametrize(
    "do_options",
    [
        {},
        {
            CONF_SCAN_INTERVAL: 20,
            CONF_DATA_COUNT: 2,
        },
    ],
)
async def test_config_climate(opp, do_options):
    """Run test for climate."""
    device_name = "test_climate"
    device_config = {
        CONF_NAME: device_name,
        CONF_TARGET_TEMP: 117,
        CONF_CURRENT_TEMP: 117,
        CONF_SLAVE: 10,
        **do_options,
    }
    await base_config_test(
        opp,
        device_config,
        device_name,
        CLIMATE_DOMAIN,
        CONF_CLIMATES,
        None,
        method_discovery=True,
    )


@pytest.mark.parametrize(
    "regs,expected",
    [
        (
            [0x00],
            "auto",
        ),
    ],
)
async def test_temperature_climate(opp, regs, expected):
    """Run test for given config."""
    climate_name = "modbus_test_climate"
    return
    state = await base_test(
        opp,
        {
            CONF_NAME: climate_name,
            CONF_SLAVE: 1,
            CONF_TARGET_TEMP: 117,
            CONF_CURRENT_TEMP: 117,
            CONF_DATA_COUNT: 2,
        },
        climate_name,
        CLIMATE_DOMAIN,
        CONF_CLIMATES,
        None,
        regs,
        expected,
        method_discovery=True,
        scan_interval=5,
    )
    assert state == expected


async def test_service_climate_update(opp, mock_pymodbus):
    """Run test for service openpeerpower.update_entity."""

    entity_id = "climate.test"
    config = {
        CONF_CLIMATES: [
            {
                CONF_NAME: "test",
                CONF_TARGET_TEMP: 117,
                CONF_CURRENT_TEMP: 117,
                CONF_SLAVE: 10,
            }
        ]
    }
    mock_pymodbus.read_input_registers.return_value = ReadResult([0x00])
    await prepare_service_update(
        opp,
        config,
    )
    await opp.services.async_call(
        "openpeerpower", "update_entity", {"entity_id": entity_id}, blocking=True
    )
    assert opp.states.get(entity_id).state == "auto"


async def test_restore_state_climate(opp):
    """Run test for sensor restore state."""

    climate_name = "test_climate"
    test_temp = 37
    entity_id = f"{CLIMATE_DOMAIN}.{climate_name}"
    test_value = State(entity_id, 35)
    test_value.attributes = {ATTR_TEMPERATURE: test_temp}
    config_sensor = {
        CONF_NAME: climate_name,
        CONF_TARGET_TEMP: 117,
        CONF_CURRENT_TEMP: 117,
    }
    mock_restore_cache(
        opp,
        (test_value,),
    )
    await base_config_test(
        opp,
        config_sensor,
        climate_name,
        CLIMATE_DOMAIN,
        CONF_CLIMATES,
        None,
        method_discovery=True,
    )
    state = opp.states.get(entity_id)
    assert state.state == HVAC_MODE_AUTO
    assert state.attributes[ATTR_TEMPERATURE] == test_temp
