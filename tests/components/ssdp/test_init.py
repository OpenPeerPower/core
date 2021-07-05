"""Test the SSDP integration."""
import asyncio
from datetime import timedelta
from unittest.mock import patch

import aiohttp
import pytest

from openpeerpower import config_entries
from openpeerpower.components import ssdp
from openpeerpower.const import EVENT_OPENPEERPOWER_STARTED, EVENT_OPENPEERPOWER_STOP
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util

from tests.common import async_fire_time_changed, mock_coro


async def test_scan_match_st(opp, caplog):
    """Test matching based on ST."""
    scanner = ssdp.Scanner(opp, {"mock-domain": [{"st": "mock-st"}]})

    async def _mock_async_scan(*args, async_callback=None, **kwargs):
        await async_callback(
            {
                "st": "mock-st",
                "location": None,
                "usn": "mock-usn",
                "server": "mock-server",
                "ext": "",
            }
        )

    with patch(
        "openpeerpower.components.ssdp.async_search",
        side_effect=_mock_async_scan,
    ), patch.object(
        opp.config_entries.flow, "async_init", return_value=mock_coro()
    ) as mock_init:
        await scanner.async_scan(None)

    assert len(mock_init.mock_calls) == 1
    assert mock_init.mock_calls[0][1][0] == "mock-domain"
    assert mock_init.mock_calls[0][2]["context"] == {
        "source": config_entries.SOURCE_SSDP
    }
    assert mock_init.mock_calls[0][2]["data"] == {
        ssdp.ATTR_SSDP_ST: "mock-st",
        ssdp.ATTR_SSDP_LOCATION: None,
        ssdp.ATTR_SSDP_USN: "mock-usn",
        ssdp.ATTR_SSDP_SERVER: "mock-server",
        ssdp.ATTR_SSDP_EXT: "",
    }
    assert "Failed to fetch ssdp data" not in caplog.text


@pytest.mark.parametrize(
    "key", (ssdp.ATTR_UPNP_MANUFACTURER, ssdp.ATTR_UPNP_DEVICE_TYPE)
)
async def test_scan_match_upnp_devicedesc(opp, aioclient_mock, key):
    """Test matching based on UPnP device description data."""
    aioclient_mock.get(
        "http://1.1.1.1",
        text=f"""
<root>
  <device>
    <{key}>Paulus</{key}>
  </device>
</root>
    """,
    )
    scanner = ssdp.Scanner(opp, {"mock-domain": [{key: "Paulus"}]})

    async def _mock_async_scan(*args, async_callback=None, **kwargs):
        for _ in range(5):
            await async_callback(
                {
                    "st": "mock-st",
                    "location": "http://1.1.1.1",
                }
            )

    with patch(
        "openpeerpower.components.ssdp.async_search",
        side_effect=_mock_async_scan,
    ), patch.object(
        opp.config_entries.flow, "async_init", return_value=mock_coro()
    ) as mock_init:
        await scanner.async_scan(None)

    # If we get duplicate respones, ensure we only look it up once
    assert len(aioclient_mock.mock_calls) == 1
    assert len(mock_init.mock_calls) == 1
    assert mock_init.mock_calls[0][1][0] == "mock-domain"
    assert mock_init.mock_calls[0][2]["context"] == {
        "source": config_entries.SOURCE_SSDP
    }


async def test_scan_not_all_present(opp, aioclient_mock):
    """Test match fails if some specified attributes are not present."""
    aioclient_mock.get(
        "http://1.1.1.1",
        text="""
<root>
  <device>
    <deviceType>Paulus</deviceType>
  </device>
</root>
    """,
    )
    scanner = ssdp.Scanner(
        opp,
        {
            "mock-domain": [
                {
                    ssdp.ATTR_UPNP_DEVICE_TYPE: "Paulus",
                    ssdp.ATTR_UPNP_MANUFACTURER: "Paulus",
                }
            ]
        },
    )

    async def _mock_async_scan(*args, async_callback=None, **kwargs):
        await async_callback(
            {
                "st": "mock-st",
                "location": "http://1.1.1.1",
            }
        )

    with patch(
        "openpeerpower.components.ssdp.async_search",
        side_effect=_mock_async_scan,
    ), patch.object(
        opp.config_entries.flow, "async_init", return_value=mock_coro()
    ) as mock_init:
        await scanner.async_scan(None)

    assert not mock_init.mock_calls


async def test_scan_not_all_match(opp, aioclient_mock):
    """Test match fails if some specified attribute values differ."""
    aioclient_mock.get(
        "http://1.1.1.1",
        text="""
<root>
  <device>
    <deviceType>Paulus</deviceType>
    <manufacturer>Paulus</manufacturer>
  </device>
</root>
    """,
    )
    scanner = ssdp.Scanner(
        opp,
        {
            "mock-domain": [
                {
                    ssdp.ATTR_UPNP_DEVICE_TYPE: "Paulus",
                    ssdp.ATTR_UPNP_MANUFACTURER: "Not-Paulus",
                }
            ]
        },
    )

    async def _mock_async_scan(*args, async_callback=None, **kwargs):
        await async_callback(
            {
                "st": "mock-st",
                "location": "http://1.1.1.1",
            }
        )

    with patch(
        "openpeerpower.components.ssdp.async_search",
        side_effect=_mock_async_scan,
    ), patch.object(
        opp.config_entries.flow, "async_init", return_value=mock_coro()
    ) as mock_init:
        await scanner.async_scan(None)

    assert not mock_init.mock_calls


