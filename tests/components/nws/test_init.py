"""Tests for init module."""
from openpeerpower.components.nws.const import DOMAIN
from openpeerpower.components.weather import DOMAIN as WEATHER_DOMAIN
from openpeerpower.const import STATE_UNAVAILABLE

from tests.common import MockConfigEntry
from tests.components.nws.const import NWS_CONFIG


async def test_unload_entry.opp, mock_simple_nws):
    """Test that nws setup with config yaml."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=NWS_CONFIG,
    )
    entry.add_to_opp.opp)

    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    assert len.opp.states.async_entity_ids(WEATHER_DOMAIN)) == 1
    assert DOMAIN in.opp.data

    assert len.opp.data[DOMAIN]) == 1
    entries = opp.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1

    assert await opp.config_entries.async_unload(entries[0].entry_id)
    entities = opp.states.async_entity_ids(WEATHER_DOMAIN)
    assert len(entities) == 1
    for entity in entities:
        assert.opp.states.get(entity).state == STATE_UNAVAILABLE
    assert DOMAIN not in.opp.data

    assert await opp.config_entries.async_remove(entries[0].entry_id)
    await opp.async_block_till_done()
    assert len.opp.states.async_entity_ids(WEATHER_DOMAIN)) == 0
