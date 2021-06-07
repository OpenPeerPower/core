"""Test the SSDP integration."""
import asyncio
from datetime import timedelta
from ipaddress import IPv4Address, IPv6Address
from unittest.mock import patch

import aiohttp
from async_upnp_client.search import SSDPListener
from async_upnp_client.utils import CaseInsensitiveDict
import pytest

from openpeerpower import config_entries
from openpeerpower.components import ssdp
from openpeerpower.const import (
    EVENT_OPENPEERPOWER_STARTED,
    EVENT_OPENPEERPOWER_STOP,
    MATCH_ALL,
)
from openpeerpower.core import CoreState, callback
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util

from tests.common import async_fire_time_changed, mock_coro


def _patched_ssdp_listener(info, *args, **kwargs):
    listener = SSDPListener(*args, **kwargs)

    async def _async_callback(*_):
        await listener.async_callback(info)

    listener.async_start = _async_callback
    return listener


async def _async_run_mocked_scan(opp, mock_ssdp_response, mock_get_ssdp):
    def _generate_fake_ssdp_listener(*args, **kwargs):
        return _patched_ssdp_listener(
            mock_ssdp_response,
            *args,
            **kwargs,
        )

    with patch(
        "openpeerpower.components.ssdp.async_get_ssdp",
        return_value=mock_get_ssdp,
    ), patch(
        "openpeerpower.components.ssdp.SSDPListener",
        new=_generate_fake_ssdp_listener,
    ), patch.object(
        opp.config_entries.flow, "async_init", return_value=mock_coro()
    ) as mock_init:
        assert await async_setup_component(opp, ssdp.DOMAIN, {ssdp.DOMAIN: {}})
        opp.bus.async_fire(EVENT_OPENPEERPOWER_STARTED)
        await opp.async_block_till_done()
        await opp.async_block_till_done()

    return mock_init


async def test_scan_match_st(opp, caplog):
    """Test matching based on ST."""
    mock_ssdp_response = {
        "st": "mock-st",
        "location": None,
        "usn": "mock-usn",
        "server": "mock-server",
        "ext": "",
    }
    mock_get_ssdp = {"mock-domain": [{"st": "mock-st"}]}
    mock_init = await _async_run_mocked_scan(opp, mock_ssdp_response, mock_get_ssdp)

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


async def test_partial_response(opp, caplog):
    """Test location and st missing."""
    mock_ssdp_response = {
        "usn": "mock-usn",
        "server": "mock-server",
        "ext": "",
    }
    mock_get_ssdp = {"mock-domain": [{"st": "mock-st"}]}
    mock_init = await _async_run_mocked_scan(opp, mock_ssdp_response, mock_get_ssdp)

    assert len(mock_init.mock_calls) == 0


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
    mock_get_ssdp = {"mock-domain": [{key: "Paulus"}]}
    mock_ssdp_response = {
        "st": "mock-st",
        "location": "http://1.1.1.1",
    }
    mock_init = await _async_run_mocked_scan(opp, mock_ssdp_response, mock_get_ssdp)
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
    mock_ssdp_response = {
        "st": "mock-st",
        "location": "http://1.1.1.1",
    }
    mock_get_ssdp = {
        "mock-domain": [
            {
                ssdp.ATTR_UPNP_DEVICE_TYPE: "Paulus",
                ssdp.ATTR_UPNP_MANUFACTURER: "Paulus",
            }
        ]
    }
    mock_init = await _async_run_mocked_scan(opp, mock_ssdp_response, mock_get_ssdp)

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
    mock_ssdp_response = {
        "st": "mock-st",
        "location": "http://1.1.1.1",
    }
    mock_get_ssdp = {
        "mock-domain": [
            {
                ssdp.ATTR_UPNP_DEVICE_TYPE: "Paulus",
                ssdp.ATTR_UPNP_MANUFACTURER: "Not-Paulus",
            }
        ]
    }
    mock_init = await _async_run_mocked_scan(opp, mock_ssdp_response, mock_get_ssdp)

    assert not mock_init.mock_calls