@pytest.mark.parametrize("exc", [asyncio.TimeoutError, aiohttp.ClientError])
async def test_scan_description_fetch_fail(opp, aioclient_mock, exc):
    """Test failing to fetch description."""
    aioclient_mock.get("http://1.1.1.1", exc=exc)
    scanner = ssdp.Scanner(opp, {})

    async def _mock_async_scan(*args, async_callback=None, **kwargs):
        await async_callback(
            {
                "st": "mock-st",
                "location": "http://1.1.1.1",
            }
        )

    with patch(
        "openpeerpower.components.ssdp.async_search",
        side_effect=_mock_async_scan,
    ):
        await scanner.async_scan(None)


async def test_scan_description_parse_fail(opp, aioclient_mock):
    """Test invalid XML."""
    aioclient_mock.get(
        "http://1.1.1.1",
        text="""
<root>INVALIDXML
    """,
    )
    scanner = ssdp.Scanner(opp, {})

    async def _mock_async_scan(*args, async_callback=None, **kwargs):
        await async_callback(
            {
                "st": "mock-st",
                "location": "http://1.1.1.1",
            }
        )

    with patch(
        "openpeerpower.components.ssdp.async_search",
        side_effect=_mock_async_scan,
    ):
        await scanner.async_scan(None)


async def test_invalid_characters(opp, aioclient_mock):
    """Test that we replace bad characters with placeholders."""
    aioclient_mock.get(
        "http://1.1.1.1",
        text="""
<root>
  <device>
    <deviceType>ABC</deviceType>
    <serialNumber>\xff\xff\xff\xff</serialNumber>
  </device>
</root>
    """,
    )
    scanner = ssdp.Scanner(
        opp,
        {
            "mock-domain": [
                {
                    ssdp.ATTR_UPNP_DEVICE_TYPE: "ABC",
                }
            ]
        },
    )

    async def _mock_async_scan(*args, async_callback=None, **kwargs):
        await async_callback(
            {
                "st": "mock-st",
                "location": "http://1.1.1.1",
            }
        )

    with patch(
        "openpeerpower.components.ssdp.async_search",
        side_effect=_mock_async_scan,
    ), patch.object(
        opp.config_entries.flow, "async_init", return_value=mock_coro()
    ) as mock_init:
        await scanner.async_scan(None)

    assert len(mock_init.mock_calls) == 1
    assert mock_init.mock_calls[0][1][0] == "mock-domain"
    assert mock_init.mock_calls[0][2]["context"] == {
        "source": config_entries.SOURCE_SSDP
    }
    assert mock_init.mock_calls[0][2]["data"] == {
        "ssdp_location": "http://1.1.1.1",
        "ssdp_st": "mock-st",
        "deviceType": "ABC",
        "serialNumber": "ÿÿÿÿ",
    }


@patch("openpeerpower.components.ssdp.async_search")
async def test_start_stop_scanner(async_search_mock, opp):
    """Test we start and stop the scanner."""
    assert await async_setup_component(opp, ssdp.DOMAIN, {ssdp.DOMAIN: {}})

    opp.bus.async_fire(EVENT_OPENPEERPOWER_STARTED)
    await opp.async_block_till_done()
    async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=200))
    await opp.async_block_till_done()
    assert async_search_mock.call_count == 2

    opp.bus.async_fire(EVENT_OPENPEERPOWER_STOP)
    await opp.async_block_till_done()
    async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=200))
    await opp.async_block_till_done()
    assert async_search_mock.call_count == 2


async def test_unexpected_exception_while_fetching(opp, aioclient_mock, caplog):
    """Test unexpected exception while fetching."""
    aioclient_mock.get(
        "http://1.1.1.1",
        text="""
<root>
  <device>
    <deviceType>ABC</deviceType>
    <serialNumber>\xff\xff\xff\xff</serialNumber>
  </device>
</root>
    """,
    )
    scanner = ssdp.Scanner(
        opp,
        {
            "mock-domain": [
                {
                    ssdp.ATTR_UPNP_DEVICE_TYPE: "ABC",
                }
            ]
        },
    )

    async def _mock_async_scan(*args, async_callback=None, **kwargs):
        await async_callback(
            {
                "st": "mock-st",
                "location": "http://1.1.1.1",
            }
        )

    with patch(
        "openpeerpower.components.ssdp.ElementTree.fromstring", side_effect=ValueError
    ), patch(
        "openpeerpower.components.ssdp.async_search",
        side_effect=_mock_async_scan,
    ), patch.object(
        opp.config_entries.flow, "async_init", return_value=mock_coro()
    ) as mock_init:
        await scanner.async_scan(None)

    assert len(mock_init.mock_calls) == 0
    assert "Failed to fetch ssdp data from: http://1.1.1.1" in caplog.text
