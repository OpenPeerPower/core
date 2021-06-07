"""The test for the threshold sensor platform."""

from openpeerpower.const import ATTR_UNIT_OF_MEASUREMENT, STATE_UNKNOWN, TEMP_CELSIUS
from openpeerpower.setup import async_setup_component


async def test_sensor_upper(opp):
    """Test if source is above threshold."""
    config = {
        "binary_sensor": {
            "platform": "threshold",
            "upper": "15",
            "entity_id": "sensor.test_monitored",
        }
    }

    assert await async_setup_component(opp, "binary_sensor", config)
    await opp.async_block_till_done()

    opp.states.async_set(
        "sensor.test_monitored", 16, {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS}
    )
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.attributes.get("entity_id") == "sensor.test_monitored"
    assert state.attributes.get("sensor_value") == 16
    assert state.attributes.get("position") == "above"
    assert state.attributes.get("upper") == float(config["binary_sensor"]["upper"])
    assert state.attributes.get("hysteresis") == 0.0
    assert state.attributes.get("type") == "upper"

    assert state.state == "on"

    opp.states.async_set("sensor.test_monitored", 14)
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.state == "off"

    opp.states.async_set("sensor.test_monitored", 15)
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.state == "off"


async def test_sensor_lower(opp):
    """Test if source is below threshold."""
    config = {
        "binary_sensor": {
            "platform": "threshold",
            "lower": "15",
            "entity_id": "sensor.test_monitored",
        }
    }

    assert await async_setup_component(opp, "binary_sensor", config)
    await opp.async_block_till_done()

    opp.states.async_set("sensor.test_monitored", 16)
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.attributes.get("position") == "above"
    assert state.attributes.get("lower") == float(config["binary_sensor"]["lower"])
    assert state.attributes.get("hysteresis") == 0.0
    assert state.attributes.get("type") == "lower"

    assert state.state == "off"

    opp.states.async_set("sensor.test_monitored", 14)
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.state == "on"


async def test_sensor_hysteresis(opp):
    """Test if source is above threshold using hysteresis."""
    config = {
        "binary_sensor": {
            "platform": "threshold",
            "upper": "15",
            "hysteresis": "2.5",
            "entity_id": "sensor.test_monitored",
        }
    }

    assert await async_setup_component(opp, "binary_sensor", config)
    await opp.async_block_till_done()

    opp.states.async_set("sensor.test_monitored", 20)
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.attributes.get("position") == "above"
    assert state.attributes.get("upper") == float(config["binary_sensor"]["upper"])
    assert state.attributes.get("hysteresis") == 2.5
    assert state.attributes.get("type") == "upper"

    assert state.state == "on"

    opp.states.async_set("sensor.test_monitored", 13)
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.state == "on"

    opp.states.async_set("sensor.test_monitored", 12)
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.state == "off"

    opp.states.async_set("sensor.test_monitored", 17)
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.state == "off"

    opp.states.async_set("sensor.test_monitored", 18)
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.state == "on"


async def test_sensor_in_range_no_hysteresis(opp):
    """Test if source is within the range."""
    config = {
        "binary_sensor": {
            "platform": "threshold",
            "lower": "10",
            "upper": "20",
            "entity_id": "sensor.test_monitored",
        }
    }

    assert await async_setup_component(opp, "binary_sensor", config)
    await opp.async_block_till_done()

    opp.states.async_set(
        "sensor.test_monitored", 16, {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS}
    )
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.attributes.get("entity_id") == "sensor.test_monitored"
    assert state.attributes.get("sensor_value") == 16
    assert state.attributes.get("position") == "in_range"
    assert state.attributes.get("lower") == float(config["binary_sensor"]["lower"])
    assert state.attributes.get("upper") == float(config["binary_sensor"]["upper"])
    assert state.attributes.get("hysteresis") == 0.0
    assert state.attributes.get("type") == "range"

    assert state.state == "on"

    opp.states.async_set("sensor.test_monitored", 9)
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.attributes.get("position") == "below"
    assert state.state == "off"

    opp.states.async_set("sensor.test_monitored", 21)
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.attributes.get("position") == "above"
    assert state.state == "off"


