"""The tests for the buienradar weather component."""
from openpeerpower.components.buienradar.const import DOMAIN
from openpeerpower.const import CONF_LATITUDE, CONF_LONGITUDE

from tests.common import MockConfigEntry

TEST_CFG_DATA = {CONF_LATITUDE: 51.5288504, CONF_LONGITUDE: 5.4002156}


async def test_smoke_test_setup_component(aioclient_mock, opp):
    """Smoke test for successfully set-up with default config."""
    mock_entry = MockConfigEntry(domain=DOMAIN, unique_id="TEST_ID", data=TEST_CFG_DATA)

    mock_entry.add_to_opp(opp)

    await opp.config_entries.async_setup(mock_entry.entry_id)
    await opp.async_block_till_done()

    state = opp.states.get("weather.buienradar")
    assert state.state == "unknown"
