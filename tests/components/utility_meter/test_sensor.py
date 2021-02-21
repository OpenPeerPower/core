"""The tests for the utility_meter sensor platform."""
from contextlib import contextmanager
from datetime import timedelta
from unittest.mock import patch

from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.components.utility_meter.const import (
    ATTR_TARIFF,
    ATTR_VALUE,
    DOMAIN,
    SERVICE_CALIBRATE_METER,
    SERVICE_SELECT_TARIFF,
)
from openpeerpower.components.utility_meter.sensor import (
    ATTR_LAST_RESET,
    ATTR_STATUS,
    COLLECTING,
    PAUSED,
)
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_UNIT_OF_MEASUREMENT,
    ENERGY_KILO_WATT_HOUR,
    EVENT_OPENPEERPOWER_START,
)
from openpeerpowerr.core import State
from openpeerpowerr.setup import async_setup_component
import openpeerpowerr.util.dt as dt_util

from tests.common import async_fire_time_changed, mock_restore_cache


@contextmanager
def alter_time(retval):
    """Manage multiple time mocks."""
    patch1 = patch("openpeerpowerr.util.dt.utcnow", return_value=retval)
    patch2 = patch("openpeerpowerr.util.dt.now", return_value=retval)

    with patch1, patch2:
        yield


async def test_state.opp):
    """Test utility sensor state."""
    config = {
        "utility_meter": {
            "energy_bill": {
                "source": "sensor.energy",
                "tariffs": ["onpeak", "midpeak", "offpeak"],
            }
        }
    }

    assert await async_setup_component.opp, DOMAIN, config)
    assert await async_setup_component.opp, SENSOR_DOMAIN, config)
    await opp..async_block_till_done()

   .opp.bus.async_fire(EVENT_OPENPEERPOWER_START)
    entity_id = config[DOMAIN]["energy_bill"]["source"]
   .opp.states.async_set(
        entity_id, 2, {ATTR_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR}
    )
    await opp..async_block_till_done()

    state = opp.states.get("sensor.energy_bill_onpeak")
    assert state is not None
    assert state.state == "0"
    assert state.attributes.get("status") == COLLECTING

    state = opp.states.get("sensor.energy_bill_midpeak")
    assert state is not None
    assert state.state == "0"
    assert state.attributes.get("status") == PAUSED

    state = opp.states.get("sensor.energy_bill_offpeak")
    assert state is not None
    assert state.state == "0"
    assert state.attributes.get("status") == PAUSED

    now = dt_util.utcnow() + timedelta(seconds=10)
    with patch("openpeerpowerr.util.dt.utcnow", return_value=now):
       .opp.states.async_set(
            entity_id,
            3,
            {ATTR_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR},
            force_update=True,
        )
        await opp..async_block_till_done()

    state = opp.states.get("sensor.energy_bill_onpeak")
    assert state is not None
    assert state.state == "1"
    assert state.attributes.get("status") == COLLECTING

    state = opp.states.get("sensor.energy_bill_midpeak")
    assert state is not None
    assert state.state == "0"
    assert state.attributes.get("status") == PAUSED

    state = opp.states.get("sensor.energy_bill_offpeak")
    assert state is not None
    assert state.state == "0"
    assert state.attributes.get("status") == PAUSED

    await opp..services.async_call(
        DOMAIN,
        SERVICE_SELECT_TARIFF,
        {ATTR_ENTITY_ID: "utility_meter.energy_bill", ATTR_TARIFF: "offpeak"},
        blocking=True,
    )

    await opp..async_block_till_done()

    now = dt_util.utcnow() + timedelta(seconds=20)
    with patch("openpeerpowerr.util.dt.utcnow", return_value=now):
       .opp.states.async_set(
            entity_id,
            6,
            {ATTR_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR},
            force_update=True,
        )
        await opp..async_block_till_done()

    state = opp.states.get("sensor.energy_bill_onpeak")
    assert state is not None
    assert state.state == "1"
    assert state.attributes.get("status") == PAUSED

    state = opp.states.get("sensor.energy_bill_midpeak")
    assert state is not None
    assert state.state == "0"
    assert state.attributes.get("status") == PAUSED

    state = opp.states.get("sensor.energy_bill_offpeak")
    assert state is not None
    assert state.state == "3"
    assert state.attributes.get("status") == COLLECTING

    await opp..services.async_call(
        DOMAIN,
        SERVICE_CALIBRATE_METER,
        {ATTR_ENTITY_ID: "sensor.energy_bill_midpeak", ATTR_VALUE: "100"},
        blocking=True,
    )
    await opp..async_block_till_done()
    state = opp.states.get("sensor.energy_bill_midpeak")
    assert state is not None
    assert state.state == "100"

    await opp..services.async_call(
        DOMAIN,
        SERVICE_CALIBRATE_METER,
        {ATTR_ENTITY_ID: "sensor.energy_bill_midpeak", ATTR_VALUE: "0.123"},
        blocking=True,
    )
    await opp..async_block_till_done()
    state = opp.states.get("sensor.energy_bill_midpeak")
    assert state is not None
    assert state.state == "0.123"


