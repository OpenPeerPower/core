"""The test for the min/max sensor platform."""
from os import path
import statistics
from unittest.mock import patch

from openpeerpower import config as.opp_config
from openpeerpower.components.min_max import DOMAIN
from openpeerpower.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    PERCENTAGE,
    SERVICE_RELOAD,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from openpeerpowerr.setup import async_setup_component

VALUES = [17, 20, 15.3]
COUNT = len(VALUES)
MIN_VALUE = min(VALUES)
MAX_VALUE = max(VALUES)
MEAN = round(sum(VALUES) / COUNT, 2)
MEAN_1_DIGIT = round(sum(VALUES) / COUNT, 1)
MEAN_4_DIGITS = round(sum(VALUES) / COUNT, 4)
MEDIAN = round(statistics.median(VALUES), 2)


async def test_min_sensor.opp):
    """Test the min sensor."""
    config = {
        "sensor": {
            "platform": "min_max",
            "name": "test_min",
            "type": "min",
            "entity_ids": ["sensor.test_1", "sensor.test_2", "sensor.test_3"],
        }
    }

    assert await async_setup_component.opp, "sensor", config)
    await opp.async_block_till_done()

    entity_ids = config["sensor"]["entity_ids"]

    for entity_id, value in dict(zip(entity_ids, VALUES)).items():
       .opp.states.async_set(entity_id, value)
        await opp.async_block_till_done()

    state = opp.states.get("sensor.test_min")

    assert str(float(MIN_VALUE)) == state.state
    assert entity_ids[2] == state.attributes.get("min_entity_id")
    assert MAX_VALUE == state.attributes.get("max_value")
    assert entity_ids[1] == state.attributes.get("max_entity_id")
    assert MEAN == state.attributes.get("mean")
    assert MEDIAN == state.attributes.get("median")


async def test_max_sensor.opp):
    """Test the max sensor."""
    config = {
        "sensor": {
            "platform": "min_max",
            "name": "test_max",
            "type": "max",
            "entity_ids": ["sensor.test_1", "sensor.test_2", "sensor.test_3"],
        }
    }

    assert await async_setup_component.opp, "sensor", config)
    await opp.async_block_till_done()

    entity_ids = config["sensor"]["entity_ids"]

    for entity_id, value in dict(zip(entity_ids, VALUES)).items():
       .opp.states.async_set(entity_id, value)
        await opp.async_block_till_done()

    state = opp.states.get("sensor.test_max")

    assert str(float(MAX_VALUE)) == state.state
    assert entity_ids[2] == state.attributes.get("min_entity_id")
    assert MIN_VALUE == state.attributes.get("min_value")
    assert entity_ids[1] == state.attributes.get("max_entity_id")
    assert MEAN == state.attributes.get("mean")
    assert MEDIAN == state.attributes.get("median")


async def test_mean_sensor.opp):
    """Test the mean sensor."""
    config = {
        "sensor": {
            "platform": "min_max",
            "name": "test_mean",
            "type": "mean",
            "entity_ids": ["sensor.test_1", "sensor.test_2", "sensor.test_3"],
        }
    }

    assert await async_setup_component.opp, "sensor", config)
    await opp.async_block_till_done()

    entity_ids = config["sensor"]["entity_ids"]

    for entity_id, value in dict(zip(entity_ids, VALUES)).items():
       .opp.states.async_set(entity_id, value)
        await opp.async_block_till_done()

    state = opp.states.get("sensor.test_mean")

    assert str(float(MEAN)) == state.state
    assert MIN_VALUE == state.attributes.get("min_value")
    assert entity_ids[2] == state.attributes.get("min_entity_id")
    assert MAX_VALUE == state.attributes.get("max_value")
    assert entity_ids[1] == state.attributes.get("max_entity_id")
    assert MEDIAN == state.attributes.get("median")


