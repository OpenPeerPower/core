"""Test Met weather entity."""

from openpeerpower import config_entries
from openpeerpower.components.met import DOMAIN
from openpeerpower.components.weather import DOMAIN as WEATHER_DOMAIN
from openpeerpower.helpers import entity_registry as er


async def test_tracking_home(opp, mock_weather):
    """Test we track home."""
    await opp.config_entries.flow.async_init("met", context={"source": "onboarding"})
    await opp.async_block_till_done()
    assert len(opp.states.async_entity_ids("weather")) == 1
    assert len(mock_weather.mock_calls) == 4

    # Test the hourly sensor is disabled by default
    registry = er.async_get(opp)

    state = opp.states.get("weather.test_home_hourly")
    assert state is None

    entry = registry.async_get("weather.test_home_hourly")
    assert entry
    assert entry.disabled
    assert entry.disabled_by == er.DISABLED_INTEGRATION

    # Test we track config
    await opp.config.async_update(latitude=10, longitude=20)
    await opp.async_block_till_done()

    assert len(mock_weather.mock_calls) == 8

    # Same coordinates again should not trigger any new requests to met.no
    await opp.config.async_update(latitude=10, longitude=20)
    await opp.async_block_till_done()
    assert len(mock_weather.mock_calls) == 8

    entry = opp.config_entries.async_entries()[0]
    await opp.config_entries.async_remove(entry.entry_id)
    await opp.async_block_till_done()
    assert len(opp.states.async_entity_ids("weather")) == 0


async def test_not_tracking_home(opp, mock_weather):
    """Test when we not track home."""

    # Pre-create registry entry for disabled by default hourly weather
    registry = er.async_get(opp)
    registry.async_get_or_create(
        WEATHER_DOMAIN,
        DOMAIN,
        "10-20-hourly",
        suggested_object_id="somewhere_hourly",
        disabled_by=None,
    )

    await opp.config_entries.flow.async_init(
        "met",
        context={"source": config_entries.SOURCE_USER},
        data={"name": "Somewhere", "latitude": 10, "longitude": 20, "elevation": 0},
    )
    await opp.async_block_till_done()
    assert len(opp.states.async_entity_ids("weather")) == 2
    assert len(mock_weather.mock_calls) == 4

    # Test we do not track config
    await opp.config.async_update(latitude=10, longitude=20)
    await opp.async_block_till_done()

    assert len(mock_weather.mock_calls) == 4

    entry = opp.config_entries.async_entries()[0]
    await opp.config_entries.async_remove(entry.entry_id)
    await opp.async_block_till_done()
    assert len(opp.states.async_entity_ids("weather")) == 0