@pytest.mark.parametrize("exc", [asyncio.TimeoutError, aiohttp.ClientError])
async def test_scan_description_fetch_fail(opp, aioclient_mock, exc):
    """Test failing to fetch description."""
    aioclient_mock.get("http://1.1.1.1", exc=exc)
    mock_ssdp_response = {
        "st": "mock-st",
        "usn": "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL::urn:mdx-netflix-com:service:target:3",
        "location": "http://1.1.1.1",
    }
    mock_get_ssdp = {
        "mock-domain": [
            {
                ssdp.ATTR_UPNP_DEVICE_TYPE: "Paulus",
                ssdp.ATTR_UPNP_MANUFACTURER: "Paulus",
            }
        ]
    }
    mock_init = await _async_run_mocked_scan(opp, mock_ssdp_response, mock_get_ssdp)

    assert not mock_init.mock_calls

    assert ssdp.async_get_discovery_info_by_st(opp, "mock-st") == [
        {
            "UDN": "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL",
            "ssdp_location": "http://1.1.1.1",
            "ssdp_st": "mock-st",
            "ssdp_usn": "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL::urn:mdx-netflix-com:service:target:3",
        }
    ]


async def test_scan_description_parse_fail(opp, aioclient_mock):
    """Test invalid XML."""
    aioclient_mock.get(
        "http://1.1.1.1",
        text="""
<root>INVALIDXML
    """,
    )

    mock_ssdp_response = {
        "st": "mock-st",
        "location": "http://1.1.1.1",
    }
    mock_get_ssdp = {
        "mock-domain": [
            {
                ssdp.ATTR_UPNP_DEVICE_TYPE: "Paulus",
                ssdp.ATTR_UPNP_MANUFACTURER: "Paulus",
            }
        ]
    }
    mock_init = await _async_run_mocked_scan(opp, mock_ssdp_response, mock_get_ssdp)

    assert not mock_init.mock_calls


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

    mock_ssdp_response = {
        "st": "mock-st",
        "location": "http://1.1.1.1",
    }
    mock_get_ssdp = {
        "mock-domain": [
            {
                ssdp.ATTR_UPNP_DEVICE_TYPE: "ABC",
            }
        ]
    }

    mock_init = await _async_run_mocked_scan(opp, mock_ssdp_response, mock_get_ssdp)

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


@patch("openpeerpower.components.ssdp.SSDPListener.async_start")
@patch("openpeerpower.components.ssdp.SSDPListener.async_search")
async def test_start_stop_scanner(async_start_mock, async_search_mock, opp):
    """Test we start and stop the scanner."""
    assert await async_setup_component(opp, ssdp.DOMAIN, {ssdp.DOMAIN: {}})

    opp.bus.async_fire(EVENT_OPENPEERPOWER_STARTED)
    await opp.async_block_till_done()
    async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=200))
    await opp.async_block_till_done()
    assert async_start_mock.call_count == 1
    assert async_search_mock.call_count == 1

    opp.bus.async_fire(EVENT_OPENPEERPOWER_STOP)
    await opp.async_block_till_done()
    async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=200))
    await opp.async_block_till_done()
    assert async_start_mock.call_count == 1
    assert async_search_mock.call_count == 1


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
    mock_ssdp_response = {
        "st": "mock-st",
        "location": "http://1.1.1.1",
    }
    mock_get_ssdp = {
        "mock-domain": [
            {
                ssdp.ATTR_UPNP_DEVICE_TYPE: "ABC",
            }
        ]
    }

    with patch(
        "openpeerpower.components.ssdp.descriptions.ElementTree.fromstring",
        side_effect=ValueError,
    ):
        mock_init = await _async_run_mocked_scan(opp, mock_ssdp_response, mock_get_ssdp)

    assert len(mock_init.mock_calls) == 0
    assert "Failed to fetch ssdp data from: http://1.1.1.1" in caplog.text