async def test_sensor_in_range_with_hysteresis(opp):
    """Test if source is within the range."""
    config = {
        "binary_sensor": {
            "platform": "threshold",
            "lower": "10",
            "upper": "20",
            "hysteresis": "2",
            "entity_id": "sensor.test_monitored",
        }
    }

    assert await async_setup_component(opp, "binary_sensor", config)
    await opp.async_block_till_done()

    opp.states.async_set(
        "sensor.test_monitored", 16, {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS}
    )
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.attributes.get("entity_id") == "sensor.test_monitored"
    assert state.attributes.get("sensor_value") == 16
    assert state.attributes.get("position") == "in_range"
    assert state.attributes.get("lower") == float(config["binary_sensor"]["lower"])
    assert state.attributes.get("upper") == float(config["binary_sensor"]["upper"])
    assert state.attributes.get("hysteresis") == float(
        config["binary_sensor"]["hysteresis"]
    )
    assert state.attributes.get("type") == "range"

    assert state.state == "on"

    opp.states.async_set("sensor.test_monitored", 8)
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.attributes.get("position") == "in_range"
    assert state.state == "on"

    opp.states.async_set("sensor.test_monitored", 7)
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.attributes.get("position") == "below"
    assert state.state == "off"

    opp.states.async_set("sensor.test_monitored", 12)
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.attributes.get("position") == "below"
    assert state.state == "off"

    opp.states.async_set("sensor.test_monitored", 13)
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.attributes.get("position") == "in_range"
    assert state.state == "on"

    opp.states.async_set("sensor.test_monitored", 22)
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.attributes.get("position") == "in_range"
    assert state.state == "on"

    opp.states.async_set("sensor.test_monitored", 23)
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.attributes.get("position") == "above"
    assert state.state == "off"

    opp.states.async_set("sensor.test_monitored", 18)
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.attributes.get("position") == "above"
    assert state.state == "off"

    opp.states.async_set("sensor.test_monitored", 17)
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.attributes.get("position") == "in_range"
    assert state.state == "on"


async def test_sensor_in_range_unknown_state(opp):
    """Test if source is within the range."""
    config = {
        "binary_sensor": {
            "platform": "threshold",
            "lower": "10",
            "upper": "20",
            "entity_id": "sensor.test_monitored",
        }
    }

    assert await async_setup_component(opp, "binary_sensor", config)
    await opp.async_block_till_done()

    opp.states.async_set(
        "sensor.test_monitored", 16, {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS}
    )
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.attributes.get("entity_id") == "sensor.test_monitored"
    assert state.attributes.get("sensor_value") == 16
    assert state.attributes.get("position") == "in_range"
    assert state.attributes.get("lower") == float(config["binary_sensor"]["lower"])
    assert state.attributes.get("upper") == float(config["binary_sensor"]["upper"])
    assert state.attributes.get("hysteresis") == 0.0
    assert state.attributes.get("type") == "range"

    assert state.state == "on"

    opp.states.async_set("sensor.test_monitored", STATE_UNKNOWN)
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.attributes.get("position") == "unknown"
    assert state.state == "off"


async def test_sensor_lower_zero_threshold(opp):
    """Test if a lower threshold of zero is set."""
    config = {
        "binary_sensor": {
            "platform": "threshold",
            "lower": "0",
            "entity_id": "sensor.test_monitored",
        }
    }

    assert await async_setup_component(opp, "binary_sensor", config)
    await opp.async_block_till_done()

    opp.states.async_set("sensor.test_monitored", 16)
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.attributes.get("type") == "lower"
    assert state.attributes.get("lower") == float(config["binary_sensor"]["lower"])

    assert state.state == "off"

    opp.states.async_set("sensor.test_monitored", -3)
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.state == "on"


async def test_sensor_upper_zero_threshold(opp):
    """Test if an upper threshold of zero is set."""
    config = {
        "binary_sensor": {
            "platform": "threshold",
            "upper": "0",
            "entity_id": "sensor.test_monitored",
        }
    }

    assert await async_setup_component(opp, "binary_sensor", config)
    await opp.async_block_till_done()

    opp.states.async_set("sensor.test_monitored", -10)
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.attributes.get("type") == "upper"
    assert state.attributes.get("upper") == float(config["binary_sensor"]["upper"])

    assert state.state == "off"

    opp.states.async_set("sensor.test_monitored", 2)
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.threshold")

    assert state.state == "on"
