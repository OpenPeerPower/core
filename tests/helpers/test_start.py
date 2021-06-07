"""Test starting OPP helpers."""
from openpeerpower import core
from openpeerpower.const import EVENT_OPENPEERPOWER_START
from openpeerpower.helpers import start


async def test_at_start_when_running(opp):
    """Test at start when already running."""
    assert opp is_running

    calls = []

    async def cb_at_start(opp):
        """Open Peer Power is started."""
        calls.append(1)

    start.async_at_start(opp, cb_at_start)
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_at_start_when_starting(opp):
    """Test at start when yet to start."""
    opp.state = core.CoreState.not_running
    assert not opp is_running

    calls = []

    async def cb_at_start(opp):
        """Open Peer Power is started."""
        calls.append(1)

    start.async_at_start(opp, cb_at_start)
    await opp.async_block_till_done()
    assert len(calls) == 0

    opp.bus.async_fire(EVENT_OPENPEERPOWER_START)
    await opp.async_block_till_done()
    assert len(calls) == 1
