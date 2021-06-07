"""The tests for the Buienradar sensor platform."""
from openpeerpower.components.buienradar.const import DOMAIN
from openpeerpower.const import CONF_LATITUDE, CONF_LONGITUDE
from openpeerpower.helpers.entity_registry import async_get

from tests.common import MockConfigEntry

TEST_LONGITUDE = 51.5288504
TEST_LATITUDE = 5.4002156

CONDITIONS = ["stationname", "temperature"]
TEST_CFG_DATA = {CONF_LATITUDE: TEST_LATITUDE, CONF_LONGITUDE: TEST_LONGITUDE}


async def test_smoke_test_setup_component(aioclient_mock, opp):
    """Smoke test for successfully set-up with default config."""
    mock_entry = MockConfigEntry(domain=DOMAIN, unique_id="TEST_ID", data=TEST_CFG_DATA)

    mock_entry.add_to_opp(opp)

    entity_registry = async_get(opp)
    for cond in CONDITIONS:
        entity_registry.async_get_or_create(
            domain="sensor",
            platform="buienradar",
            unique_id=f"{TEST_LATITUDE:2.6f}{TEST_LONGITUDE:2.6f}{cond}",
            config_entry=mock_entry,
            original_name=f"Buienradar {cond}",
        )
    await opp.async_block_till_done()

    await opp.config_entries.async_setup(mock_entry.entry_id)
    await opp.async_block_till_done()

    for cond in CONDITIONS:
        state = opp.states.get(f"sensor.buienradar_5_40021651_528850{cond}")
        assert state.state == "unknown"
