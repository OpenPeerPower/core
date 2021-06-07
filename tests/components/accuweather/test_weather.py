"""Test weather of AccuWeather integration."""
from datetime import timedelta
import json
from unittest.mock import PropertyMock, patch

from openpeerpower.components.accuweather.const import ATTRIBUTION
from openpeerpower.components.weather import (
    ATTR_FORECAST,
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_PRECIPITATION,
    ATTR_FORECAST_PRECIPITATION_PROBABILITY,
    ATTR_FORECAST_TEMP,
    ATTR_FORECAST_TEMP_LOW,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_WIND_BEARING,
    ATTR_FORECAST_WIND_SPEED,
    ATTR_WEATHER_HUMIDITY,
    ATTR_WEATHER_OZONE,
    ATTR_WEATHER_PRESSURE,
    ATTR_WEATHER_TEMPERATURE,
    ATTR_WEATHER_VISIBILITY,
    ATTR_WEATHER_WIND_BEARING,
    ATTR_WEATHER_WIND_SPEED,
)
from openpeerpower.const import ATTR_ATTRIBUTION, ATTR_ENTITY_ID, STATE_UNAVAILABLE
from openpeerpower.helpers import entity_registry as er
from openpeerpower.setup import async_setup_component
from openpeerpower.util.dt import utcnow

from tests.common import async_fire_time_changed, load_fixture
from tests.components.accuweather import init_integration


async def test_weather_without_forecast(opp):
    """Test states of the weather without forecast."""
    await init_integration(opp)
    registry = er.async_get(opp)

    state = opp.states.get("weather.home")
    assert state
    assert state.state == "sunny"
    assert not state.attributes.get(ATTR_FORECAST)
    assert state.attributes.get(ATTR_WEATHER_HUMIDITY) == 67
    assert not state.attributes.get(ATTR_WEATHER_OZONE)
    assert state.attributes.get(ATTR_WEATHER_PRESSURE) == 1012.0
    assert state.attributes.get(ATTR_WEATHER_TEMPERATURE) == 22.6
    assert state.attributes.get(ATTR_WEATHER_VISIBILITY) == 16.1
    assert state.attributes.get(ATTR_WEATHER_WIND_BEARING) == 180
    assert state.attributes.get(ATTR_WEATHER_WIND_SPEED) == 14.5
    assert state.attributes.get(ATTR_ATTRIBUTION) == ATTRIBUTION

    entry = registry.async_get("weather.home")
    assert entry
    assert entry.unique_id == "0123456"


async def test_weather_with_forecast(opp):
    """Test states of the weather with forecast."""
    await init_integration(opp, forecast=True)
    registry = er.async_get(opp)

    state = opp.states.get("weather.home")
    assert state
    assert state.state == "sunny"
    assert state.attributes.get(ATTR_WEATHER_HUMIDITY) == 67
    assert state.attributes.get(ATTR_WEATHER_OZONE) == 32
    assert state.attributes.get(ATTR_WEATHER_PRESSURE) == 1012.0
    assert state.attributes.get(ATTR_WEATHER_TEMPERATURE) == 22.6
    assert state.attributes.get(ATTR_WEATHER_VISIBILITY) == 16.1
    assert state.attributes.get(ATTR_WEATHER_WIND_BEARING) == 180
    assert state.attributes.get(ATTR_WEATHER_WIND_SPEED) == 14.5
    assert state.attributes.get(ATTR_ATTRIBUTION) == ATTRIBUTION
    forecast = state.attributes.get(ATTR_FORECAST)[0]
    assert forecast.get(ATTR_FORECAST_CONDITION) == "lightning-rainy"
    assert forecast.get(ATTR_FORECAST_PRECIPITATION) == 4.8
    assert forecast.get(ATTR_FORECAST_PRECIPITATION_PROBABILITY) == 58
    assert forecast.get(ATTR_FORECAST_TEMP) == 29.5
    assert forecast.get(ATTR_FORECAST_TEMP_LOW) == 15.4
    assert forecast.get(ATTR_FORECAST_TIME) == "2020-07-26T05:00:00+00:00"
    assert forecast.get(ATTR_FORECAST_WIND_BEARING) == 166
    assert forecast.get(ATTR_FORECAST_WIND_SPEED) == 13.0

    entry = registry.async_get("weather.home")
    assert entry
    assert entry.unique_id == "0123456"


async def test_availability(opp):
    """Ensure that we mark the entities unavailable correctly when service is offline."""
    await init_integration(opp)

    state = opp.states.get("weather.home")
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "sunny"

    future = utcnow() + timedelta(minutes=60)
    with patch(
        "openpeerpower.components.accuweather.AccuWeather._async_get_data",
        side_effect=ConnectionError(),
    ):
        async_fire_time_changed(opp, future)
        await opp.async_block_till_done()

        state = opp.states.get("weather.home")
        assert state
        assert state.state == STATE_UNAVAILABLE

    future = utcnow() + timedelta(minutes=120)
    with patch(
        "openpeerpower.components.accuweather.AccuWeather.async_get_current_conditions",
        return_value=json.loads(
            load_fixture("accuweather/current_conditions_data.json")
        ),
    ), patch(
        "openpeerpower.components.accuweather.AccuWeather.requests_remaining",
        new_callable=PropertyMock,
        return_value=10,
    ):
        async_fire_time_changed(opp, future)
        await opp.async_block_till_done()

        state = opp.states.get("weather.home")
        assert state
        assert state.state != STATE_UNAVAILABLE
        assert state.state == "sunny"


async def test_manual_update_entity(opp):
    """Test manual update entity via service homeasasistant/update_entity."""
    await init_integration(opp, forecast=True)

    await async_setup_component(opp, "openpeerpower", {})

    current = json.loads(load_fixture("accuweather/current_conditions_data.json"))
    forecast = json.loads(load_fixture("accuweather/forecast_data.json"))

    with patch(
        "openpeerpower.components.accuweather.AccuWeather.async_get_current_conditions",
        return_value=current,
    ) as mock_current, patch(
        "openpeerpower.components.accuweather.AccuWeather.async_get_forecast",
        return_value=forecast,
    ) as mock_forecast, patch(
        "openpeerpower.components.accuweather.AccuWeather.requests_remaining",
        new_callable=PropertyMock,
        return_value=10,
    ):
        await opp.services.async_call(
            "openpeerpower",
            "update_entity",
            {ATTR_ENTITY_ID: ["weather.home"]},
            blocking=True,
        )
    assert mock_current.call_count == 1
    assert mock_forecast.call_count == 1


async def test_unsupported_condition_icon_data(opp):
    """Test with unsupported condition icon data."""
    await init_integration(opp, forecast=True, unsupported_icon=True)

    state = opp.states.get("weather.home")
    assert state.attributes.get(ATTR_FORECAST_CONDITION) is None
