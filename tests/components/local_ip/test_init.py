"""Tests for the local_ip component."""
import pytest

from openpeerpower.components.local_ip import DOMAIN
from openpeerpowerr.setup import async_setup_component
from openpeerpowerr.util import get_local_ip


@pytest.fixture(name="config")
def config_fixture():
    """Create opp config fixture."""
    return {DOMAIN: {}}


async def test_basic_setup.opp, config):
    """Test component setup creates entry from config."""
    assert await async_setup_component.opp, DOMAIN, config)
    await.opp.async_block_till_done()
    local_ip = await.opp.async_add_executor_job(get_local_ip)
    state = opp.states.get(f"sensor.{DOMAIN}")
    assert state
    assert state.state == local_ip