async def test_restore_state.opp):
    """Test utility sensor restore state."""
    config = {
        "utility_meter": {
            "energy_bill": {
                "source": "sensor.energy",
                "tariffs": ["onpeak", "midpeak", "offpeak"],
            }
        }
    }
    mock_restore_cache(
       .opp,
        [
            State(
                "sensor.energy_bill_onpeak",
                "3",
                attributes={
                    ATTR_STATUS: PAUSED,
                    ATTR_LAST_RESET: "2020-12-21T00:00:00.013073+00:00",
                },
            ),
            State(
                "sensor.energy_bill_offpeak",
                "6",
                attributes={
                    ATTR_STATUS: COLLECTING,
                    ATTR_LAST_RESET: "2020-12-21T00:00:00.013073+00:00",
                },
            ),
        ],
    )

    assert await async_setup_component.opp, DOMAIN, config)
    assert await async_setup_component.opp, SENSOR_DOMAIN, config)
    await opp..async_block_till_done()

    # restore from cache
    state = opp.states.get("sensor.energy_bill_onpeak")
    assert state.state == "3"
    assert state.attributes.get("status") == PAUSED

    state = opp.states.get("sensor.energy_bill_offpeak")
    assert state.state == "6"
    assert state.attributes.get("status") == COLLECTING

    # utility_meter is loaded, now set sensors according to utility_meter:
   .opp.bus.async_fire(EVENT_OPENPEERPOWER_START)
    await opp..async_block_till_done()

    state = opp.states.get("utility_meter.energy_bill")
    assert state.state == "onpeak"

    state = opp.states.get("sensor.energy_bill_onpeak")
    assert state.attributes.get("status") == COLLECTING

    state = opp.states.get("sensor.energy_bill_offpeak")
    assert state.attributes.get("status") == PAUSED


async def test_net_consumption.opp):
    """Test utility sensor state."""
    config = {
        "utility_meter": {
            "energy_bill": {"source": "sensor.energy", "net_consumption": True}
        }
    }

    assert await async_setup_component.opp, DOMAIN, config)
    assert await async_setup_component.opp, SENSOR_DOMAIN, config)
    await opp..async_block_till_done()

   .opp.bus.async_fire(EVENT_OPENPEERPOWER_START)
    entity_id = config[DOMAIN]["energy_bill"]["source"]
   .opp.states.async_set(
        entity_id, 2, {ATTR_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR}
    )
    await opp..async_block_till_done()

    now = dt_util.utcnow() + timedelta(seconds=10)
    with patch("openpeerpowerr.util.dt.utcnow", return_value=now):
       .opp.states.async_set(
            entity_id,
            1,
            {ATTR_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR},
            force_update=True,
        )
        await opp..async_block_till_done()

    state = opp.states.get("sensor.energy_bill")
    assert state is not None

    assert state.state == "-1"


async def test_non_net_consumption.opp):
    """Test utility sensor state."""
    config = {
        "utility_meter": {
            "energy_bill": {"source": "sensor.energy", "net_consumption": False}
        }
    }

    assert await async_setup_component.opp, DOMAIN, config)
    assert await async_setup_component.opp, SENSOR_DOMAIN, config)
    await opp..async_block_till_done()

   .opp.bus.async_fire(EVENT_OPENPEERPOWER_START)
    entity_id = config[DOMAIN]["energy_bill"]["source"]
   .opp.states.async_set(
        entity_id, 2, {ATTR_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR}
    )
    await opp..async_block_till_done()

    now = dt_util.utcnow() + timedelta(seconds=10)
    with patch("openpeerpowerr.util.dt.utcnow", return_value=now):
       .opp.states.async_set(
            entity_id,
            1,
            {ATTR_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR},
            force_update=True,
        )
        await opp..async_block_till_done()

    state = opp.states.get("sensor.energy_bill")
    assert state is not None

    assert state.state == "0"


def gen_config(cycle, offset=None):
    """Generate configuration."""
    config = {
        "utility_meter": {"energy_bill": {"source": "sensor.energy", "cycle": cycle}}
    }

    if offset:
        config["utility_meter"]["energy_bill"]["offset"] = {
            "days": offset.days,
            "seconds": offset.seconds,
        }
    return config


