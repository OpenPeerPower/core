"""Tests for the samsungtv component."""
from openpeerpower.components.samsungtv.const import DOMAIN as SAMSUNGTV_DOMAIN
from openpeerpower.core import OpenPeerPower
from openpeerpower.setup import async_setup_component

from tests.common import MockConfigEntry


async def setup_samsungtv(opp: OpenPeerPower, config: dict):
    """Set up mock Samsung TV."""
    await async_setup_component(opp, "persistent_notification", {})
    entry = MockConfigEntry(domain=SAMSUNGTV_DOMAIN, data=config)
    entry.add_to_opp(opp)
    assert await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()
