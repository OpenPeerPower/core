"""Tests for the IPP integration."""
import os

import aiohttp
from pyipp import IPPConnectionUpgradeRequired, IPPError

from openpeerpower.components.ipp.const import CONF_BASE_PATH, CONF_UUID, DOMAIN
from openpeerpower.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SSL,
    CONF_TYPE,
    CONF_VERIFY_SSL,
)
from openpeerpower.core import OpenPeerPower

from tests.common import MockConfigEntry
from tests.test_util.aiohttp import AiohttpClientMocker

ATTR_HOSTNAME = "hostname"
ATTR_PROPERTIES = "properties"

HOST = "192.168.1.31"
PORT = 631
BASE_PATH = "/ipp/print"

IPP_ZEROCONF_SERVICE_TYPE = "_ipp._tcp.local."
IPPS_ZEROCONF_SERVICE_TYPE = "_ipps._tcp.local."

ZEROCONF_NAME = "EPSON XP-6000 Series"
ZEROCONF_HOST = HOST
ZEROCONF_HOSTNAME = "EPSON123456.local."
ZEROCONF_PORT = PORT
ZEROCONF_RP = "ipp/print"

MOCK_USER_INPUT = {
    CONF_HOST: HOST,
    CONF_PORT: PORT,
    CONF_SSL: False,
    CONF_VERIFY_SSL: False,
    CONF_BASE_PATH: BASE_PATH,
}

MOCK_ZEROCONF_IPP_SERVICE_INFO = {
    CONF_TYPE: IPP_ZEROCONF_SERVICE_TYPE,
    CONF_NAME: f"{ZEROCONF_NAME}.{IPP_ZEROCONF_SERVICE_TYPE}",
    CONF_HOST: ZEROCONF_HOST,
    ATTR_HOSTNAME: ZEROCONF_HOSTNAME,
    CONF_PORT: ZEROCONF_PORT,
    ATTR_PROPERTIES: {"rp": ZEROCONF_RP},
}

MOCK_ZEROCONF_IPPS_SERVICE_INFO = {
    CONF_TYPE: IPPS_ZEROCONF_SERVICE_TYPE,
    CONF_NAME: f"{ZEROCONF_NAME}.{IPPS_ZEROCONF_SERVICE_TYPE}",
    CONF_HOST: ZEROCONF_HOST,
    ATTR_HOSTNAME: ZEROCONF_HOSTNAME,
    CONF_PORT: ZEROCONF_PORT,
    ATTR_PROPERTIES: {"rp": ZEROCONF_RP},
}


def load_fixture_binary(filename):
    """Load a binary fixture."""
    path = os.path.join(os.path.dirname(__file__), "..", "..", "fixtures", filename)
    with open(path, "rb") as fptr:
        return fptr.read()


def mock_connection(
    aioclient_mock: AiohttpClientMocker,
    host: str = HOST,
    port: int = PORT,
    ssl: bool = False,
    base_path: str = BASE_PATH,
    conn_error: bool = False,
    conn_upgrade_error: bool = False,
    ipp_error: bool = False,
    no_unique_id: bool = False,
    parse_error: bool = False,
    version_not_supported: bool = False,
):
    """Mock the IPP connection."""
    scheme = "https" if ssl else "http"
    ipp_url = f"{scheme}://{host}:{port}"

    if ipp_error:
        aioclient_mock.post(f"{ipp_url}{base_path}", exc=IPPError)
        return

    if conn_error:
        aioclient_mock.post(f"{ipp_url}{base_path}", exc=aiohttp.ClientError)
        return

    if conn_upgrade_error:
        aioclient_mock.post(f"{ipp_url}{base_path}", exc=IPPConnectionUpgradeRequired)
        return

    fixture = "ipp/get-printer-attributes.bin"
    if no_unique_id:
        fixture = "ipp/get-printer-attributes-success-nodata.bin"
    elif version_not_supported:
        fixture = "ipp/get-printer-attributes-error-0x0503.bin"

    if parse_error:
        content = "BAD"
    else:
        content = load_fixture_binary(fixture)

    aioclient_mock.post(
        f"{ipp_url}{base_path}",
        content=content,
        headers={"Content-Type": "application/ipp"},
    )


async def init_integration(
    opp. OpenPeerPower,
    aioclient_mock: AiohttpClientMocker,
    skip_setup: bool = False,
    host: str = HOST,
    port: int = PORT,
    ssl: bool = False,
    base_path: str = BASE_PATH,
    uuid: str = "cfe92100-67c4-11d4-a45f-f8d027761251",
    unique_id: str = "cfe92100-67c4-11d4-a45f-f8d027761251",
    conn_error: bool = False,
) -> MockConfigEntry:
    """Set up the IPP integration in Open Peer Power."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=unique_id,
        data={
            CONF_HOST: host,
            CONF_PORT: port,
            CONF_SSL: ssl,
            CONF_VERIFY_SSL: True,
            CONF_BASE_PATH: base_path,
            CONF_UUID: uuid,
        },
    )

    entry.add_to.opp.opp)

    mock_connection(
        aioclient_mock,
        host=host,
        port=port,
        ssl=ssl,
        base_path=base_path,
        conn_error=conn_error,
    )

    if not skip_setup:
        await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()

    return entry
