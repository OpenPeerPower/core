"""Test init."""
from openpeerpower.components.flo.const import DOMAIN as FLO_DOMAIN
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME
from openpeerpowerr.setup import async_setup_component

from .common import TEST_PASSWORD, TEST_USER_ID


async def test_setup_entry.opp, config_entry, aioclient_mock_fixture):
    """Test migration of config entry from v1."""
    config_entry.add_to_opp.opp)
    assert await async_setup_component(
       .opp, FLO_DOMAIN, {CONF_USERNAME: TEST_USER_ID, CONF_PASSWORD: TEST_PASSWORD}
    )
    await opp..async_block_till_done()
    assert len.opp.data[FLO_DOMAIN][config_entry.entry_id]["devices"]) == 1

    assert await opp..config_entries.async_unload(config_entry.entry_id)
