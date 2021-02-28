"""The tests for the derivative sensor platform."""
from datetime import timedelta
from unittest.mock import patch

from openpeerpower.const import POWER_WATT, TIME_HOURS, TIME_MINUTES, TIME_SECONDS
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util


async def test_state(opp):
    """Test derivative sensor state."""
    config = {
        "sensor": {
            "platform": "derivative",
            "name": "derivative",
            "source": "sensor.energy",
            "unit": "kW",
            "round": 2,
        }
    }

    assert await async_setup_component(opp, "sensor", config)

    entity_id = config["sensor"]["source"]
    base = dt_util.utcnow()
    with patch("openpeerpower.util.dt.utcnow") as now:
        now.return_value = base
        opp.states.async_set(entity_id, 1, {})
        await opp.async_block_till_done()

        now.return_value += timedelta(seconds=3600)
        opp.states.async_set(entity_id, 1, {}, force_update=True)
        await opp.async_block_till_done()

    state = opp.states.get("sensor.derivative")
    assert state is not None

    # Testing a energy sensor at 1 kWh for 1hour = 0kW
    assert round(float(state.state), config["sensor"]["round"]) == 0.0

    assert state.attributes.get("unit_of_measurement") == "kW"


async def _setup_sensor(opp, config):
    default_config = {
        "platform": "derivative",
        "name": "power",
        "source": "sensor.energy",
        "round": 2,
    }

    config = {"sensor": dict(default_config, **config)}
    assert await async_setup_component(opp, "sensor", config)

    entity_id = config["sensor"]["source"]
    opp.states.async_set(entity_id, 0, {})
    await opp.async_block_till_done()

    return config, entity_id


async def setup_tests(opp, config, times, values, expected_state):
    """Test derivative sensor state."""
    config, entity_id = await _setup_sensor(opp, config)

    # Testing a energy sensor with non-monotonic intervals and values
    base = dt_util.utcnow()
    with patch("openpeerpower.util.dt.utcnow") as now:
        for time, value in zip(times, values):
            now.return_value = base + timedelta(seconds=time)
            opp.states.async_set(entity_id, value, {}, force_update=True)
            await opp.async_block_till_done()

    state = opp.states.get("sensor.power")
    assert state is not None

    assert round(float(state.state), config["sensor"]["round"]) == expected_state

    return state


async def test_dataSet1.opp):
    """Test derivative sensor state."""
    await setup_tests(
        opp,
        {"unit_time": TIME_SECONDS},
        times=[20, 30, 40, 50],
        values=[10, 30, 5, 0],
        expected_state=-0.5,
    )


async def test_dataSet2.opp):
    """Test derivative sensor state."""
    await setup_tests(
        opp,
        {"unit_time": TIME_SECONDS},
        times=[20, 30],
        values=[5, 0],
        expected_state=-0.5,
    )


async def test_dataSet3.opp):
    """Test derivative sensor state."""
    state = await setup_tests(
        opp,
        {"unit_time": TIME_SECONDS},
        times=[20, 30],
        values=[5, 10],
        expected_state=0.5,
    )

    assert state.attributes.get("unit_of_measurement") == f"/{TIME_SECONDS}"


async def test_dataSet4.opp):
    """Test derivative sensor state."""
    await setup_tests(
        opp,
        {"unit_time": TIME_SECONDS},
        times=[20, 30],
        values=[5, 5],
        expected_state=0,
    )


async def test_dataSet5.opp):
    """Test derivative sensor state."""
    await setup_tests(
        opp,
        {"unit_time": TIME_SECONDS},
        times=[20, 30],
        values=[10, -10],
        expected_state=-2,
    )


async def test_dataSet6.opp):
    """Test derivative sensor state."""
    await setup_tests(opp, {}, times=[0, 60], values=[0, 1 / 60], expected_state=1)


async def test_data_moving_average_for_discrete_sensor(opp):
    """Test derivative sensor state."""
    # We simulate the following situation:
    # The temperature rises 1 °C per minute for 30 minutes long.
    # There is a data point every 30 seconds, however, the sensor returns
    # the temperature rounded down to an integer value.
    # We use a time window of 10 minutes and therefore we can expect
    # (because the true derivative is 1 °C/min) an error of less than 10%.

    temperature_values = []
    for temperature in range(30):
        temperature_values += [temperature] * 2  # two values per minute
    time_window = 600
    times = list(range(0, 1800 + 30, 30))

    config, entity_id = await _setup_sensor(
        opp,
        {
            "time_window": {"seconds": time_window},
            "unit_time": TIME_MINUTES,
            "round": 1,
        },
    )  # two minute window

    base = dt_util.utcnow()
    for time, value in zip(times, temperature_values):
        now = base + timedelta(seconds=time)
        with patch("openpeerpower.util.dt.utcnow", return_value=now):
            opp.states.async_set(entity_id, value, {}, force_update=True)
            await opp.async_block_till_done()

        if time_window < time < times[-1] - time_window:
            state = opp.states.get("sensor.power")
            derivative = round(float(state.state), config["sensor"]["round"])
            # Test that the error is never more than
            # (time_window_in_minutes / true_derivative * 100) = 10% + ε
            assert abs(1 - derivative) <= 0.1 + 1e-6


async def test_prefix(opp):
    """Test derivative sensor state using a power source."""
    config = {
        "sensor": {
            "platform": "derivative",
            "name": "derivative",
            "source": "sensor.power",
            "round": 2,
            "unit_prefix": "k",
        }
    }

    assert await async_setup_component(opp, "sensor", config)

    entity_id = config["sensor"]["source"]
    base = dt_util.utcnow()
    with patch("openpeerpower.util.dt.utcnow") as now:
        now.return_value = base
        opp.states.async_set(
            entity_id, 1000, {"unit_of_measurement": POWER_WATT}, force_update=True
        )
        await opp.async_block_till_done()

        now.return_value += timedelta(seconds=3600)
        opp.states.async_set(
            entity_id, 1000, {"unit_of_measurement": POWER_WATT}, force_update=True
        )
        await opp.async_block_till_done()

    state = opp.states.get("sensor.derivative")
    assert state is not None

    # Testing a power sensor at 1000 Watts for 1hour = 0kW/h
    assert round(float(state.state), config["sensor"]["round"]) == 0.0
    assert state.attributes.get("unit_of_measurement") == f"kW/{TIME_HOURS}"


async def test_suffix(opp):
    """Test derivative sensor state using a network counter source."""
    config = {
        "sensor": {
            "platform": "derivative",
            "name": "derivative",
            "source": "sensor.bytes_per_second",
            "round": 2,
            "unit_prefix": "k",
            "unit_time": TIME_SECONDS,
        }
    }

    assert await async_setup_component(opp, "sensor", config)

    entity_id = config["sensor"]["source"]
    base = dt_util.utcnow()
    with patch("openpeerpower.util.dt.utcnow") as now:
        now.return_value = base
        opp.states.async_set(entity_id, 1000, {})
        await opp.async_block_till_done()

        now.return_value += timedelta(seconds=10)
        opp.states.async_set(entity_id, 1000, {}, force_update=True)
        await opp.async_block_till_done()

    state = opp.states.get("sensor.derivative")
    assert state is not None

    # Testing a network speed sensor at 1000 bytes/s over 10s  = 10kbytes/s2
    assert round(float(state.state), config["sensor"]["round"]) == 0.0
