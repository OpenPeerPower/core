"""The sensor tests for the tado platform."""

from .util import async_init_integration


async def test_air_con_create_sensors(opp):
    """Test creation of aircon sensors."""

    await async_init_integration(opp)

    state = opp.states.get("sensor.air_conditioning_tado_mode")
    assert state.state == "HOME"

    state = opp.states.get("sensor.air_conditioning_temperature")
    assert state.state == "24.76"

    state = opp.states.get("sensor.air_conditioning_ac")
    assert state.state == "ON"

    state = opp.states.get("sensor.air_conditioning_humidity")
    assert state.state == "60.9"


async def test_home_create_sensors(opp):
    """Test creation of home sensors."""

    await async_init_integration(opp)

    state = opp.states.get("sensor.home_name_outdoor_temperature")
    assert state.state == "7.46"

    state = opp.states.get("sensor.home_name_solar_percentage")
    assert state.state == "2.1"

    state = opp.states.get("sensor.home_name_weather_condition")
    assert state.state == "fog"


async def test_heater_create_sensors(opp):
    """Test creation of heater sensors."""

    await async_init_integration(opp)

    state = opp.states.get("sensor.baseboard_heater_tado_mode")
    assert state.state == "HOME"

    state = opp.states.get("sensor.baseboard_heater_temperature")
    assert state.state == "20.65"

    state = opp.states.get("sensor.baseboard_heater_humidity")
    assert state.state == "45.2"


async def test_water_heater_create_sensors(opp):
    """Test creation of water heater sensors."""

    await async_init_integration(opp)

    state = opp.states.get("sensor.water_heater_tado_mode")
    assert state.state == "HOME"