async def test_scan_with_registered_callback(opp, aioclient_mock, caplog):
    """Test matching based on callback."""
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
    mock_ssdp_response = {
        "st": "mock-st",
        "location": "http://1.1.1.1",
        "usn": "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL::urn:mdx-netflix-com:service:target:3",
        "server": "mock-server",
        "x-rincon-bootseq": "55",
        "ext": "",
    }
    not_matching_intergration_callbacks = []
    intergration_match_all_callbacks = []
    intergration_match_all_not_present_callbacks = []
    intergration_callbacks = []
    intergration_callbacks_from_cache = []
    match_any_callbacks = []

    @callback
    def _async_exception_callbacks(info):
        raise ValueError

    @callback
    def _async_intergration_callbacks(info):
        intergration_callbacks.append(info)

    @callback
    def _async_intergration_match_all_callbacks(info):
        intergration_match_all_callbacks.append(info)

    @callback
    def _async_intergration_match_all_not_present_callbacks(info):
        intergration_match_all_not_present_callbacks.append(info)

    @callback
    def _async_intergration_callbacks_from_cache(info):
        intergration_callbacks_from_cache.append(info)

    @callback
    def _async_not_matching_intergration_callbacks(info):
        not_matching_intergration_callbacks.append(info)

    @callback
    def _async_match_any_callbacks(info):
        match_any_callbacks.append(info)

    def _generate_fake_ssdp_listener(*args, **kwargs):
        listener = SSDPListener(*args, **kwargs)

        async def _async_callback(*_):
            await listener.async_callback(mock_ssdp_response)

        @callback
        def _callback(*_):
            opp.async_create_task(listener.async_callback(mock_ssdp_response))

        listener.async_start = _async_callback
        listener.async_search = _callback
        return listener

    with patch(
        "openpeerpower.components.ssdp.SSDPListener",
        new=_generate_fake_ssdp_listener,
    ):
        opp.state = CoreState.stopped
        assert await async_setup_component(opp, ssdp.DOMAIN, {ssdp.DOMAIN: {}})
        await opp.async_block_till_done()
        ssdp.async_register_callback(opp, _async_exception_callbacks, {})
        ssdp.async_register_callback(
            opp,
            _async_intergration_callbacks,
            {"st": "mock-st"},
        )
        ssdp.async_register_callback(
            opp,
            _async_intergration_match_all_callbacks,
            {"x-rincon-bootseq": MATCH_ALL},
        )
        ssdp.async_register_callback(
            opp,
            _async_intergration_match_all_not_present_callbacks,
            {"x-not-there": MATCH_ALL},
        )
        ssdp.async_register_callback(
            opp,
            _async_not_matching_intergration_callbacks,
            {"st": "not-match-mock-st"},
        )
        ssdp.async_register_callback(
            opp,
            _async_match_any_callbacks,
        )
        await opp.async_block_till_done()
        async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=200))
        ssdp.async_register_callback(
            opp,
            _async_intergration_callbacks_from_cache,
            {"st": "mock-st"},
        )
        await opp.async_block_till_done()
        opp.bus.async_fire(EVENT_OPENPEERPOWER_STARTED)
        opp.state = CoreState.running
        await opp.async_block_till_done()
        async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=200))
        await opp.async_block_till_done()
        assert opp.state == CoreState.running

    assert len(intergration_callbacks) == 3
    assert len(intergration_callbacks_from_cache) == 3
    assert len(intergration_match_all_callbacks) == 3
    assert len(intergration_match_all_not_present_callbacks) == 0
    assert len(match_any_callbacks) == 3
    assert len(not_matching_intergration_callbacks) == 0
    assert intergration_callbacks[0] == {
        ssdp.ATTR_UPNP_DEVICE_TYPE: "Paulus",
        ssdp.ATTR_SSDP_EXT: "",
        ssdp.ATTR_SSDP_LOCATION: "http://1.1.1.1",
        ssdp.ATTR_SSDP_SERVER: "mock-server",
        ssdp.ATTR_SSDP_ST: "mock-st",
        ssdp.ATTR_SSDP_USN: "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL::urn:mdx-netflix-com:service:target:3",
        ssdp.ATTR_UPNP_UDN: "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL",
        "x-rincon-bootseq": "55",
    }
    assert "Failed to callback info" in caplog.text


