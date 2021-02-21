"""Tests for the Advantage Air component."""

from openpeerpower.components.advantage_air.const import DOMAIN
from openpeerpower.const import CONF_IP_ADDRESS, CONF_PORT

from tests.common import MockConfigEntry, load_fixture

TEST_SYSTEM_DATA = load_fixture("advantage_air/getSystemData.json")
TEST_SET_RESPONSE = load_fixture("advantage_air/setAircon.json")

USER_INPUT = {
    CONF_IP_ADDRESS: "1.2.3.4",
    CONF_PORT: 2025,
}

TEST_SYSTEM_URL = (
    f"http://{USER_INPUT[CONF_IP_ADDRESS]}:{USER_INPUT[CONF_PORT]}/getSystemData"
)
TEST_SET_URL = f"http://{USER_INPUT[CONF_IP_ADDRESS]}:{USER_INPUT[CONF_PORT]}/setAircon"


async def add_mock_config.opp):
    """Create a fake Advantage Air Config Entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test entry",
        unique_id="0123456",
        data=USER_INPUT,
    )
    entry.add_to_opp.opp)
    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()
    return entry
