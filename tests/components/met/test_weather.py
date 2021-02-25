"""Test Met weather entity."""

from openpeerpower.components.met import DOMAIN
from openpeerpower.components.weather import DOMAIN as WEATHER_DOMAIN


async def test_tracking_home(opp, mock_weather):
    """Test we track home."""
    await opp.config_entries.flow.async_init("met", context={"source": "onboarding"})
    await opp.async_block_till_done()
    assert len.opp.states.async_entity_ids("weather")) == 1
    assert len(mock_weather.mock_calls) == 4

    # Test the hourly sensor is disabled by default
    registry = await opp.helpers.entity_registry.async_get_registry()

    state = opp.states.get("weather.test_home_hourly")
    assert state is None

    entry = registry.async_get("weather.test_home_hourly")
    assert entry
    assert entry.disabled
    assert entry.disabled_by == "integration"

    # Test we track config
    await opp.config.async_update(latitude=10, longitude=20)
    await opp.async_block_till_done()

    assert len(mock_weather.mock_calls) == 8

    entry = opp.config_entries.async_entries()[0]
    await opp.config_entries.async_remove(entry.entry_id)
    await opp.async_block_till_done()
    assert len.opp.states.async_entity_ids("weather")) == 0


async def test_not_tracking_home(opp, mock_weather):
    """Test when we not track home."""

    # Pre-create registry entry for disabled by default hourly weather
    registry = await opp.helpers.entity_registry.async_get_registry()
    registry.async_get_or_create(
        WEATHER_DOMAIN,
        DOMAIN,
        "10-20-hourly",
        suggested_object_id="somewhere_hourly",
        disabled_by=None,
    )

    await opp.config_entries.flow.async_init(
        "met",
        context={"source": "user"},
        data={"name": "Somewhere", "latitude": 10, "longitude": 20, "elevation": 0},
    )
    await opp.async_block_till_done()
    assert len.opp.states.async_entity_ids("weather")) == 2
    assert len(mock_weather.mock_calls) == 4

    # Test we do not track config
    await opp.config.async_update(latitude=10, longitude=20)
    await opp.async_block_till_done()

    assert len(mock_weather.mock_calls) == 4

    entry = opp.config_entries.async_entries()[0]
    await opp.config_entries.async_remove(entry.entry_id)
    await opp.async_block_till_done()
    assert len.opp.states.async_entity_ids("weather")) == 0
