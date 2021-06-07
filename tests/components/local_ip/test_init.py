"""Tests for the local_ip component."""
from openpeerpower.components.local_ip import DOMAIN
from openpeerpower.util import get_local_ip

from tests.common import MockConfigEntry


async def test_basic_setup(opp):
    """Test component setup creates entry from config."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_opp(opp)

    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    local_ip = await opp.async_add_executor_job(get_local_ip)
    state = opp.states.get(f"sensor.{DOMAIN}")
    assert state
    assert state.state == local_ip