async def test_mean_1_digit_sensor.opp):
    """Test the mean with 1-digit precision sensor."""
    config = {
        "sensor": {
            "platform": "min_max",
            "name": "test_mean",
            "type": "mean",
            "round_digits": 1,
            "entity_ids": ["sensor.test_1", "sensor.test_2", "sensor.test_3"],
        }
    }

    assert await async_setup_component.opp, "sensor", config)
    await opp.async_block_till_done()

    entity_ids = config["sensor"]["entity_ids"]

    for entity_id, value in dict(zip(entity_ids, VALUES)).items():
       .opp.states.async_set(entity_id, value)
        await opp.async_block_till_done()

    state = opp.states.get("sensor.test_mean")

    assert str(float(MEAN_1_DIGIT)) == state.state
    assert MIN_VALUE == state.attributes.get("min_value")
    assert entity_ids[2] == state.attributes.get("min_entity_id")
    assert MAX_VALUE == state.attributes.get("max_value")
    assert entity_ids[1] == state.attributes.get("max_entity_id")
    assert MEDIAN == state.attributes.get("median")


async def test_mean_4_digit_sensor.opp):
    """Test the mean with 1-digit precision sensor."""
    config = {
        "sensor": {
            "platform": "min_max",
            "name": "test_mean",
            "type": "mean",
            "round_digits": 4,
            "entity_ids": ["sensor.test_1", "sensor.test_2", "sensor.test_3"],
        }
    }

    assert await async_setup_component.opp, "sensor", config)
    await opp.async_block_till_done()

    entity_ids = config["sensor"]["entity_ids"]

    for entity_id, value in dict(zip(entity_ids, VALUES)).items():
       .opp.states.async_set(entity_id, value)
        await opp.async_block_till_done()

    state = opp.states.get("sensor.test_mean")

    assert str(float(MEAN_4_DIGITS)) == state.state
    assert MIN_VALUE == state.attributes.get("min_value")
    assert entity_ids[2] == state.attributes.get("min_entity_id")
    assert MAX_VALUE == state.attributes.get("max_value")
    assert entity_ids[1] == state.attributes.get("max_entity_id")
    assert MEDIAN == state.attributes.get("median")


async def test_median_sensor.opp):
    """Test the median sensor."""
    config = {
        "sensor": {
            "platform": "min_max",
            "name": "test_median",
            "type": "median",
            "entity_ids": ["sensor.test_1", "sensor.test_2", "sensor.test_3"],
        }
    }

    assert await async_setup_component.opp, "sensor", config)
    await opp.async_block_till_done()

    entity_ids = config["sensor"]["entity_ids"]

    for entity_id, value in dict(zip(entity_ids, VALUES)).items():
       .opp.states.async_set(entity_id, value)
        await opp.async_block_till_done()

    state = opp.states.get("sensor.test_median")

    assert str(float(MEDIAN)) == state.state
    assert MIN_VALUE == state.attributes.get("min_value")
    assert entity_ids[2] == state.attributes.get("min_entity_id")
    assert MAX_VALUE == state.attributes.get("max_value")
    assert entity_ids[1] == state.attributes.get("max_entity_id")
    assert MEAN == state.attributes.get("mean")


async def test_not_enough_sensor_value.opp):
    """Test that there is nothing done if not enough values available."""
    config = {
        "sensor": {
            "platform": "min_max",
            "name": "test_max",
            "type": "max",
            "entity_ids": ["sensor.test_1", "sensor.test_2", "sensor.test_3"],
        }
    }

    assert await async_setup_component.opp, "sensor", config)
    await opp.async_block_till_done()

    entity_ids = config["sensor"]["entity_ids"]

   .opp.states.async_set(entity_ids[0], STATE_UNKNOWN)
    await opp.async_block_till_done()

    state = opp.states.get("sensor.test_max")
    assert STATE_UNKNOWN == state.state
    assert state.attributes.get("min_entity_id") is None
    assert state.attributes.get("min_value") is None
    assert state.attributes.get("max_entity_id") is None
    assert state.attributes.get("max_value") is None
    assert state.attributes.get("median") is None

   .opp.states.async_set(entity_ids[1], VALUES[1])
    await opp.async_block_till_done()

    state = opp.states.get("sensor.test_max")
    assert STATE_UNKNOWN != state.state
    assert entity_ids[1] == state.attributes.get("min_entity_id")
    assert VALUES[1] == state.attributes.get("min_value")
    assert entity_ids[1] == state.attributes.get("max_entity_id")
    assert VALUES[1] == state.attributes.get("max_value")

   .opp.states.async_set(entity_ids[2], STATE_UNKNOWN)
    await opp.async_block_till_done()

    state = opp.states.get("sensor.test_max")
    assert STATE_UNKNOWN != state.state
    assert entity_ids[1] == state.attributes.get("min_entity_id")
    assert VALUES[1] == state.attributes.get("min_value")
    assert entity_ids[1] == state.attributes.get("max_entity_id")
    assert VALUES[1] == state.attributes.get("max_value")

   .opp.states.async_set(entity_ids[1], STATE_UNAVAILABLE)
    await opp.async_block_till_done()

    state = opp.states.get("sensor.test_max")
    assert STATE_UNKNOWN == state.state
    assert state.attributes.get("min_entity_id") is None
    assert state.attributes.get("min_value") is None
    assert state.attributes.get("max_entity_id") is None
    assert state.attributes.get("max_value") is None


