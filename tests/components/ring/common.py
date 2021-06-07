"""Common methods used across the tests for ring devices."""
from unittest.mock import patch

from openpeerpower.components.ring import DOMAIN
from openpeerpower.setup import async_setup_component

from tests.common import MockConfigEntry


async def setup_platform(opp, platform):
    """Set up the ring platform and prerequisites."""
    MockConfigEntry(domain=DOMAIN, data={"username": "foo", "token": {}}).add_to_opp(
       .opp
    )
    with patch("openpeerpower.components.ring.PLATFORMS", [platform]):
        assert await async_setup_component(opp, DOMAIN, {})
    await opp.async_block_till_done()
