"""Common initialisation for the Plugwise integration."""

from openpeerpower.components.plugwise.const import DOMAIN
from openpeerpowerr.core import OpenPeerPower

from tests.common import MockConfigEntry
from tests.test_util.aiohttp import AiohttpClientMocker


async def async_init_integration(
   .opp: OpenPeerPower,
    aioclient_mock: AiohttpClientMocker,
    skip_setup: bool = False,
):
    """Initialize the Smile integration."""

    entry = MockConfigEntry(
        domain=DOMAIN, data={"host": "1.1.1.1", "password": "test-password"}
    )
    entry.add_to_opp.opp)

    if not skip_setup:
        await.opp.config_entries.async_setup(entry.entry_id)
        await.opp.async_block_till_done()

    return entry
