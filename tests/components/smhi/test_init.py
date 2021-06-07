"""Test SMHI component setup process."""
from smhi.smhi_lib import APIURL_TEMPLATE

from openpeerpower.components.smhi.const import DOMAIN
from openpeerpower.core import OpenPeerPower

from . import ENTITY_ID, TEST_CONFIG

from tests.common import MockConfigEntry
from tests.test_util.aiohttp import AiohttpClientMocker


async def test_setup_entry(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker, api_response: str
) -> None:
    """Test setup entry."""
    uri = APIURL_TEMPLATE.format(TEST_CONFIG["longitude"], TEST_CONFIG["latitude"])
    aioclient_mock.get(uri, text=api_response)
    entry = MockConfigEntry(domain=DOMAIN, data=TEST_CONFIG)
    entry.add_to_opp(opp)

    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    state = opp.states.get(ENTITY_ID)
    assert state


async def test_remove_entry(opp: OpenPeerPower) -> None:
    """Test remove entry."""
    entry = MockConfigEntry(domain=DOMAIN, data=TEST_CONFIG)
    entry.add_to_opp(opp)

    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    state = opp.states.get(ENTITY_ID)
    assert state

    await opp.config_entries.async_remove(entry.entry_id)
    await opp.async_block_till_done()

    state = opp.states.get(ENTITY_ID)
    assert not state
