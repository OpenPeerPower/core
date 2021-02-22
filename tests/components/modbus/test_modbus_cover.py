"""The tests for the Modbus cover component."""
import pytest

from openpeerpower.components.cover import DOMAIN as COVER_DOMAIN
from openpeerpower.components.modbus.const import CALL_TYPE_COIL, CONF_REGISTER
from openpeerpower.const import (
    CONF_COVERS,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_SLAVE,
    STATE_OPEN,
    STATE_OPENING,
)

from .conftest import base_config_test, base_test


@pytest.mark.parametrize("do_options", [False, True])
@pytest.mark.parametrize("read_type", [CALL_TYPE_COIL, CONF_REGISTER])
async def test_config_cover.opp, do_options, read_type):
    """Run test for cover."""
    device_name = "test_cover"
    device_config = {
        CONF_NAME: device_name,
        read_type: 1234,
    }
    if do_options:
        device_config.update(
            {
                CONF_SLAVE: 10,
                CONF_SCAN_INTERVAL: 20,
            }
        )
    await base_config_test(
        opp.
        device_config,
        device_name,
        COVER_DOMAIN,
        CONF_COVERS,
        None,
        method_discovery=True,
    )


@pytest.mark.parametrize(
    "regs,expected",
    [
        (
            [0x00],
            STATE_OPENING,
        ),
        (
            [0x80],
            STATE_OPENING,
        ),
        (
            [0xFE],
            STATE_OPENING,
        ),
        (
            [0xFF],
            STATE_OPENING,
        ),
        (
            [0x01],
            STATE_OPENING,
        ),
    ],
)
async def test_coil_cover.opp, regs, expected):
    """Run test for given config."""
    cover_name = "modbus_test_cover"
    state = await base_test(
        opp.
        {
            CONF_NAME: cover_name,
            CALL_TYPE_COIL: 1234,
            CONF_SLAVE: 1,
        },
        cover_name,
        COVER_DOMAIN,
        CONF_COVERS,
        None,
        regs,
        expected,
        method_discovery=True,
        scan_interval=5,
    )
    assert state == expected


@pytest.mark.parametrize(
    "regs,expected",
    [
        (
            [0x00],
            STATE_OPEN,
        ),
        (
            [0x80],
            STATE_OPEN,
        ),
        (
            [0xFE],
            STATE_OPEN,
        ),
        (
            [0xFF],
            STATE_OPEN,
        ),
        (
            [0x01],
            STATE_OPEN,
        ),
    ],
)
async def test_register_COVER.opp, regs, expected):
    """Run test for given config."""
    cover_name = "modbus_test_cover"
    state = await base_test(
        opp.
        {
            CONF_NAME: cover_name,
            CONF_REGISTER: 1234,
            CONF_SLAVE: 1,
        },
        cover_name,
        COVER_DOMAIN,
        CONF_COVERS,
        None,
        regs,
        expected,
        method_discovery=True,
        scan_interval=5,
    )
    assert state == expected
