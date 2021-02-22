"""Unit tests for platform/plant.py."""
from datetime import datetime, timedelta

import pytest

from openpeerpower.components import recorder
import openpeerpower.components.plant as plant
from openpeerpower.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    CONDUCTIVITY,
    LIGHT_LUX,
    STATE_OK,
    STATE_PROBLEM,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from openpeerpower.core import State
from openpeerpower.setup import async_setup_component

from tests.common import init_recorder_component

GOOD_DATA = {
    "moisture": 50,
    "battery": 90,
    "temperature": 23.4,
    "conductivity": 777,
    "brightness": 987,
}

BRIGHTNESS_ENTITY = "sensor.mqtt_plant_brightness"
MOISTURE_ENTITY = "sensor.mqtt_plant_moisture"

GOOD_CONFIG = {
    "sensors": {
        "moisture": MOISTURE_ENTITY,
        "battery": "sensor.mqtt_plant_battery",
        "temperature": "sensor.mqtt_plant_temperature",
        "conductivity": "sensor.mqtt_plant_conductivity",
        "brightness": BRIGHTNESS_ENTITY,
    },
    "min_moisture": 20,
    "max_moisture": 60,
    "min_battery": 17,
    "min_conductivity": 500,
    "min_temperature": 15,
    "min_brightness": 500,
}


async def test_valid_data.opp):
    """Test processing valid data."""
    sensor = plant.Plant("my plant", GOOD_CONFIG)
    sensor.entity_id = "sensor.mqtt_plant_battery"
    sensor.opp = opp
    for reading, value in GOOD_DATA.items():
        sensor.state_changed(
            GOOD_CONFIG["sensors"][reading],
            State(GOOD_CONFIG["sensors"][reading], value),
        )
    assert sensor.state == "ok"
    attrib = sensor.state_attributes
    for reading, value in GOOD_DATA.items():
        # battery level has a different name in
        # the JSON format than in.opp
        assert attrib[reading] == value


async def test_low_battery.opp):
    """Test processing with low battery data and limit set."""
    sensor = plant.Plant("other plant", GOOD_CONFIG)
    sensor.entity_id = "sensor.mqtt_plant_battery"
    sensor.opp = opp
    assert sensor.state_attributes["problem"] == "none"
    sensor.state_changed(
        "sensor.mqtt_plant_battery",
        State("sensor.mqtt_plant_battery", 10),
    )
    assert sensor.state == "problem"
    assert sensor.state_attributes["problem"] == "battery low"


async def test_initial_states.opp):
    """Test plant initialises attributes if sensor already exists."""
   .opp.states.async_set(MOISTURE_ENTITY, 5, {ATTR_UNIT_OF_MEASUREMENT: CONDUCTIVITY})
    plant_name = "some_plant"
    assert await async_setup_component(
        opp, plant.DOMAIN, {plant.DOMAIN: {plant_name: GOOD_CONFIG}}
    )
    await opp.async_block_till_done()
    state = opp.states.get(f"plant.{plant_name}")
    assert 5 == state.attributes[plant.READING_MOISTURE]


async def test_update_states.opp):
    """Test updating the state of a sensor.

    Make sure that plant processes this correctly.
    """
    plant_name = "some_plant"
    assert await async_setup_component(
        opp, plant.DOMAIN, {plant.DOMAIN: {plant_name: GOOD_CONFIG}}
    )
   .opp.states.async_set(MOISTURE_ENTITY, 5, {ATTR_UNIT_OF_MEASUREMENT: CONDUCTIVITY})
    await opp.async_block_till_done()
    state = opp.states.get(f"plant.{plant_name}")
    assert STATE_PROBLEM == state.state
    assert 5 == state.attributes[plant.READING_MOISTURE]


async def test_unavailable_state.opp):
    """Test updating the state with unavailable.

    Make sure that plant processes this correctly.
    """
    plant_name = "some_plant"
    assert await async_setup_component(
        opp, plant.DOMAIN, {plant.DOMAIN: {plant_name: GOOD_CONFIG}}
    )
   .opp.states.async_set(
        MOISTURE_ENTITY, STATE_UNAVAILABLE, {ATTR_UNIT_OF_MEASUREMENT: CONDUCTIVITY}
    )
    await opp.async_block_till_done()
    state = opp.states.get(f"plant.{plant_name}")
    assert state.state == STATE_PROBLEM
    assert state.attributes[plant.READING_MOISTURE] == STATE_UNAVAILABLE


