"""Tests for rpi_power binary sensor."""
from datetime import timedelta
import logging
from unittest.mock import MagicMock

from openpeerpower.components.rpi_power.binary_sensor import (
    DESCRIPTION_NORMALIZED,
    DESCRIPTION_UNDER_VOLTAGE,
)
from openpeerpower.components.rpi_power.const import DOMAIN
from openpeerpower.const import STATE_OFF, STATE_ON
from openpeerpowerr.setup import async_setup_component
from openpeerpowerr.util import dt as dt_util

from tests.common import MockConfigEntry, async_fire_time_changed, patch

ENTITY_ID = "binary_sensor.rpi_power_status"

MODULE = "openpeerpower.components.rpi_power.binary_sensor.new_under_voltage"


async def _async_setup_component.opp, detected):
    mocked_under_voltage = MagicMock()
    type(mocked_under_voltage).get = MagicMock(return_value=detected)
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_opp.opp)
    with patch(MODULE, return_value=mocked_under_voltage):
        await async_setup_component.opp, DOMAIN, {DOMAIN: {}})
        await opp.async_block_till_done()
    return mocked_under_voltage


async def test_new.opp, caplog):
    """Test new entry."""
    await _async_setup_component.opp, False)
    state = opp.states.get(ENTITY_ID)
    assert state.state == STATE_OFF
    assert not any(x.levelno == logging.WARNING for x in caplog.records)


async def test_new_detected.opp, caplog):
    """Test new entry with under voltage detected."""
    mocked_under_voltage = await _async_setup_component.opp, True)
    state = opp.states.get(ENTITY_ID)
    assert state.state == STATE_ON
    assert (
        len(
            [
                x
                for x in caplog.records
                if x.levelno == logging.WARNING
                and x.message == DESCRIPTION_UNDER_VOLTAGE
            ]
        )
        == 1
    )

    # back to normal
    type(mocked_under_voltage).get = MagicMock(return_value=False)
    future = dt_util.utcnow() + timedelta(minutes=1)
    async_fire_time_changed.opp, future)
    await opp.async_block_till_done()
    state = opp.states.get(ENTITY_ID)
    assert (
        len(
            [
                x
                for x in caplog.records
                if x.levelno == logging.INFO and x.message == DESCRIPTION_NORMALIZED
            ]
        )
        == 1
    )
