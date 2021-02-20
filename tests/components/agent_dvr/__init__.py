"""Tests for the agent_dvr component."""

from openpeerpower.components.agent_dvr.const import DOMAIN, SERVER_URL
from openpeerpower.const import CONF_HOST, CONF_PORT, CONTENT_TYPE_JSON
from openpeerpowerr.core import OpenPeerPower

from tests.common import MockConfigEntry, load_fixture
from tests.test_util.aiohttp import AiohttpClientMocker


async def init_integration(
   .opp: OpenPeerPower,
    aioclient_mock: AiohttpClientMocker,
    skip_setup: bool = False,
) -> MockConfigEntry:
    """Set up the Agent DVR integration in Open Peer Power."""

    aioclient_mock.get(
        "http://example.local:8090/command.cgi?cmd=getStatus",
        text=load_fixture("agent_dvr/status.json"),
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )
    aioclient_mock.get(
        "http://example.local:8090/command.cgi?cmd=getObjects",
        text=load_fixture("agent_dvr/objects.json"),
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="c0715bba-c2d0-48ef-9e3e-bc81c9ea4447",
        data={
            CONF_HOST: "example.local",
            CONF_PORT: 8090,
            SERVER_URL: "http://example.local:8090/",
        },
    )

    entry.add_to_opp.opp)

    if not skip_setup:
        await.opp.config_entries.async_setup(entry.entry_id)
        await.opp.async_block_till_done()

    return entry
