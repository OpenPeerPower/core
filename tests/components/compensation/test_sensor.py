"""The tests for the integration sensor platform."""

from openpeerpower.components.compensation.const import CONF_PRECISION, DOMAIN
from openpeerpower.components.compensation.sensor import ATTR_COEFFICIENTS
from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    EVENT_OPENPEERPOWER_START,
    EVENT_STATE_CHANGED,
    STATE_UNKNOWN,
)
from openpeerpower.setup import async_setup_component


async def test_linear_state(opp):
    """Test compensation sensor state."""
    config = {
        "compensation": {
            "test": {
                "source": "sensor.uncompensated",
                "data_points": [
                    [1.0, 2.0],
                    [2.0, 3.0],
                ],
                "precision": 2,
                "unit_of_measurement": "a",
            }
        }
    }
    expected_entity_id = "sensor.compensation_sensor_uncompensated"

    assert await async_setup_component(opp, DOMAIN, config)
    assert await async_setup_component(opp, SENSOR_DOMAIN, config)
    await opp.async_block_till_done()

    opp.bus.async_fire(EVENT_OPENPEERPOWER_START)
    entity_id = config[DOMAIN]["test"]["source"]
    opp.states.async_set(entity_id, 4, {})
    await opp.async_block_till_done()

    state = opp.states.get(expected_entity_id)
    assert state is not None

    assert round(float(state.state), config[DOMAIN]["test"][CONF_PRECISION]) == 5.0

    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "a"

    coefs = [round(v, 1) for v in state.attributes.get(ATTR_COEFFICIENTS)]
    assert coefs == [1.0, 1.0]

    opp.states.async_set(entity_id, "foo", {})
    await opp.async_block_till_done()

    state = opp.states.get(expected_entity_id)
    assert state is not None

    assert state.state == STATE_UNKNOWN


async def test_linear_state_from_attribute(opp):
    """Test compensation sensor state that pulls from attribute."""
    config = {
        "compensation": {
            "test": {
                "source": "sensor.uncompensated",
                "attribute": "value",
                "data_points": [
                    [1.0, 2.0],
                    [2.0, 3.0],
                ],
                "precision": 2,
            }
        }
    }
    expected_entity_id = "sensor.compensation_sensor_uncompensated_value"

    assert await async_setup_component(opp, DOMAIN, config)
    assert await async_setup_component(opp, SENSOR_DOMAIN, config)
    await opp.async_block_till_done()

    opp.bus.async_fire(EVENT_OPENPEERPOWER_START)

    entity_id = config[DOMAIN]["test"]["source"]
    opp.states.async_set(entity_id, 3, {"value": 4})
    await opp.async_block_till_done()

    state = opp.states.get(expected_entity_id)
    assert state is not None

    assert round(float(state.state), config[DOMAIN]["test"][CONF_PRECISION]) == 5.0

    coefs = [round(v, 1) for v in state.attributes.get(ATTR_COEFFICIENTS)]
    assert coefs == [1.0, 1.0]

    opp.states.async_set(entity_id, 3, {"value": "bar"})
    await opp.async_block_till_done()

    state = opp.states.get(expected_entity_id)
    assert state is not None

    assert state.state == STATE_UNKNOWN


async def test_quadratic_state(opp):
    """Test 3 degree polynominial compensation sensor."""
    config = {
        "compensation": {
            "test": {
                "source": "sensor.temperature",
                "data_points": [
                    [50, 3.3],
                    [50, 2.8],
                    [50, 2.9],
                    [70, 2.3],
                    [70, 2.6],
                    [70, 2.1],
                    [80, 2.5],
                    [80, 2.9],
                    [80, 2.4],
                    [90, 3.0],
                    [90, 3.1],
                    [90, 2.8],
                    [100, 3.3],
                    [100, 3.5],
                    [100, 3.0],
                ],
                "degree": 2,
                "precision": 3,
            }
        }
    }
    assert await async_setup_component(opp, DOMAIN, config)
    await opp.async_block_till_done()
    await opp.async_start()
    await opp.async_block_till_done()

    entity_id = config[DOMAIN]["test"]["source"]
    opp.states.async_set(entity_id, 43.2, {})
    await opp.async_block_till_done()

    state = opp.states.get("sensor.compensation_sensor_temperature")

    assert state is not None

    assert round(float(state.state), config[DOMAIN]["test"][CONF_PRECISION]) == 3.327


async def test_numpy_errors(opp, caplog):
    """Tests bad polyfits."""
    config = {
        "compensation": {
            "test": {
                "source": "sensor.uncompensated",
                "data_points": [
                    [1.0, 1.0],
                    [1.0, 1.0],
                ],
            },
            "test2": {
                "source": "sensor.uncompensated2",
                "data_points": [
                    [0.0, 1.0],
                    [0.0, 1.0],
                ],
            },
        }
    }
    await async_setup_component(opp, DOMAIN, config)
    await opp.async_block_till_done()
    await opp.async_start()
    await opp.async_block_till_done()

    assert "polyfit may be poorly conditioned" in caplog.text

    assert "invalid value encountered in true_divide" in caplog.text


async def test_datapoints_greater_than_degree(opp, caplog):
    """Tests 3 bad data points."""
    config = {
        "compensation": {
            "test": {
                "source": "sensor.uncompensated",
                "data_points": [
                    [1.0, 2.0],
                    [2.0, 3.0],
                ],
                "degree": 2,
            },
        }
    }
    await async_setup_component(opp, DOMAIN, config)
    await opp.async_block_till_done()
    await opp.async_start()
    await opp.async_block_till_done()

    assert "data_points must have at least 3 data_points" in caplog.text


async def test_new_state_is_none(opp):
    """Tests catch for empty new states."""
    config = {
        "compensation": {
            "test": {
                "source": "sensor.uncompensated",
                "data_points": [
                    [1.0, 2.0],
                    [2.0, 3.0],
                ],
                "precision": 2,
                "unit_of_measurement": "a",
            }
        }
    }
    expected_entity_id = "sensor.compensation_sensor_uncompensated"

    await async_setup_component(opp, DOMAIN, config)
    await opp.async_block_till_done()
    await opp.async_start()
    await opp.async_block_till_done()

    last_changed = opp.states.get(expected_entity_id).last_changed

    opp.bus.async_fire(
        EVENT_STATE_CHANGED, event_data={"entity_id": "sensor.uncompensated"}
    )

    assert last_changed == opp.states.get(expected_entity_id).last_changed
