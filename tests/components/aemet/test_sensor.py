"""The sensor tests for the AEMET OpenData platform."""

from unittest.mock import patch

from openpeerpower.components.weather import (
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_SNOWY,
)
from openpeerpower.const import STATE_UNKNOWN
import openpeerpower.util.dt as dt_util

from .util import async_init_integration


async def test_aemet_forecast_create_sensors.opp):
    """Test creation of forecast sensors."""

    now = dt_util.parse_datetime("2021-01-09 12:00:00+00:00")
    with patch("openpeerpower.util.dt.now", return_value=now), patch(
        "openpeerpower.util.dt.utcnow", return_value=now
    ):
        await async_init_integration.opp)

    state =.opp.states.get("sensor.aemet_daily_forecast_condition")
    assert state.state == ATTR_CONDITION_PARTLYCLOUDY

    state =.opp.states.get("sensor.aemet_daily_forecast_precipitation")
    assert state.state == STATE_UNKNOWN

    state =.opp.states.get("sensor.aemet_daily_forecast_precipitation_probability")
    assert state.state == "30"

    state =.opp.states.get("sensor.aemet_daily_forecast_temperature")
    assert state.state == "4"

    state =.opp.states.get("sensor.aemet_daily_forecast_temperature_low")
    assert state.state == "-4"

    state =.opp.states.get("sensor.aemet_daily_forecast_time")
    assert state.state == "2021-01-10 00:00:00+00:00"

    state =.opp.states.get("sensor.aemet_daily_forecast_wind_bearing")
    assert state.state == "45.0"

    state =.opp.states.get("sensor.aemet_daily_forecast_wind_speed")
    assert state.state == "20"

    state =.opp.states.get("sensor.aemet_hourly_forecast_condition")
    assert state is None

    state =.opp.states.get("sensor.aemet_hourly_forecast_precipitation")
    assert state is None

    state =.opp.states.get("sensor.aemet_hourly_forecast_precipitation_probability")
    assert state is None

    state =.opp.states.get("sensor.aemet_hourly_forecast_temperature")
    assert state is None

    state =.opp.states.get("sensor.aemet_hourly_forecast_temperature_low")
    assert state is None

    state =.opp.states.get("sensor.aemet_hourly_forecast_time")
    assert state is None

    state =.opp.states.get("sensor.aemet_hourly_forecast_wind_bearing")
    assert state is None

    state =.opp.states.get("sensor.aemet_hourly_forecast_wind_speed")
    assert state is None


async def test_aemet_weather_create_sensors.opp):
    """Test creation of weather sensors."""

    now = dt_util.parse_datetime("2021-01-09 12:00:00+00:00")
    with patch("openpeerpower.util.dt.now", return_value=now), patch(
        "openpeerpower.util.dt.utcnow", return_value=now
    ):
        await async_init_integration.opp)

    state =.opp.states.get("sensor.aemet_condition")
    assert state.state == ATTR_CONDITION_SNOWY

    state =.opp.states.get("sensor.aemet_humidity")
    assert state.state == "99.0"

    state =.opp.states.get("sensor.aemet_pressure")
    assert state.state == "1004.4"

    state =.opp.states.get("sensor.aemet_rain")
    assert state.state == "1.8"

    state =.opp.states.get("sensor.aemet_rain_probability")
    assert state.state == "100"

    state =.opp.states.get("sensor.aemet_snow")
    assert state.state == "1.8"

    state =.opp.states.get("sensor.aemet_snow_probability")
    assert state.state == "100"

    state =.opp.states.get("sensor.aemet_station_id")
    assert state.state == "3195"

    state =.opp.states.get("sensor.aemet_station_name")
    assert state.state == "MADRID RETIRO"

    state =.opp.states.get("sensor.aemet_station_timestamp")
    assert state.state == "2021-01-09T12:00:00+00:00"

    state =.opp.states.get("sensor.aemet_storm_probability")
    assert state.state == "0"

    state =.opp.states.get("sensor.aemet_temperature")
    assert state.state == "-0.7"

    state =.opp.states.get("sensor.aemet_temperature_feeling")
    assert state.state == "-4"

    state =.opp.states.get("sensor.aemet_town_id")
    assert state.state == "id28065"

    state =.opp.states.get("sensor.aemet_town_name")
    assert state.state == "Getafe"

    state =.opp.states.get("sensor.aemet_town_timestamp")
    assert state.state == "2021-01-09 11:47:45+00:00"

    state =.opp.states.get("sensor.aemet_wind_bearing")
    assert state.state == "90.0"

    state =.opp.states.get("sensor.aemet_wind_max_speed")
    assert state.state == "24"

    state =.opp.states.get("sensor.aemet_wind_speed")
    assert state.state == "15"
