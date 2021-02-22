"""Define tests for the OpenWeatherMap config flow."""
from unittest.mock import MagicMock, patch

from pyowm.commons.exceptions import APIRequestError, UnauthorizedError

from openpeerpower import data_entry_flow
from openpeerpower.components.openweathermap.const import (
    CONF_LANGUAGE,
    DEFAULT_FORECAST_MODE,
    DEFAULT_LANGUAGE,
    DOMAIN,
)
from openpeerpower.config_entries import SOURCE_USER
from openpeerpower.const import (
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_MODE,
    CONF_NAME,
)

from tests.common import MockConfigEntry

CONFIG = {
    CONF_NAME: "openweathermap",
    CONF_API_KEY: "foo",
    CONF_LATITUDE: 50,
    CONF_LONGITUDE: 40,
    CONF_MODE: DEFAULT_FORECAST_MODE,
    CONF_LANGUAGE: DEFAULT_LANGUAGE,
}

VALID_YAML_CONFIG = {CONF_API_KEY: "foo"}


async def test_form.opp):
    """Test that the form is served with valid input."""
    mocked_owm = _create_mocked_owm(True)

    with patch(
        "pyowm.weatherapi25.weather_manager.WeatherManager",
        return_value=mocked_owm,
    ):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == SOURCE_USER
        assert result["errors"] == {}

        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
        )

        await.opp.async_block_till_done()

        conf_entries =.opp.config_entries.async_entries(DOMAIN)
        entry = conf_entries[0]
        assert entry.state == "loaded"

        await.opp.config_entries.async_unload(conf_entries[0].entry_id)
        await.opp.async_block_till_done()
        assert entry.state == "not_loaded"

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == CONFIG[CONF_NAME]
        assert result["data"][CONF_LATITUDE] == CONFIG[CONF_LATITUDE]
        assert result["data"][CONF_LONGITUDE] == CONFIG[CONF_LONGITUDE]
        assert result["data"][CONF_API_KEY] == CONFIG[CONF_API_KEY]


async def test_form_options.opp):
    """Test that the options form."""
    mocked_owm = _create_mocked_owm(True)

    with patch(
        "pyowm.weatherapi25.weather_manager.WeatherManager",
        return_value=mocked_owm,
    ):
        config_entry = MockConfigEntry(
            domain=DOMAIN, unique_id="openweathermap_unique_id", data=CONFIG
        )
        config_entry.add_to.opp.opp)

        assert await.opp.config_entries.async_setup(config_entry.entry_id)
        await.opp.async_block_till_done()

        assert config_entry.state == "loaded"

        result = await.opp.config_entries.options.async_init(config_entry.entry_id)

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "init"

        result = await.opp.config_entries.options.async_configure(
            result["flow_id"], user_input={CONF_MODE: "daily"}
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert config_entry.options == {
            CONF_MODE: "daily",
            CONF_LANGUAGE: DEFAULT_LANGUAGE,
        }

        await.opp.async_block_till_done()

        assert config_entry.state == "loaded"

        result = await.opp.config_entries.options.async_init(config_entry.entry_id)

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "init"

        result = await.opp.config_entries.options.async_configure(
            result["flow_id"], user_input={CONF_MODE: "onecall_daily"}
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert config_entry.options == {
            CONF_MODE: "onecall_daily",
            CONF_LANGUAGE: DEFAULT_LANGUAGE,
        }

        await.opp.async_block_till_done()

        assert config_entry.state == "loaded"


async def test_form_invalid_api_key.opp):
    """Test that the form is served with no input."""
    mocked_owm = _create_mocked_owm(True)

    with patch(
        "pyowm.weatherapi25.weather_manager.WeatherManager",
        return_value=mocked_owm,
        side_effect=UnauthorizedError(""),
    ):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
        )

        assert result["errors"] == {"base": "invalid_api_key"}


async def test_form_api_call_error.opp):
    """Test setting up with api call error."""
    mocked_owm = _create_mocked_owm(True)

    with patch(
        "pyowm.weatherapi25.weather_manager.WeatherManager",
        return_value=mocked_owm,
        side_effect=APIRequestError(""),
    ):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
        )

        assert result["errors"] == {"base": "cannot_connect"}


async def test_form_api_offline.opp):
    """Test setting up with api call error."""
    mocked_owm = _create_mocked_owm(False)

    with patch(
        "openpeerpower.components.openweathermap.config_flow.OWM",
        return_value=mocked_owm,
    ):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
        )

        assert result["errors"] == {"base": "invalid_api_key"}


def _create_mocked_owm(is_api_online: bool):
    mocked_owm = MagicMock()

    weather = MagicMock()
    weather.temperature.return_value.get.return_value = 10
    weather.pressure.get.return_value = 10
    weather.humidity.return_value = 10
    weather.wind.return_value.get.return_value = 0
    weather.clouds.return_value = "clouds"
    weather.rain.return_value = []
    weather.snow.return_value = []
    weather.detailed_status.return_value = "status"
    weather.weather_code = 803

    mocked_owm.weather_at_coords.return_value.weather = weather

    one_day_forecast = MagicMock()
    one_day_forecast.reference_time.return_value = 10
    one_day_forecast.temperature.return_value.get.return_value = 10
    one_day_forecast.rain.return_value.get.return_value = 0
    one_day_forecast.snow.return_value.get.return_value = 0
    one_day_forecast.wind.return_value.get.return_value = 0
    one_day_forecast.weather_code = 803

    mocked_owm.forecast_at_coords.return_value.forecast.weathers = [one_day_forecast]

    one_call = MagicMock()
    one_call.current = weather
    one_call.forecast_hourly = [one_day_forecast]
    one_call.forecast_daily = [one_day_forecast]

    mocked_owm.one_call.return_value = one_call

    mocked_owm.weather_manager.return_value.one_call.return_value = is_api_online

    return mocked_owm
