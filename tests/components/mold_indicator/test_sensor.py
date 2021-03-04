"""The tests for the MoldIndicator sensor."""
import pytest

from openpeerpower.components.mold_indicator.sensor import (
    ATTR_CRITICAL_TEMP,
    ATTR_DEWPOINT,
)
import openpeerpower.components.sensor as sensor
from openpeerpower.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    PERCENTAGE,
    STATE_UNKNOWN,
    TEMP_CELSIUS,
)
from openpeerpower.setup import async_setup_component


@pytest.fixture(autouse=True)
def init_sensors_fixture(opp):
    """Set up things to be run when tests are started."""
    opp.states.async_set(
        "test.indoortemp", "20", {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS}
    )
    opp.states.async_set(
        "test.outdoortemp", "10", {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS}
    )
    opp.states.async_set(
        "test.indoorhumidity", "50", {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE}
    )


async def test_setup(opp):
    """Test the mold indicator sensor setup."""
    assert await async_setup_component(
        opp,
        sensor.DOMAIN,
        {
            "sensor": {
                "platform": "mold_indicator",
                "indoor_temp_sensor": "test.indoortemp",
                "outdoor_temp_sensor": "test.outdoortemp",
                "indoor_humidity_sensor": "test.indoorhumidity",
                "calibration_factor": 2.0,
            }
        },
    )
    await opp.async_block_till_done()
    moldind = opp.states.get("sensor.mold_indicator")
    assert moldind
    assert PERCENTAGE == moldind.attributes.get("unit_of_measurement")


async def test_invalidcalib(opp):
    """Test invalid sensor values."""
    opp.states.async_set(
        "test.indoortemp", "10", {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS}
    )
    opp.states.async_set(
        "test.outdoortemp", "10", {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS}
    )
    opp.states.async_set(
        "test.indoorhumidity", "0", {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE}
    )

    assert await async_setup_component(
        opp,
        sensor.DOMAIN,
        {
            "sensor": {
                "platform": "mold_indicator",
                "indoor_temp_sensor": "test.indoortemp",
                "outdoor_temp_sensor": "test.outdoortemp",
                "indoor_humidity_sensor": "test.indoorhumidity",
                "calibration_factor": 0,
            }
        },
    )
    await opp.async_block_till_done()
    await opp.async_start()
    await opp.async_block_till_done()
    moldind = opp.states.get("sensor.mold_indicator")
    assert moldind
    assert moldind.state == "unavailable"
    assert moldind.attributes.get(ATTR_DEWPOINT) is None
    assert moldind.attributes.get(ATTR_CRITICAL_TEMP) is None


async def test_invalidhum(opp):
    """Test invalid sensor values."""
    opp.states.async_set(
        "test.indoortemp", "10", {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS}
    )
    opp.states.async_set(
        "test.outdoortemp", "10", {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS}
    )
    opp.states.async_set(
        "test.indoorhumidity", "-1", {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE}
    )

    assert await async_setup_component(
        opp,
        sensor.DOMAIN,
        {
            "sensor": {
                "platform": "mold_indicator",
                "indoor_temp_sensor": "test.indoortemp",
                "outdoor_temp_sensor": "test.outdoortemp",
                "indoor_humidity_sensor": "test.indoorhumidity",
                "calibration_factor": 2.0,
            }
        },
    )

    await opp.async_block_till_done()
    await opp.async_start()
    await opp.async_block_till_done()
    moldind = opp.states.get("sensor.mold_indicator")
    assert moldind
    assert moldind.state == "unavailable"
    assert moldind.attributes.get(ATTR_DEWPOINT) is None
    assert moldind.attributes.get(ATTR_CRITICAL_TEMP) is None

    opp.states.async_set(
        "test.indoorhumidity", "A", {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE}
    )
    await opp.async_block_till_done()
    moldind = opp.states.get("sensor.mold_indicator")
    assert moldind
    assert moldind.state == "unavailable"
    assert moldind.attributes.get(ATTR_DEWPOINT) is None
    assert moldind.attributes.get(ATTR_CRITICAL_TEMP) is None

    opp.states.async_set(
        "test.indoorhumidity", "10", {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS}
    )
    await opp.async_block_till_done()
    moldind = opp.states.get("sensor.mold_indicator")
    assert moldind
    assert moldind.state == "unavailable"
    assert moldind.attributes.get(ATTR_DEWPOINT) is None
    assert moldind.attributes.get(ATTR_CRITICAL_TEMP) is None


