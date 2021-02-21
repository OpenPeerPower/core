"""Tests for the WLED integration."""

import json

from openpeerpower.components.wled.const import DOMAIN
from openpeerpower.const import CONF_HOST, CONF_MAC, CONTENT_TYPE_JSON
from openpeerpowerr.core import OpenPeerPower

from tests.common import MockConfigEntry, load_fixture
from tests.test_util.aiohttp import AiohttpClientMocker


async def init_integration(
   .opp: OpenPeerPower,
    aioclient_mock: AiohttpClientMocker,
    rgbw: bool = False,
    skip_setup: bool = False,
) -> MockConfigEntry:
    """Set up the WLED integration in Open Peer Power."""

    fixture = "wled/rgb.json" if not rgbw else "wled/rgbw.json"
    data = json.loads(load_fixture(fixture))

    aioclient_mock.get(
        "http://192.168.1.123:80/json/",
        json=data,
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    aioclient_mock.post(
        "http://192.168.1.123:80/json/state",
        json=data["state"],
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    aioclient_mock.get(
        "http://192.168.1.123:80/json/info",
        json=data["info"],
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    aioclient_mock.get(
        "http://192.168.1.123:80/json/state",
        json=data["state"],
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "192.168.1.123", CONF_MAC: "aabbccddeeff"}
    )

    entry.add_to_opp.opp)

    if not skip_setup:
        await.opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()

    return entry