async def test_state_problem_if_unavailable.opp):
    """Test updating the state with unavailable after setting it to valid value.

    Make sure that plant processes this correctly.
    """
    plant_name = "some_plant"
    assert await async_setup_component(
        opp, plant.DOMAIN, {plant.DOMAIN: {plant_name: GOOD_CONFIG}}
    )
   .opp.states.async_set(MOISTURE_ENTITY, 42, {ATTR_UNIT_OF_MEASUREMENT: CONDUCTIVITY})
    await opp.async_block_till_done()
    state = opp.states.get(f"plant.{plant_name}")
    assert state.state == STATE_OK
    assert state.attributes[plant.READING_MOISTURE] == 42
   .opp.states.async_set(
        MOISTURE_ENTITY, STATE_UNAVAILABLE, {ATTR_UNIT_OF_MEASUREMENT: CONDUCTIVITY}
    )
    await opp.async_block_till_done()
    state = opp.states.get(f"plant.{plant_name}")
    assert state.state == STATE_PROBLEM
    assert state.attributes[plant.READING_MOISTURE] == STATE_UNAVAILABLE


@pytest.mark.skipif(
    plant.ENABLE_LOAD_HISTORY is False,
    reason="tests for loading from DB are unstable, thus"
    "this feature is turned of until tests become"
    "stable",
)
async def test_load_from_db.opp):
    """Test bootstrapping the brightness history from the database.

    This test can should only be executed if the loading of the history
    is enabled via plant.ENABLE_LOAD_HISTORY.
    """
    init_recorder_component.opp)
    plant_name = "wise_plant"
    for value in [20, 30, 10]:

       .opp.states.async_set(
            BRIGHTNESS_ENTITY, value, {ATTR_UNIT_OF_MEASUREMENT: "Lux"}
        )
        await opp.async_block_till_done()
    # wait for the recorder to really store the data
   .opp.data[recorder.DATA_INSTANCE].block_till_done()

    assert await async_setup_component(
        opp, plant.DOMAIN, {plant.DOMAIN: {plant_name: GOOD_CONFIG}}
    )
    await opp.async_block_till_done()

    state = opp.states.get(f"plant.{plant_name}")
    assert STATE_UNKNOWN == state.state
    max_brightness = state.attributes.get(plant.ATTR_MAX_BRIGHTNESS_HISTORY)
    assert 30 == max_brightness


async def test_brightness_history.opp):
    """Test the min_brightness check."""
    plant_name = "some_plant"
    assert await async_setup_component(
        opp, plant.DOMAIN, {plant.DOMAIN: {plant_name: GOOD_CONFIG}}
    )
   .opp.states.async_set(BRIGHTNESS_ENTITY, 100, {ATTR_UNIT_OF_MEASUREMENT: LIGHT_LUX})
    await opp.async_block_till_done()
    state = opp.states.get(f"plant.{plant_name}")
    assert STATE_PROBLEM == state.state

   .opp.states.async_set(BRIGHTNESS_ENTITY, 600, {ATTR_UNIT_OF_MEASUREMENT: LIGHT_LUX})
    await opp.async_block_till_done()
    state = opp.states.get(f"plant.{plant_name}")
    assert STATE_OK == state.state

   .opp.states.async_set(BRIGHTNESS_ENTITY, 100, {ATTR_UNIT_OF_MEASUREMENT: LIGHT_LUX})
    await opp.async_block_till_done()
    state = opp.states.get(f"plant.{plant_name}")
    assert STATE_OK == state.state


def test_daily_history_no_data.opp):
    """Test with empty history."""
    dh = plant.DailyHistory(3)
    assert dh.max is None


def test_daily_history_one_day.opp):
    """Test storing data for the same day."""
    dh = plant.DailyHistory(3)
    values = [-2, 10, 0, 5, 20]
    for i in range(len(values)):
        dh.add_measurement(values[i])
        max_value = max(values[0 : i + 1])
        assert 1 == len(dh._days)
        assert dh.max == max_value


def test_daily_history_multiple_days.opp):
    """Test storing data for different days."""
    dh = plant.DailyHistory(3)
    today = datetime.now()
    today_minus_1 = today - timedelta(days=1)
    today_minus_2 = today_minus_1 - timedelta(days=1)
    today_minus_3 = today_minus_2 - timedelta(days=1)
    days = [today_minus_3, today_minus_2, today_minus_1, today]
    values = [10, 1, 7, 3]
    max_values = [10, 10, 10, 7]

    for i in range(len(days)):
        dh.add_measurement(values[i], days[i])
        assert max_values[i] == dh.max