async def test_calculation(opp):
    """Test the mold indicator internal calculations."""
    assert await async_setup_component(
        opp,
        sensor.DOMAIN,
        {
            "sensor": {
                "platform": "mold_indicator",
                "indoor_temp_sensor": "test.indoortemp",
                "outdoor_temp_sensor": "test.outdoortemp",
                "indoor_humidity_sensor": "test.indoorhumidity",
                "calibration_factor": 2.0,
            }
        },
    )
    await opp.async_block_till_done()
    await opp.async_start()
    await opp.async_block_till_done()
    moldind = opp.states.get("sensor.mold_indicator")
    assert moldind

    # assert dewpoint
    dewpoint = moldind.attributes.get(ATTR_DEWPOINT)
    assert dewpoint
    assert dewpoint > 9.2
    assert dewpoint < 9.3

    # assert temperature estimation
    esttemp = moldind.attributes.get(ATTR_CRITICAL_TEMP)
    assert esttemp
    assert esttemp > 14.9
    assert esttemp < 15.1

    # assert mold indicator value
    state = moldind.state
    assert state
    assert state == "68"


async def test_unknown_sensor(opp):
    """Test the sensor_changed function."""
    assert await async_setup_component(
        opp,
        sensor.DOMAIN,
        {
            "sensor": {
                "platform": "mold_indicator",
                "indoor_temp_sensor": "test.indoortemp",
                "outdoor_temp_sensor": "test.outdoortemp",
                "indoor_humidity_sensor": "test.indoorhumidity",
                "calibration_factor": 2.0,
            }
        },
    )
    await opp.async_block_till_done()
    await opp.async_start()

    opp.states.async_set(
        "test.indoortemp", STATE_UNKNOWN, {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS}
    )
    await opp.async_block_till_done()
    moldind = opp.states.get("sensor.mold_indicator")
    assert moldind
    assert moldind.state == "unavailable"
    assert moldind.attributes.get(ATTR_DEWPOINT) is None
    assert moldind.attributes.get(ATTR_CRITICAL_TEMP) is None

    opp.states.async_set(
        "test.indoortemp", "30", {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS}
    )
    opp.states.async_set(
        "test.outdoortemp", STATE_UNKNOWN, {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS}
    )
    await opp.async_block_till_done()
    moldind = opp.states.get("sensor.mold_indicator")
    assert moldind
    assert moldind.state == "unavailable"
    assert moldind.attributes.get(ATTR_DEWPOINT) is None
    assert moldind.attributes.get(ATTR_CRITICAL_TEMP) is None

    opp.states.async_set(
        "test.outdoortemp", "25", {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS}
    )
    opp.states.async_set(
        "test.indoorhumidity",
        STATE_UNKNOWN,
        {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE},
    )
    await opp.async_block_till_done()
    moldind = opp.states.get("sensor.mold_indicator")
    assert moldind
    assert moldind.state == "unavailable"
    assert moldind.attributes.get(ATTR_DEWPOINT) is None
    assert moldind.attributes.get(ATTR_CRITICAL_TEMP) is None

    opp.states.async_set(
        "test.indoorhumidity", "20", {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE}
    )
    await opp.async_block_till_done()
    moldind = opp.states.get("sensor.mold_indicator")
    assert moldind
    assert moldind.state == "23"

    dewpoint = moldind.attributes.get(ATTR_DEWPOINT)
    assert dewpoint
    assert dewpoint > 4.5
    assert dewpoint < 4.6

    esttemp = moldind.attributes.get(ATTR_CRITICAL_TEMP)
    assert esttemp
    assert esttemp == 27.5


async def test_sensor_changed(opp):
    """Test the sensor_changed function."""
    assert await async_setup_component(
        opp,
        sensor.DOMAIN,
        {
            "sensor": {
                "platform": "mold_indicator",
                "indoor_temp_sensor": "test.indoortemp",
                "outdoor_temp_sensor": "test.outdoortemp",
                "indoor_humidity_sensor": "test.indoorhumidity",
                "calibration_factor": 2.0,
            }
        },
    )
    await opp.async_block_till_done()
    await opp.async_start()

    opp.states.async_set(
        "test.indoortemp", "30", {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS}
    )
    await opp.async_block_till_done()
    assert opp.states.get("sensor.mold_indicator").state == "90"

    opp.states.async_set(
        "test.outdoortemp", "25", {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS}
    )
    await opp.async_block_till_done()
    assert opp.states.get("sensor.mold_indicator").state == "57"

    opp.states.async_set(
        "test.indoorhumidity", "20", {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE}
    )
    await opp.async_block_till_done()
    assert opp.states.get("sensor.mold_indicator").state == "23"
