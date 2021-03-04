"""Tests for the Cloudflare integration."""
from typing import List
from unittest.mock import AsyncMock, patch

from pycfdns import CFRecord

from openpeerpower.components.cloudflare.const import CONF_RECORDS, DOMAIN
from openpeerpower.const import CONF_API_TOKEN, CONF_ZONE

from tests.common import MockConfigEntry

ENTRY_CONFIG = {
    CONF_API_TOKEN: "mock-api-token",
    CONF_ZONE: "mock.com",
    CONF_RECORDS: ["ha.mock.com", "openpeerpower.mock.com"],
}

ENTRY_OPTIONS = {}

USER_INPUT = {
    CONF_API_TOKEN: "mock-api-token",
}

USER_INPUT_ZONE = {CONF_ZONE: "mock.com"}

USER_INPUT_RECORDS = {CONF_RECORDS: ["ha.mock.com", "openpeerpower.mock.com"]}

MOCK_ZONE = "mock.com"
MOCK_ZONE_ID = "mock-zone-id"
MOCK_ZONE_RECORDS = [
    {
        "id": "zone-record-id",
        "type": "A",
        "name": "ha.mock.com",
        "proxied": True,
        "content": "127.0.0.1",
    },
    {
        "id": "zone-record-id-2",
        "type": "A",
        "name": "openpeerpower.mock.com",
        "proxied": True,
        "content": "127.0.0.1",
    },
    {
        "id": "zone-record-id-3",
        "type": "A",
        "name": "mock.com",
        "proxied": True,
        "content": "127.0.0.1",
    },
]


async def init_integration(
    opp,
    *,
    data: dict = ENTRY_CONFIG,
    options: dict = ENTRY_OPTIONS,
) -> MockConfigEntry:
    """Set up the Cloudflare integration in Open Peer Power."""
    entry = MockConfigEntry(domain=DOMAIN, data=data, options=options)
    entry.add_to_opp(opp)

    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    return entry


def _get_mock_cfupdate(
    zone: str = MOCK_ZONE,
    zone_id: str = MOCK_ZONE_ID,
    records: List = MOCK_ZONE_RECORDS,
):
    client = AsyncMock()

    zone_records = [record["name"] for record in records]
    cf_records = [CFRecord(record) for record in records]

    client.get_zones = AsyncMock(return_value=[zone])
    client.get_zone_records = AsyncMock(return_value=zone_records)
    client.get_record_info = AsyncMock(return_value=cf_records)
    client.get_zone_id = AsyncMock(return_value=zone_id)
    client.update_records = AsyncMock(return_value=None)

    return client


def _patch_async_setup(return_value=True):
    return patch(
        "openpeerpower.components.cloudflare.async_setup",
        return_value=return_value,
    )


def _patch_async_setup_entry(return_value=True):
    return patch(
        "openpeerpower.components.cloudflare.async_setup_entry",
        return_value=return_value,
    )
