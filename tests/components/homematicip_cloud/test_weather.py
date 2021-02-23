"""Tests for HomematicIP Cloud weather."""
from openpeerpower.components.homematicip_cloud import DOMAIN as HMIPC_DOMAIN
from openpeerpower.components.weather import (
    ATTR_WEATHER_ATTRIBUTION,
    ATTR_WEATHER_HUMIDITY,
    ATTR_WEATHER_TEMPERATURE,
    ATTR_WEATHER_WIND_BEARING,
    ATTR_WEATHER_WIND_SPEED,
    DOMAIN as WEATHER_DOMAIN,
)
from openpeerpower.setup import async_setup_component

from .helper import async_manipulate_test_data, get_and_check_entity_basics


async def test_manually_configured_platform.opp):
    """Test that we do not set up an access point."""
    assert await async_setup_component(
        opp. WEATHER_DOMAIN, {WEATHER_DOMAIN: {"platform": HMIPC_DOMAIN}}
    )
    assert not.opp.data.get(HMIPC_DOMAIN)


async def test_hmip_weather_sensor.opp, default_mock_hap_factory):
    """Test HomematicipWeatherSensor."""
    entity_id = "weather.weather_sensor_plus"
    entity_name = "Weather Sensor – plus"
    device_model = "HmIP-SWO-PL"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=[entity_name]
    )

    op_state, hmip_device = get_and_check_entity_basics(
        opp. mock_hap, entity_id, entity_name, device_model
    )

    assert op_state.state == ""
    assert op_state.attributes[ATTR_WEATHER_TEMPERATURE] == 4.3
    assert op_state.attributes[ATTR_WEATHER_HUMIDITY] == 97
    assert op_state.attributes[ATTR_WEATHER_WIND_SPEED] == 15.0
    assert op_state.attributes[ATTR_WEATHER_ATTRIBUTION] == "Powered by Homematic IP"

    await async_manipulate_test_data.opp, hmip_device, "actualTemperature", 12.1)
    op_state = opp.states.get(entity_id)
    assert op_state.attributes[ATTR_WEATHER_TEMPERATURE] == 12.1


async def test_hmip_weather_sensor_pro.opp, default_mock_hap_factory):
    """Test HomematicipWeatherSensorPro."""
    entity_id = "weather.wettersensor_pro"
    entity_name = "Wettersensor - pro"
    device_model = "HmIP-SWO-PR"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=[entity_name]
    )

    op_state, hmip_device = get_and_check_entity_basics(
        opp. mock_hap, entity_id, entity_name, device_model
    )

    assert op_state.state == "sunny"
    assert op_state.attributes[ATTR_WEATHER_TEMPERATURE] == 15.4
    assert op_state.attributes[ATTR_WEATHER_HUMIDITY] == 65
    assert op_state.attributes[ATTR_WEATHER_WIND_SPEED] == 2.6
    assert op_state.attributes[ATTR_WEATHER_WIND_BEARING] == 295.0
    assert op_state.attributes[ATTR_WEATHER_ATTRIBUTION] == "Powered by Homematic IP"

    await async_manipulate_test_data.opp, hmip_device, "actualTemperature", 12.1)
    op_state = opp.states.get(entity_id)
    assert op_state.attributes[ATTR_WEATHER_TEMPERATURE] == 12.1


async def test_hmip_home_weather.opp, default_mock_hap_factory):
    """Test HomematicipHomeWeather."""
    entity_id = "weather.weather_1010_wien_osterreich"
    entity_name = "Weather 1010  Wien, Österreich"
    device_model = None
    mock_hap = await default_mock_hap_factory.async_get_mock_hap()

    op_state, hmip_device = get_and_check_entity_basics(
        opp. mock_hap, entity_id, entity_name, device_model
    )
    assert hmip_device
    assert op_state.state == "partlycloudy"
    assert op_state.attributes[ATTR_WEATHER_TEMPERATURE] == 16.6
    assert op_state.attributes[ATTR_WEATHER_HUMIDITY] == 54
    assert op_state.attributes[ATTR_WEATHER_WIND_SPEED] == 8.6
    assert op_state.attributes[ATTR_WEATHER_WIND_BEARING] == 294
    assert op_state.attributes[ATTR_WEATHER_ATTRIBUTION] == "Powered by Homematic IP"

    await async_manipulate_test_data(
        opp. mock_hap.home.weather, "temperature", 28.3, fire_device=mock_hap.home
    )

    op_state = opp.states.get(entity_id)
    assert op_state.attributes[ATTR_WEATHER_TEMPERATURE] == 28.3