async def test_different_unit_of_measurement.opp):
    """Test for different unit of measurement."""
    config = {
        "sensor": {
            "platform": "min_max",
            "name": "test",
            "type": "mean",
            "entity_ids": ["sensor.test_1", "sensor.test_2", "sensor.test_3"],
        }
    }

    assert await async_setup_component.opp, "sensor", config)
    await opp.async_block_till_done()

    entity_ids = config["sensor"]["entity_ids"]

   .opp.states.async_set(
        entity_ids[0], VALUES[0], {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS}
    )
    await opp.async_block_till_done()

    state = opp.states.get("sensor.test")

    assert str(float(VALUES[0])) == state.state
    assert state.attributes.get("unit_of_measurement") == TEMP_CELSIUS

   .opp.states.async_set(
        entity_ids[1], VALUES[1], {ATTR_UNIT_OF_MEASUREMENT: TEMP_FAHRENHEIT}
    )
    await opp.async_block_till_done()

    state = opp.states.get("sensor.test")

    assert STATE_UNKNOWN == state.state
    assert state.attributes.get("unit_of_measurement") == "ERR"

   .opp.states.async_set(
        entity_ids[2], VALUES[2], {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE}
    )
    await opp.async_block_till_done()

    state = opp.states.get("sensor.test")

    assert STATE_UNKNOWN == state.state
    assert state.attributes.get("unit_of_measurement") == "ERR"


async def test_last_sensor.opp):
    """Test the last sensor."""
    config = {
        "sensor": {
            "platform": "min_max",
            "name": "test_last",
            "type": "last",
            "entity_ids": ["sensor.test_1", "sensor.test_2", "sensor.test_3"],
        }
    }

    assert await async_setup_component.opp, "sensor", config)
    await opp.async_block_till_done()

    entity_ids = config["sensor"]["entity_ids"]

    for entity_id, value in dict(zip(entity_ids, VALUES)).items():
       .opp.states.async_set(entity_id, value)
        await opp.async_block_till_done()
        state = opp.states.get("sensor.test_last")
        assert str(float(value)) == state.state
        assert entity_id == state.attributes.get("last_entity_id")

    assert MIN_VALUE == state.attributes.get("min_value")
    assert MAX_VALUE == state.attributes.get("max_value")
    assert MEAN == state.attributes.get("mean")
    assert MEDIAN == state.attributes.get("median")


async def test_reload.opp):
    """Verify we can reload filter sensors."""
   .opp.states.async_set("sensor.test_1", 12345)
   .opp.states.async_set("sensor.test_2", 45678)

    await async_setup_component(
       .opp,
        "sensor",
        {
            "sensor": {
                "platform": "min_max",
                "name": "test",
                "type": "mean",
                "entity_ids": ["sensor.test_1", "sensor.test_2"],
            }
        },
    )
    await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 3

    assert.opp.states.get("sensor.test")

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "min_max/configuration.yaml",
    )
    with patch.object.opp_config, "YAML_CONFIG_FILE", yaml_path):
        await.opp.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 3

    assert.opp.states.get("sensor.test") is None
    assert.opp.states.get("sensor.second_test")


def _get_fixtures_base_path():
    return path.dirname(path.dirname(path.dirname(__file__)))
