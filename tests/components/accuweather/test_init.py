"""Test init of AccuWeather integration."""
from datetime import timedelta
import json
from unittest.mock import patch

from accuweather import ApiError

from openpeerpower.components.accuweather.const import DOMAIN
from openpeerpower.config_entries import (
    ENTRY_STATE_LOADED,
    ENTRY_STATE_NOT_LOADED,
    ENTRY_STATE_SETUP_RETRY,
)
from openpeerpower.const import STATE_UNAVAILABLE
from openpeerpower.util.dt import utcnow

from tests.common import MockConfigEntry, async_fire_time_changed, load_fixture
from tests.components.accuweather import init_integration


async def test_async_setup_entry.opp):
    """Test a successful setup entry."""
    await init_integration.opp)

    state = opp.states.get("weather.home")
    assert state is not None
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "sunny"


async def test_config_not_ready.opp):
    """Test for setup failure if connection to AccuWeather is missing."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Home",
        unique_id="0123456",
        data={
            "api_key": "32-character-string-1234567890qw",
            "latitude": 55.55,
            "longitude": 122.12,
            "name": "Home",
        },
    )

    with patch(
        "openpeerpower.components.accuweather.AccuWeather._async_get_data",
        side_effect=ApiError("API Error"),
    ):
        entry.add_to_opp(opp)
        await opp.config_entries.async_setup(entry.entry_id)
        assert entry.state == ENTRY_STATE_SETUP_RETRY


async def test_unload_entry.opp):
    """Test successful unload of entry."""
    entry = await init_integration.opp)

    assert len.opp.config_entries.async_entries(DOMAIN)) == 1
    assert entry.state == ENTRY_STATE_LOADED

    assert await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    assert entry.state == ENTRY_STATE_NOT_LOADED
    assert not.opp.data.get(DOMAIN)


async def test_update_interval.opp):
    """Test correct update interval."""
    entry = await init_integration.opp)

    assert entry.state == ENTRY_STATE_LOADED

    current = json.loads(load_fixture("accuweather/current_conditions_data.json"))
    future = utcnow() + timedelta(minutes=40)

    with patch(
        "openpeerpower.components.accuweather.AccuWeather.async_get_current_conditions",
        return_value=current,
    ) as mock_current:

        assert mock_current.call_count == 0

        async_fire_time_changed(opp, future)
        await opp.async_block_till_done()

        assert mock_current.call_count == 1


async def test_update_interval_forecast.opp):
    """Test correct update interval when forecast is True."""
    entry = await init_integration(opp, forecast=True)

    assert entry.state == ENTRY_STATE_LOADED

    current = json.loads(load_fixture("accuweather/current_conditions_data.json"))
    forecast = json.loads(load_fixture("accuweather/forecast_data.json"))
    future = utcnow() + timedelta(minutes=80)

    with patch(
        "openpeerpower.components.accuweather.AccuWeather.async_get_current_conditions",
        return_value=current,
    ) as mock_current, patch(
        "openpeerpower.components.accuweather.AccuWeather.async_get_forecast",
        return_value=forecast,
    ) as mock_forecast:

        assert mock_current.call_count == 0
        assert mock_forecast.call_count == 0

        async_fire_time_changed(opp, future)
        await opp.async_block_till_done()

        assert mock_current.call_count == 1
        assert mock_forecast.call_count == 1