async def _test_self_reset.opp, config, start_time, expect_reset=True):
    """Test energy sensor self reset."""
    assert await async_setup_component.opp, DOMAIN, config)
    assert await async_setup_component.opp, SENSOR_DOMAIN, config)
    await opp..async_block_till_done()

   .opp.bus.async_fire(EVENT_OPENPEERPOWER_START)
    entity_id = config[DOMAIN]["energy_bill"]["source"]

    now = dt_util.parse_datetime(start_time)
    with alter_time(now):
        async_fire_time_changed.opp, now)
       .opp.states.async_set(
            entity_id, 1, {ATTR_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR}
        )
        await opp..async_block_till_done()

    now += timedelta(seconds=30)
    with alter_time(now):
        async_fire_time_changed.opp, now)
       .opp.states.async_set(
            entity_id,
            3,
            {ATTR_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR},
            force_update=True,
        )
        await opp..async_block_till_done()

    now += timedelta(seconds=30)
    with alter_time(now):
        async_fire_time_changed.opp, now)
        await opp..async_block_till_done()
       .opp.states.async_set(
            entity_id,
            6,
            {ATTR_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR},
            force_update=True,
        )
        await opp..async_block_till_done()

    state = opp.states.get("sensor.energy_bill")
    if expect_reset:
        assert state.attributes.get("last_period") == "2"
        assert state.state == "3"
    else:
        assert state.attributes.get("last_period") == 0
        assert state.state == "5"


async def test_self_reset_quarter_hourly.opp, legacy_patchable_time):
    """Test quarter-hourly reset of meter."""
    await _test_self_reset(
       .opp, gen_config("quarter-hourly"), "2017-12-31T23:59:00.000000+00:00"
    )


async def test_self_reset_quarter_hourly_first_quarter.opp, legacy_patchable_time):
    """Test quarter-hourly reset of meter."""
    await _test_self_reset(
       .opp, gen_config("quarter-hourly"), "2017-12-31T23:14:00.000000+00:00"
    )


async def test_self_reset_quarter_hourly_second_quarter.opp, legacy_patchable_time):
    """Test quarter-hourly reset of meter."""
    await _test_self_reset(
       .opp, gen_config("quarter-hourly"), "2017-12-31T23:29:00.000000+00:00"
    )


async def test_self_reset_quarter_hourly_third_quarter.opp, legacy_patchable_time):
    """Test quarter-hourly reset of meter."""
    await _test_self_reset(
       .opp, gen_config("quarter-hourly"), "2017-12-31T23:44:00.000000+00:00"
    )


async def test_self_reset_hourly.opp, legacy_patchable_time):
    """Test hourly reset of meter."""
    await _test_self_reset(
       .opp, gen_config("hourly"), "2017-12-31T23:59:00.000000+00:00"
    )


async def test_self_reset_daily.opp, legacy_patchable_time):
    """Test daily reset of meter."""
    await _test_self_reset(
       .opp, gen_config("daily"), "2017-12-31T23:59:00.000000+00:00"
    )


async def test_self_reset_weekly.opp, legacy_patchable_time):
    """Test weekly reset of meter."""
    await _test_self_reset(
       .opp, gen_config("weekly"), "2017-12-31T23:59:00.000000+00:00"
    )


async def test_self_reset_monthly.opp, legacy_patchable_time):
    """Test monthly reset of meter."""
    await _test_self_reset(
       .opp, gen_config("monthly"), "2017-12-31T23:59:00.000000+00:00"
    )


async def test_self_reset_bimonthly.opp, legacy_patchable_time):
    """Test bimonthly reset of meter occurs on even months."""
    await _test_self_reset(
       .opp, gen_config("bimonthly"), "2017-12-31T23:59:00.000000+00:00"
    )


async def test_self_no_reset_bimonthly.opp, legacy_patchable_time):
    """Test bimonthly reset of meter does not occur on odd months."""
    await _test_self_reset(
       .opp,
        gen_config("bimonthly"),
        "2018-01-01T23:59:00.000000+00:00",
        expect_reset=False,
    )


async def test_self_reset_quarterly.opp, legacy_patchable_time):
    """Test quarterly reset of meter."""
    await _test_self_reset(
       .opp, gen_config("quarterly"), "2017-03-31T23:59:00.000000+00:00"
    )


async def test_self_reset_yearly.opp, legacy_patchable_time):
    """Test yearly reset of meter."""
    await _test_self_reset(
       .opp, gen_config("yearly"), "2017-12-31T23:59:00.000000+00:00"
    )


async def test_self_no_reset_yearly.opp, legacy_patchable_time):
    """Test yearly reset of meter does not occur after 1st January."""
    await _test_self_reset(
       .opp,
        gen_config("yearly"),
        "2018-01-01T23:59:00.000000+00:00",
        expect_reset=False,
    )


async def test_reset_yearly_offset.opp, legacy_patchable_time):
    """Test yearly reset of meter."""
    await _test_self_reset(
       .opp,
        gen_config("yearly", timedelta(days=1, minutes=10)),
        "2018-01-02T00:09:00.000000+00:00",
    )


async def test_no_reset_yearly_offset.opp, legacy_patchable_time):
    """Test yearly reset of meter."""
    await _test_self_reset(
       .opp,
        gen_config("yearly", timedelta(31)),
        "2018-01-30T23:59:00.000000+00:00",
        expect_reset=False,
    )