async def test_unsolicited_ssdp_registered_callback(opp, aioclient_mock, caplog):
    """Test matching based on callback can handle unsolicited ssdp traffic without st."""
    aioclient_mock.get(
        "http://10.6.9.12:1400/xml/device_description.xml",
        text="""
<root>
  <device>
    <deviceType>Paulus</deviceType>
  </device>
</root>
    """,
    )
    mock_ssdp_response = {
        "location": "http://10.6.9.12:1400/xml/device_description.xml",
        "nt": "uuid:RINCON_1111BB963FD801400",
        "nts": "ssdp:alive",
        "server": "Linux UPnP/1.0 Sonos/63.2-88230 (ZPS12)",
        "usn": "uuid:RINCON_1111BB963FD801400",
        "x-rincon-household": "Sonos_dfjfkdghjhkjfhkdjfhkd",
        "x-rincon-bootseq": "250",
        "bootid.upnp.org": "250",
        "x-rincon-wifimode": "0",
        "x-rincon-variant": "1",
        "household.smartspeaker.audio": "Sonos_v3294823948542543534",
    }
    intergration_callbacks = []

    @callback
    def _async_intergration_callbacks(info):
        intergration_callbacks.append(info)

    def _generate_fake_ssdp_listener(*args, **kwargs):
        listener = SSDPListener(*args, **kwargs)

        async def _async_callback(*_):
            await listener.async_callback(mock_ssdp_response)

        @callback
        def _callback(*_):
            opp.async_create_task(listener.async_callback(mock_ssdp_response))

        listener.async_start = _async_callback
        listener.async_search = _callback
        return listener

    with patch(
        "openpeerpower.components.ssdp.SSDPListener",
        new=_generate_fake_ssdp_listener,
    ):
        opp.state = CoreState.stopped
        assert await async_setup_component(opp, ssdp.DOMAIN, {ssdp.DOMAIN: {}})
        await opp.async_block_till_done()
        ssdp.async_register_callback(
            opp,
            _async_intergration_callbacks,
            {"nts": "ssdp:alive", "x-rincon-bootseq": MATCH_ALL},
        )
        await opp.async_block_till_done()
        async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=200))
        await opp.async_block_till_done()
        opp.bus.async_fire(EVENT_OPENPEERPOWER_STARTED)
        opp.state = CoreState.running
        await opp.async_block_till_done()
        async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=200))
        await opp.async_block_till_done()
        assert opp.state == CoreState.running

    assert (
        len(intergration_callbacks) == 2
    )  # unsolicited callbacks without st are not cached
    assert intergration_callbacks[0] == {
        "UDN": "uuid:RINCON_1111BB963FD801400",
        "bootid.upnp.org": "250",
        "deviceType": "Paulus",
        "household.smartspeaker.audio": "Sonos_v3294823948542543534",
        "nt": "uuid:RINCON_1111BB963FD801400",
        "nts": "ssdp:alive",
        "ssdp_location": "http://10.6.9.12:1400/xml/device_description.xml",
        "ssdp_server": "Linux UPnP/1.0 Sonos/63.2-88230 (ZPS12)",
        "ssdp_usn": "uuid:RINCON_1111BB963FD801400",
        "x-rincon-bootseq": "250",
        "x-rincon-household": "Sonos_dfjfkdghjhkjfhkdjfhkd",
        "x-rincon-variant": "1",
        "x-rincon-wifimode": "0",
    }
    assert "Failed to callback info" not in caplog.text


