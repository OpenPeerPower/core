"""The tests for the Weather component."""
from openpeerpower.components import weather
from openpeerpower.components.weather import (
    ATTR_FORECAST,
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_PRECIPITATION,
    ATTR_FORECAST_PRECIPITATION_PROBABILITY,
    ATTR_FORECAST_TEMP,
    ATTR_FORECAST_TEMP_LOW,
    ATTR_WEATHER_ATTRIBUTION,
    ATTR_WEATHER_HUMIDITY,
    ATTR_WEATHER_OZONE,
    ATTR_WEATHER_PRESSURE,
    ATTR_WEATHER_TEMPERATURE,
    ATTR_WEATHER_WIND_BEARING,
    ATTR_WEATHER_WIND_SPEED,
)
from openpeerpower.setup import async_setup_component
from openpeerpower.util.unit_system import METRIC_SYSTEM


async def test_attributes.opp):
    """Test weather attributes."""
    assert await async_setup_component(
       .opp, weather.DOMAIN, {"weather": {"platform": "demo"}}
    )
   .opp.config.units = METRIC_SYSTEM
    await opp.async_block_till_done()

    state = opp.states.get("weather.demo_weather_south")
    assert state is not None

    assert state.state == "sunny"

    data = state.attributes
    assert data.get(ATTR_WEATHER_TEMPERATURE) == 21.6
    assert data.get(ATTR_WEATHER_HUMIDITY) == 92
    assert data.get(ATTR_WEATHER_PRESSURE) == 1099
    assert data.get(ATTR_WEATHER_WIND_SPEED) == 0.5
    assert data.get(ATTR_WEATHER_WIND_BEARING) is None
    assert data.get(ATTR_WEATHER_OZONE) is None
    assert data.get(ATTR_WEATHER_ATTRIBUTION) == "Powered by Open Peer Power"
    assert data.get(ATTR_FORECAST)[0].get(ATTR_FORECAST_CONDITION) == "rainy"
    assert data.get(ATTR_FORECAST)[0].get(ATTR_FORECAST_PRECIPITATION) == 1
    assert data.get(ATTR_FORECAST)[0].get(ATTR_FORECAST_PRECIPITATION_PROBABILITY) == 60
    assert data.get(ATTR_FORECAST)[0].get(ATTR_FORECAST_TEMP) == 22
    assert data.get(ATTR_FORECAST)[0].get(ATTR_FORECAST_TEMP_LOW) == 15
    assert data.get(ATTR_FORECAST)[6].get(ATTR_FORECAST_CONDITION) == "fog"
    assert data.get(ATTR_FORECAST)[6].get(ATTR_FORECAST_PRECIPITATION) == 0.2
    assert data.get(ATTR_FORECAST)[6].get(ATTR_FORECAST_TEMP) == 21
    assert data.get(ATTR_FORECAST)[6].get(ATTR_FORECAST_TEMP_LOW) == 12
    assert (
        data.get(ATTR_FORECAST)[6].get(ATTR_FORECAST_PRECIPITATION_PROBABILITY) == 100
    )
    assert len(data.get(ATTR_FORECAST)) == 7


async def test_temperature_convert.opp):
    """Test temperature conversion."""
    assert await async_setup_component(
       .opp, weather.DOMAIN, {"weather": {"platform": "demo"}}
    )
   .opp.config.units = METRIC_SYSTEM
    await opp.async_block_till_done()

    state = opp.states.get("weather.demo_weather_north")
    assert state is not None

    assert state.state == "rainy"

    data = state.attributes
    assert data.get(ATTR_WEATHER_TEMPERATURE) == -24
