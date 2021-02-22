"""The tests for the Modbus climate component."""
import pytest

from openpeerpower.components.climate import DOMAIN as CLIMATE_DOMAIN
from openpeerpower.components.modbus.const import (
    CONF_CLIMATES,
    CONF_CURRENT_TEMP,
    CONF_DATA_COUNT,
    CONF_TARGET_TEMP,
)
from openpeerpower.const import CONF_NAME, CONF_SCAN_INTERVAL, CONF_SLAVE

from .conftest import base_config_test, base_test


@pytest.mark.parametrize("do_options", [False, True])
async def test_config_climate.opp, do_options):
    """Run test for climate."""
    device_name = "test_climate"
    device_config = {
        CONF_NAME: device_name,
        CONF_TARGET_TEMP: 117,
        CONF_CURRENT_TEMP: 117,
        CONF_SLAVE: 10,
    }
    if do_options:
        device_config.update(
            {
                CONF_SCAN_INTERVAL: 20,
                CONF_DATA_COUNT: 2,
            }
        )
    await base_config_test(
        opp.
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
async def test_temperature_climate.opp, regs, expected):
    """Run test for given config."""
    climate_name = "modbus_test_climate"
    return
    state = await base_test(
        opp.
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