async def test_scan_second_hit(opp, aioclient_mock, caplog):
    """Test matching on second scan."""
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

    mock_ssdp_response = CaseInsensitiveDict(
        **{
            "ST": "mock-st",
            "LOCATION": "http://1.1.1.1",
            "USN": "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL::urn:mdx-netflix-com:service:target:3",
            "SERVER": "mock-server",
            "EXT": "",
        }
    )
    mock_get_ssdp = {"mock-domain": [{"st": "mock-st"}]}
    intergration_callbacks = []

    @callback
    def _async_intergration_callbacks(info):
        intergration_callbacks.append(info)

    def _generate_fake_ssdp_listener(*args, **kwargs):
        listener = SSDPListener(*args, **kwargs)

        async def _async_callback(*_):
            pass

        @callback
        def _callback(*_):
            opp.async_create_task(listener.async_callback(mock_ssdp_response))

        listener.async_start = _async_callback
        listener.async_search = _callback
        return listener

    with patch(
        "openpeerpower.components.ssdp.async_get_ssdp",
        return_value=mock_get_ssdp,
    ), patch(
        "openpeerpower.components.ssdp.SSDPListener",
        new=_generate_fake_ssdp_listener,
    ), patch.object(
        opp.config_entries.flow, "async_init", return_value=mock_coro()
    ) as mock_init:
        assert await async_setup_component(opp, ssdp.DOMAIN, {ssdp.DOMAIN: {}})
        await opp.async_block_till_done()
        remove = ssdp.async_register_callback(
            opp,
            _async_intergration_callbacks,
            {"st": "mock-st"},
        )
        opp.bus.async_fire(EVENT_OPENPEERPOWER_STARTED)
        await opp.async_block_till_done()
        async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=200))
        await opp.async_block_till_done()
        async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=200))
        await opp.async_block_till_done()
        remove()
        async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=200))
        await opp.async_block_till_done()

    assert len(intergration_callbacks) == 2
    assert intergration_callbacks[0] == {
        ssdp.ATTR_UPNP_DEVICE_TYPE: "Paulus",
        ssdp.ATTR_SSDP_EXT: "",
        ssdp.ATTR_SSDP_LOCATION: "http://1.1.1.1",
        ssdp.ATTR_SSDP_SERVER: "mock-server",
        ssdp.ATTR_SSDP_ST: "mock-st",
        ssdp.ATTR_SSDP_USN: "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL::urn:mdx-netflix-com:service:target:3",
        ssdp.ATTR_UPNP_UDN: "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL",
    }
    assert len(mock_init.mock_calls) == 1
    assert mock_init.mock_calls[0][1][0] == "mock-domain"
    assert mock_init.mock_calls[0][2]["context"] == {
        "source": config_entries.SOURCE_SSDP
    }
    assert mock_init.mock_calls[0][2]["data"] == {
        ssdp.ATTR_UPNP_DEVICE_TYPE: "Paulus",
        ssdp.ATTR_SSDP_ST: "mock-st",
        ssdp.ATTR_SSDP_LOCATION: "http://1.1.1.1",
        ssdp.ATTR_SSDP_SERVER: "mock-server",
        ssdp.ATTR_SSDP_EXT: "",
        ssdp.ATTR_SSDP_USN: "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL::urn:mdx-netflix-com:service:target:3",
        ssdp.ATTR_UPNP_UDN: "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL",
    }
    assert "Failed to fetch ssdp data" not in caplog.text
    udn_discovery_info = ssdp.async_get_discovery_info_by_st(opp, "mock-st")
    discovery_info = udn_discovery_info[0]
    assert discovery_info[ssdp.ATTR_SSDP_LOCATION] == "http://1.1.1.1"
    assert discovery_info[ssdp.ATTR_SSDP_ST] == "mock-st"
    assert (
        discovery_info[ssdp.ATTR_UPNP_UDN]
        == "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL"
    )
    assert (
        discovery_info[ssdp.ATTR_SSDP_USN]
        == "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL::urn:mdx-netflix-com:service:target:3"
    )

    st_discovery_info = ssdp.async_get_discovery_info_by_udn(
        opp, "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL"
    )
    discovery_info = st_discovery_info[0]
    assert discovery_info[ssdp.ATTR_SSDP_LOCATION] == "http://1.1.1.1"
    assert discovery_info[ssdp.ATTR_SSDP_ST] == "mock-st"
    assert (
        discovery_info[ssdp.ATTR_UPNP_UDN]
        == "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL"
    )
    assert (
        discovery_info[ssdp.ATTR_SSDP_USN]
        == "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL::urn:mdx-netflix-com:service:target:3"
    )

    discovery_info = ssdp.async_get_discovery_info_by_udn_st(
        opp, "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL", "mock-st"
    )
    assert discovery_info[ssdp.ATTR_SSDP_LOCATION] == "http://1.1.1.1"
    assert discovery_info[ssdp.ATTR_SSDP_ST] == "mock-st"
    assert (
        discovery_info[ssdp.ATTR_UPNP_UDN]
        == "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL"
    )
    assert (
        discovery_info[ssdp.ATTR_SSDP_USN]
        == "uuid:TIVRTLSR7ANF-D6E-1557809135086-RETAIL::urn:mdx-netflix-com:service:target:3"
    )

    assert ssdp.async_get_discovery_info_by_udn_st(opp, "wrong", "mock-st") is None


