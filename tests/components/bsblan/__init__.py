"""Tests for the bsblan integration."""

from openpeerpower.components.bsblan.const import (
    CONF_DEVICE_IDENT,
    CONF_PASSKEY,
    DOMAIN,
)
from openpeerpower.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    CONTENT_TYPE_JSON,
)
from openpeerpowerr.core import OpenPeerPower

from tests.common import MockConfigEntry, load_fixture
from tests.test_util.aiohttp import AiohttpClientMocker


async def init_integration(
   .opp: OpenPeerPower,
    aioclient_mock: AiohttpClientMocker,
    skip_setup: bool = False,
) -> MockConfigEntry:
    """Set up the BSBLan integration in Open Peer Power."""

    aioclient_mock.post(
        "http://example.local:80/1234/JQ?Parameter=6224,6225,6226",
        params={"Parameter": "6224,6225,6226"},
        text=load_fixture("bsblan/info.json"),
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="RVS21.831F/127",
        data={
            CONF_HOST: "example.local",
            CONF_USERNAME: "nobody",
            CONF_PASSWORD: "qwerty",
            CONF_PASSKEY: "1234",
            CONF_PORT: 80,
            CONF_DEVICE_IDENT: "RVS21.831F/127",
        },
    )

    entry.add_to_opp.opp)

    if not skip_setup:
        await.opp.config_entries.async_setup(entry.entry_id)
        await.opp.async_block_till_done()

    return entry


async def init_integration_without_auth(
   .opp: OpenPeerPower,
    aioclient_mock: AiohttpClientMocker,
    skip_setup: bool = False,
) -> MockConfigEntry:
    """Set up the BSBLan integration in Open Peer Power."""

    aioclient_mock.post(
        "http://example.local:80/1234/JQ?Parameter=6224,6225,6226",
        params={"Parameter": "6224,6225,6226"},
        text=load_fixture("bsblan/info.json"),
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="RVS21.831F/127",
        data={
            CONF_HOST: "example.local",
            CONF_PASSKEY: "1234",
            CONF_PORT: 80,
            CONF_DEVICE_IDENT: "RVS21.831F/127",
        },
    )

    entry.add_to_opp.opp)

    if not skip_setup:
        await.opp.config_entries.async_setup(entry.entry_id)
        await.opp.async_block_till_done()

    return entry
