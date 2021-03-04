"""Test Litter-Robot setup process."""
from openpeerpower.components import litterrobot
from openpeerpower.setup import async_setup_component

from .common import CONFIG

from tests.common import MockConfigEntry


async def test_unload_entry(opp):
    """Test being able to unload an entry."""
    entry = MockConfigEntry(
        domain=litterrobot.DOMAIN,
        data=CONFIG[litterrobot.DOMAIN],
    )
    entry.add_to_opp(opp)

    assert await async_setup_component(opp, litterrobot.DOMAIN, {}) is True
    assert await litterrobot.async_unload_entry(opp, entry)
    assert opp.data[litterrobot.DOMAIN] == {}