_ADAPTERS_WITH_MANUAL_CONFIG = [
    {
        "auto": True,
        "default": False,
        "enabled": True,
        "ipv4": [],
        "ipv6": [
            {
                "address": "2001:db8::",
                "network_prefix": 8,
                "flowinfo": 1,
                "scope_id": 1,
            }
        ],
        "name": "eth0",
    },
    {
        "auto": True,
        "default": False,
        "enabled": True,
        "ipv4": [{"address": "192.168.1.5", "network_prefix": 23}],
        "ipv6": [],
        "name": "eth1",
    },
    {
        "auto": False,
        "default": False,
        "enabled": False,
        "ipv4": [{"address": "169.254.3.2", "network_prefix": 16}],
        "ipv6": [],
        "name": "vtun0",
    },
]


async def test_async_detect_interfaces_setting_empty_route(opp):
    """Test without default interface config and the route returns nothing."""
    mock_get_ssdp = {
        "mock-domain": [
            {
                ssdp.ATTR_UPNP_DEVICE_TYPE: "ABC",
            }
        ]
    }
    create_args = []

    def _generate_fake_ssdp_listener(*args, **kwargs):
        create_args.append([args, kwargs])
        listener = SSDPListener(*args, **kwargs)

        async def _async_callback(*_):
            pass

        @callback
        def _callback(*_):
            pass

        listener.async_start = _async_callback
        listener.async_search = _callback
        return listener

    with patch(
        "openpeerpower.components.ssdp.async_get_ssdp",
        return_value=mock_get_ssdp,
    ), patch(
        "openpeerpower.components.ssdp.SSDPListener",
        new=_generate_fake_ssdp_listener,
    ), patch(
        "openpeerpower.components.ssdp.network.async_get_adapters",
        return_value=_ADAPTERS_WITH_MANUAL_CONFIG,
    ):
        assert await async_setup_component(opp, ssdp.DOMAIN, {ssdp.DOMAIN: {}})
        await opp.async_block_till_done()
        opp.bus.async_fire(EVENT_OPENPEERPOWER_STARTED)
        await opp.async_block_till_done()

    assert {create_args[0][1]["source_ip"], create_args[1][1]["source_ip"]} == {
        IPv4Address("192.168.1.5"),
        IPv6Address("2001:db8::"),
    }
