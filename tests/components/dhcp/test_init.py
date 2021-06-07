"""Test the DHCP discovery integration."""
import datetime
import threading
from unittest.mock import patch

from scapy.error import Scapy_Exception
from scapy.layers.dhcp import DHCP
from scapy.layers.l2 import Ether

from openpeerpower import config_entries
from openpeerpower.components import dhcp
from openpeerpower.components.device_tracker.const import (
    ATTR_HOST_NAME,
    ATTR_IP,
    ATTR_MAC,
    ATTR_SOURCE_TYPE,
    SOURCE_TYPE_ROUTER,
)
from openpeerpower.const import (
    EVENT_OPENPEERPOWER_STARTED,
    EVENT_OPENPEERPOWER_STOP,
    STATE_HOME,
    STATE_NOT_HOME,
)
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util

from tests.common import async_fire_time_changed

# connect b8:b7:f1:6d:b5:33 192.168.210.56
RAW_DHCP_REQUEST = (
    b"\xff\xff\xff\xff\xff\xff\xb8\xb7\xf1m\xb53\x08\x00E\x00\x01P\x06E"
    b"\x00\x00\xff\x11\xb4X\x00\x00\x00\x00\xff\xff\xff\xff\x00D\x00C\x01<"
    b"\x0b\x14\x01\x01\x06\x00jmjV\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xb8\xb7\xf1m\xb53\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00c\x82Sc5\x01\x039\x02\x05\xdc2\x04\xc0\xa8\xd286"
    b"\x04\xc0\xa8\xd0\x017\x04\x01\x03\x1c\x06\x0c\x07connect\xff\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
)

# iRobot-AE9EC12DD3B04885BCBFA36AFB01E1CC 50:14:79:03:85:2c 192.168.1.120
RAW_DHCP_RENEWAL = (
    b"\x00\x15\x5d\x8e\xed\x02\x50\x14\x79\x03\x85\x2c\x08\x00\x45\x00"
    b"\x01\x8e\x51\xd2\x40\x00\x40\x11\x63\xa1\xc0\xa8\x01\x78\xc0\xa8"
    b"\x01\x23\x00\x44\x00\x43\x01\x7a\x12\x09\x01\x01\x06\x00\xd4\xea"
    b"\xb2\xfd\xff\xff\x00\x00\xc0\xa8\x01\x78\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x50\x14\x79\x03\x85\x2c\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x63\x82\x53\x63\x35\x01\x03\x39\x02\x05"
    b"\xdc\x3c\x45\x64\x68\x63\x70\x63\x64\x2d\x35\x2e\x32\x2e\x31\x30"
    b"\x3a\x4c\x69\x6e\x75\x78\x2d\x33\x2e\x31\x38\x2e\x37\x31\x3a\x61"
    b"\x72\x6d\x76\x37\x6c\x3a\x51\x75\x61\x6c\x63\x6f\x6d\x6d\x20\x54"
    b"\x65\x63\x68\x6e\x6f\x6c\x6f\x67\x69\x65\x73\x2c\x20\x49\x6e\x63"
    b"\x20\x41\x50\x51\x38\x30\x30\x39\x0c\x27\x69\x52\x6f\x62\x6f\x74"
    b"\x2d\x41\x45\x39\x45\x43\x31\x32\x44\x44\x33\x42\x30\x34\x38\x38"
    b"\x35\x42\x43\x42\x46\x41\x33\x36\x41\x46\x42\x30\x31\x45\x31\x43"
    b"\x43\x37\x08\x01\x21\x03\x06\x1c\x33\x3a\x3b\xff"
)


async def test_dhcp_match_hostname_and_macaddress(opp):
    """Test matching based on hostname and macaddress."""
    dhcp_watcher = dhcp.DHCPWatcher(
        opp,
        {},
        [{"domain": "mock-domain", "hostname": "connect", "macaddress": "B8B7F1*"}],
    )

    packet = Ether(RAW_DHCP_REQUEST)

    with patch.object(opp.config_entries.flow, "async_init") as mock_init:
        dhcp_watcher.handle_dhcp_packet(packet)
        # Ensure no change is ignored
        dhcp_watcher.handle_dhcp_packet(packet)

    assert len(mock_init.mock_calls) == 1
    assert mock_init.mock_calls[0][1][0] == "mock-domain"
    assert mock_init.mock_calls[0][2]["context"] == {
        "source": config_entries.SOURCE_DHCP
    }
    assert mock_init.mock_calls[0][2]["data"] == {
        dhcp.IP_ADDRESS: "192.168.210.56",
        dhcp.HOSTNAME: "connect",
        dhcp.MAC_ADDRESS: "b8b7f16db533",
    }


async def test_dhcp_renewal_match_hostname_and_macaddress(opp):
    """Test renewal matching based on hostname and macaddress."""
    dhcp_watcher = dhcp.DHCPWatcher(
        opp,
        {},
        [{"domain": "mock-domain", "hostname": "irobot-*", "macaddress": "501479*"}],
    )

    packet = Ether(RAW_DHCP_RENEWAL)

    with patch.object(opp.config_entries.flow, "async_init") as mock_init:
        dhcp_watcher.handle_dhcp_packet(packet)
        # Ensure no change is ignored
        dhcp_watcher.handle_dhcp_packet(packet)

    assert len(mock_init.mock_calls) == 1
    assert mock_init.mock_calls[0][1][0] == "mock-domain"
    assert mock_init.mock_calls[0][2]["context"] == {
        "source": config_entries.SOURCE_DHCP
    }
    assert mock_init.mock_calls[0][2]["data"] == {
        dhcp.IP_ADDRESS: "192.168.1.120",
        dhcp.HOSTNAME: "irobot-ae9ec12dd3b04885bcbfa36afb01e1cc",
        dhcp.MAC_ADDRESS: "50147903852c",
    }


async def test_dhcp_match_hostname(opp):
    """Test matching based on hostname only."""
    dhcp_watcher = dhcp.DHCPWatcher(
        opp, {}, [{"domain": "mock-domain", "hostname": "connect"}]
    )

    packet = Ether(RAW_DHCP_REQUEST)

    with patch.object(opp.config_entries.flow, "async_init") as mock_init:
        dhcp_watcher.handle_dhcp_packet(packet)

    assert len(mock_init.mock_calls) == 1
    assert mock_init.mock_calls[0][1][0] == "mock-domain"
    assert mock_init.mock_calls[0][2]["context"] == {
        "source": config_entries.SOURCE_DHCP
    }
    assert mock_init.mock_calls[0][2]["data"] == {
        dhcp.IP_ADDRESS: "192.168.210.56",
        dhcp.HOSTNAME: "connect",
        dhcp.MAC_ADDRESS: "b8b7f16db533",
    }


async def test_dhcp_match_macaddress(opp):
    """Test matching based on macaddress only."""
    dhcp_watcher = dhcp.DHCPWatcher(
        opp, {}, [{"domain": "mock-domain", "macaddress": "B8B7F1*"}]
    )

    packet = Ether(RAW_DHCP_REQUEST)

    with patch.object(opp.config_entries.flow, "async_init") as mock_init:
        dhcp_watcher.handle_dhcp_packet(packet)

    assert len(mock_init.mock_calls) == 1
    assert mock_init.mock_calls[0][1][0] == "mock-domain"
    assert mock_init.mock_calls[0][2]["context"] == {
        "source": config_entries.SOURCE_DHCP
    }
    assert mock_init.mock_calls[0][2]["data"] == {
        dhcp.IP_ADDRESS: "192.168.210.56",
        dhcp.HOSTNAME: "connect",
        dhcp.MAC_ADDRESS: "b8b7f16db533",
    }


async def test_dhcp_nomatch(opp):
    """Test not matching based on macaddress only."""
    dhcp_watcher = dhcp.DHCPWatcher(
        opp, {}, [{"domain": "mock-domain", "macaddress": "ABC123*"}]
    )

    packet = Ether(RAW_DHCP_REQUEST)

    with patch.object(opp.config_entries.flow, "async_init") as mock_init:
        dhcp_watcher.handle_dhcp_packet(packet)

    assert len(mock_init.mock_calls) == 0


async def test_dhcp_nomatch_hostname(opp):
    """Test not matching based on hostname only."""
    dhcp_watcher = dhcp.DHCPWatcher(
        opp, {}, [{"domain": "mock-domain", "hostname": "nomatch*"}]
    )

    packet = Ether(RAW_DHCP_REQUEST)

    with patch.object(opp.config_entries.flow, "async_init") as mock_init:
        dhcp_watcher.handle_dhcp_packet(packet)

    assert len(mock_init.mock_calls) == 0


async def test_dhcp_nomatch_non_dhcp_packet(opp):
    """Test matching does not throw on a non-dhcp packet."""
    dhcp_watcher = dhcp.DHCPWatcher(
        opp, {}, [{"domain": "mock-domain", "hostname": "nomatch*"}]
    )

    packet = Ether(b"")

    with patch.object(opp.config_entries.flow, "async_init") as mock_init:
        dhcp_watcher.handle_dhcp_packet(packet)

    assert len(mock_init.mock_calls) == 0


async def test_dhcp_nomatch_non_dhcp_request_packet(opp):
    """Test nothing happens with the wrong message-type."""
    dhcp_watcher = dhcp.DHCPWatcher(
        opp, {}, [{"domain": "mock-domain", "hostname": "nomatch*"}]
    )

    packet = Ether(RAW_DHCP_REQUEST)

    packet[DHCP].options = [
        ("message-type", 4),
        ("max_dhcp_size", 1500),
        ("requested_addr", "192.168.210.56"),
        ("server_id", "192.168.208.1"),
        ("param_req_list", [1, 3, 28, 6]),
        ("hostname", b"connect"),
    ]

    with patch.object(opp.config_entries.flow, "async_init") as mock_init:
        dhcp_watcher.handle_dhcp_packet(packet)

    assert len(mock_init.mock_calls) == 0


async def test_dhcp_invalid_hostname(opp):
    """Test we ignore invalid hostnames."""
    dhcp_watcher = dhcp.DHCPWatcher(
        opp, {}, [{"domain": "mock-domain", "hostname": "nomatch*"}]
    )

    packet = Ether(RAW_DHCP_REQUEST)

    packet[DHCP].options = [
        ("message-type", 3),
        ("max_dhcp_size", 1500),
        ("requested_addr", "192.168.210.56"),
        ("server_id", "192.168.208.1"),
        ("param_req_list", [1, 3, 28, 6]),
        ("hostname", "connect"),
    ]

    with patch.object(opp.config_entries.flow, "async_init") as mock_init:
        dhcp_watcher.handle_dhcp_packet(packet)

    assert len(mock_init.mock_calls) == 0


async def test_dhcp_missing_hostname(opp):
    """Test we ignore missing hostnames."""
    dhcp_watcher = dhcp.DHCPWatcher(
        opp, {}, [{"domain": "mock-domain", "hostname": "nomatch*"}]
    )

    packet = Ether(RAW_DHCP_REQUEST)

    packet[DHCP].options = [
        ("message-type", 3),
        ("max_dhcp_size", 1500),
        ("requested_addr", "192.168.210.56"),
        ("server_id", "192.168.208.1"),
        ("param_req_list", [1, 3, 28, 6]),
        ("hostname", None),
    ]

    with patch.object(opp.config_entries.flow, "async_init") as mock_init:
        dhcp_watcher.handle_dhcp_packet(packet)

    assert len(mock_init.mock_calls) == 0


async def test_dhcp_invalid_option(opp):
    """Test we ignore invalid hostname option."""
    dhcp_watcher = dhcp.DHCPWatcher(
        opp, {}, [{"domain": "mock-domain", "hostname": "nomatch*"}]
    )

    packet = Ether(RAW_DHCP_REQUEST)

    packet[DHCP].options = [
        ("message-type", 3),
        ("max_dhcp_size", 1500),
        ("requested_addr", "192.168.208.55"),
        ("server_id", "192.168.208.1"),
        ("param_req_list", [1, 3, 28, 6]),
        ("hostname"),
    ]

    with patch.object(opp.config_entries.flow, "async_init") as mock_init:
        dhcp_watcher.handle_dhcp_packet(packet)

    assert len(mock_init.mock_calls) == 0


async def test_setup_and_stop(opp):
    """Test we can setup and stop."""

    assert await async_setup_component(
        opp,
        dhcp.DOMAIN,
        {},
    )
    await opp.async_block_till_done()

    with patch("openpeerpower.components.dhcp.AsyncSniffer.start") as start_call, patch(
        "openpeerpower.components.dhcp._verify_l2socket_setup",
    ), patch("openpeerpower.components.dhcp.compile_filter",), patch(
        "openpeerpower.components.dhcp.DiscoverHosts.async_discover"
    ):
        opp.bus.async_fire(EVENT_OPENPEERPOWER_STARTED)
        await opp.async_block_till_done()

    opp.bus.async_fire(EVENT_OPENPEERPOWER_STOP)
    await opp.async_block_till_done()

    start_call.assert_called_once()


async def test_setup_fails_as_root(opp, caplog):
    """Test we handle sniff setup failing as root."""

    assert await async_setup_component(
        opp,
        dhcp.DOMAIN,
        {},
    )
    await opp.async_block_till_done()

    wait_event = threading.Event()

    with patch("os.geteuid", return_value=0), patch(
        "openpeerpower.components.dhcp._verify_l2socket_setup",
        side_effect=Scapy_Exception,
    ), patch("openpeerpower.components.dhcp.DiscoverHosts.async_discover"):
        opp.bus.async_fire(EVENT_OPENPEERPOWER_STARTED)
        await opp.async_block_till_done()

    opp.bus.async_fire(EVENT_OPENPEERPOWER_STOP)
    await opp.async_block_till_done()
    wait_event.set()
    assert "Cannot watch for dhcp packets" in caplog.text


async def test_setup_fails_non_root(opp, caplog):
    """Test we handle sniff setup failing as non-root."""

    assert await async_setup_component(
        opp,
        dhcp.DOMAIN,
        {},
    )
    await opp.async_block_till_done()

    with patch("os.geteuid", return_value=10), patch(
        "openpeerpower.components.dhcp._verify_l2socket_setup",
        side_effect=Scapy_Exception,
    ), patch("openpeerpower.components.dhcp.DiscoverHosts.async_discover"):
        opp.bus.async_fire(EVENT_OPENPEERPOWER_STARTED)
        await opp.async_block_till_done()
        opp.bus.async_fire(EVENT_OPENPEERPOWER_STOP)
        await opp.async_block_till_done()

    assert "Cannot watch for dhcp packets without root or CAP_NET_RAW" in caplog.text


async def test_setup_fails_with_broken_libpcap(opp, caplog):
    """Test we abort if libpcap is missing or broken."""

    assert await async_setup_component(
        opp,
        dhcp.DOMAIN,
        {},
    )
    await opp.async_block_till_done()

    with patch("openpeerpower.components.dhcp._verify_l2socket_setup",), patch(
        "openpeerpower.components.dhcp.compile_filter",
        side_effect=ImportError,
    ) as compile_filter, patch(
        "openpeerpower.components.dhcp.AsyncSniffer",
    ) as async_sniffer, patch(
        "openpeerpower.components.dhcp.DiscoverHosts.async_discover"
    ):
        opp.bus.async_fire(EVENT_OPENPEERPOWER_STARTED)
        await opp.async_block_till_done()
        opp.bus.async_fire(EVENT_OPENPEERPOWER_STOP)
        await opp.async_block_till_done()

    assert compile_filter.called
    assert not async_sniffer.called
    assert (
        "Cannot watch for dhcp packets without a functional packet filter"
        in caplog.text
    )


async def test_device_tracker_hostname_and_macaddress_exists_before_start(opp):
    """Test matching based on hostname and macaddress before start."""
    opp.states.async_set(
        "device_tracker.august_connect",
        STATE_HOME,
        {
            ATTR_HOST_NAME: "Connect",
            ATTR_IP: "192.168.210.56",
            ATTR_SOURCE_TYPE: SOURCE_TYPE_ROUTER,
            ATTR_MAC: "B8:B7:F1:6D:B5:33",
        },
    )

    with patch.object(opp.config_entries.flow, "async_init") as mock_init:
        device_tracker_watcher = dhcp.DeviceTrackerWatcher(
            opp,
            {},
            [{"domain": "mock-domain", "hostname": "connect", "macaddress": "B8B7F1*"}],
        )
        await device_tracker_watcher.async_start()
        await opp.async_block_till_done()
        await device_tracker_watcher.async_stop()
        await opp.async_block_till_done()

    assert len(mock_init.mock_calls) == 1
    assert mock_init.mock_calls[0][1][0] == "mock-domain"
    assert mock_init.mock_calls[0][2]["context"] == {
        "source": config_entries.SOURCE_DHCP
    }
    assert mock_init.mock_calls[0][2]["data"] == {
        dhcp.IP_ADDRESS: "192.168.210.56",
        dhcp.HOSTNAME: "connect",
        dhcp.MAC_ADDRESS: "b8b7f16db533",
    }


async def test_device_tracker_hostname_and_macaddress_after_start(opp):
    """Test matching based on hostname and macaddress after start."""

    with patch.object(opp.config_entries.flow, "async_init") as mock_init:
        device_tracker_watcher = dhcp.DeviceTrackerWatcher(
            opp,
            {},
            [{"domain": "mock-domain", "hostname": "connect", "macaddress": "B8B7F1*"}],
        )
        await device_tracker_watcher.async_start()
        await opp.async_block_till_done()
        opp.states.async_set(
            "device_tracker.august_connect",
            STATE_HOME,
            {
                ATTR_HOST_NAME: "Connect",
                ATTR_IP: "192.168.210.56",
                ATTR_SOURCE_TYPE: SOURCE_TYPE_ROUTER,
                ATTR_MAC: "B8:B7:F1:6D:B5:33",
            },
        )
        await opp.async_block_till_done()
        await device_tracker_watcher.async_stop()
        await opp.async_block_till_done()

    assert len(mock_init.mock_calls) == 1
    assert mock_init.mock_calls[0][1][0] == "mock-domain"
    assert mock_init.mock_calls[0][2]["context"] == {
        "source": config_entries.SOURCE_DHCP
    }
    assert mock_init.mock_calls[0][2]["data"] == {
        dhcp.IP_ADDRESS: "192.168.210.56",
        dhcp.HOSTNAME: "connect",
        dhcp.MAC_ADDRESS: "b8b7f16db533",
    }


async def test_device_tracker_hostname_and_macaddress_after_start_not_home(opp):
    """Test matching based on hostname and macaddress after start but not home."""

    with patch.object(opp.config_entries.flow, "async_init") as mock_init:
        device_tracker_watcher = dhcp.DeviceTrackerWatcher(
            opp,
            {},
            [{"domain": "mock-domain", "hostname": "connect", "macaddress": "B8B7F1*"}],
        )
        await device_tracker_watcher.async_start()
        await opp.async_block_till_done()
        opp.states.async_set(
            "device_tracker.august_connect",
            STATE_NOT_HOME,
            {
                ATTR_HOST_NAME: "connect",
                ATTR_IP: "192.168.210.56",
                ATTR_SOURCE_TYPE: SOURCE_TYPE_ROUTER,
                ATTR_MAC: "B8:B7:F1:6D:B5:33",
            },
        )
        await opp.async_block_till_done()
        await device_tracker_watcher.async_stop()
        await opp.async_block_till_done()

    assert len(mock_init.mock_calls) == 0


async def test_device_tracker_hostname_and_macaddress_after_start_not_router(opp):
    """Test matching based on hostname and macaddress after start but not router."""

    with patch.object(opp.config_entries.flow, "async_init") as mock_init:
        device_tracker_watcher = dhcp.DeviceTrackerWatcher(
            opp,
            {},
            [{"domain": "mock-domain", "hostname": "connect", "macaddress": "B8B7F1*"}],
        )
        await device_tracker_watcher.async_start()
        await opp.async_block_till_done()
        opp.states.async_set(
            "device_tracker.august_connect",
            STATE_HOME,
            {
                ATTR_HOST_NAME: "connect",
                ATTR_IP: "192.168.210.56",
                ATTR_SOURCE_TYPE: "something_else",
                ATTR_MAC: "B8:B7:F1:6D:B5:33",
            },
        )
        await opp.async_block_till_done()
        await device_tracker_watcher.async_stop()
        await opp.async_block_till_done()

    assert len(mock_init.mock_calls) == 0


async def test_device_tracker_hostname_and_macaddress_after_start_hostname_missing(
    opp,
):
    """Test matching based on hostname and macaddress after start but missing hostname."""

    with patch.object(opp.config_entries.flow, "async_init") as mock_init:
        device_tracker_watcher = dhcp.DeviceTrackerWatcher(
            opp,
            {},
            [{"domain": "mock-domain", "hostname": "connect", "macaddress": "B8B7F1*"}],
        )
        await device_tracker_watcher.async_start()
        await opp.async_block_till_done()
        opp.states.async_set(
            "device_tracker.august_connect",
            STATE_HOME,
            {
                ATTR_IP: "192.168.210.56",
                ATTR_SOURCE_TYPE: SOURCE_TYPE_ROUTER,
                ATTR_MAC: "B8:B7:F1:6D:B5:33",
            },
        )
        await opp.async_block_till_done()
        await device_tracker_watcher.async_stop()
        await opp.async_block_till_done()

    assert len(mock_init.mock_calls) == 0


async def test_device_tracker_ignore_self_assigned_ips_before_start(opp):
    """Test matching ignores self assigned ip address."""
    opp.states.async_set(
        "device_tracker.august_connect",
        STATE_HOME,
        {
            ATTR_HOST_NAME: "connect",
            ATTR_IP: "169.254.210.56",
            ATTR_SOURCE_TYPE: SOURCE_TYPE_ROUTER,
            ATTR_MAC: "B8:B7:F1:6D:B5:33",
        },
    )

    with patch.object(opp.config_entries.flow, "async_init") as mock_init:
        device_tracker_watcher = dhcp.DeviceTrackerWatcher(
            opp,
            {},
            [{"domain": "mock-domain", "hostname": "connect", "macaddress": "B8B7F1*"}],
        )
        await device_tracker_watcher.async_start()
        await opp.async_block_till_done()
        await device_tracker_watcher.async_stop()
        await opp.async_block_till_done()

    assert len(mock_init.mock_calls) == 0


async def test_aiodiscover_finds_new_hosts(opp):
    """Test aiodiscover finds new host."""
    with patch.object(opp.config_entries.flow, "async_init") as mock_init, patch(
        "openpeerpower.components.dhcp.DiscoverHosts.async_discover",
        return_value=[
            {
                dhcp.DISCOVERY_IP_ADDRESS: "192.168.210.56",
                dhcp.DISCOVERY_HOSTNAME: "connect",
                dhcp.DISCOVERY_MAC_ADDRESS: "b8b7f16db533",
            }
        ],
    ):
        device_tracker_watcher = dhcp.NetworkWatcher(
            opp,
            {},
            [{"domain": "mock-domain", "hostname": "connect", "macaddress": "B8B7F1*"}],
        )
        await device_tracker_watcher.async_start()
        await opp.async_block_till_done()
        await device_tracker_watcher.async_stop()
        await opp.async_block_till_done()

    assert len(mock_init.mock_calls) == 1
    assert mock_init.mock_calls[0][1][0] == "mock-domain"
    assert mock_init.mock_calls[0][2]["context"] == {
        "source": config_entries.SOURCE_DHCP
    }
    assert mock_init.mock_calls[0][2]["data"] == {
        dhcp.IP_ADDRESS: "192.168.210.56",
        dhcp.HOSTNAME: "connect",
        dhcp.MAC_ADDRESS: "b8b7f16db533",
    }


async def test_aiodiscover_does_not_call_again_on_shorter_hostname(opp):
    """Verify longer hostnames generate a new flow but shorter ones do not.

    Some routers will truncate hostnames so we want to accept
    additional discovery where the hostname is longer and then
    reject shorter ones.
    """
    with patch.object(opp.config_entries.flow, "async_init") as mock_init, patch(
        "openpeerpower.components.dhcp.DiscoverHosts.async_discover",
        return_value=[
            {
                dhcp.DISCOVERY_IP_ADDRESS: "192.168.210.56",
                dhcp.DISCOVERY_HOSTNAME: "irobot-abc",
                dhcp.DISCOVERY_MAC_ADDRESS: "b8b7f16db533",
            },
            {
                dhcp.DISCOVERY_IP_ADDRESS: "192.168.210.56",
                dhcp.DISCOVERY_HOSTNAME: "irobot-abcdef",
                dhcp.DISCOVERY_MAC_ADDRESS: "b8b7f16db533",
            },
            {
                dhcp.DISCOVERY_IP_ADDRESS: "192.168.210.56",
                dhcp.DISCOVERY_HOSTNAME: "irobot-abc",
                dhcp.DISCOVERY_MAC_ADDRESS: "b8b7f16db533",
            },
        ],
    ):
        device_tracker_watcher = dhcp.NetworkWatcher(
            opp,
            {},
            [
                {
                    "domain": "mock-domain",
                    "hostname": "irobot-*",
                    "macaddress": "B8B7F1*",
                }
            ],
        )
        await device_tracker_watcher.async_start()
        await opp.async_block_till_done()
        await device_tracker_watcher.async_stop()
        await opp.async_block_till_done()

    assert len(mock_init.mock_calls) == 2
    assert mock_init.mock_calls[0][1][0] == "mock-domain"
    assert mock_init.mock_calls[0][2]["context"] == {
        "source": config_entries.SOURCE_DHCP
    }
    assert mock_init.mock_calls[0][2]["data"] == {
        dhcp.IP_ADDRESS: "192.168.210.56",
        dhcp.HOSTNAME: "irobot-abc",
        dhcp.MAC_ADDRESS: "b8b7f16db533",
    }
    assert mock_init.mock_calls[1][1][0] == "mock-domain"
    assert mock_init.mock_calls[1][2]["context"] == {
        "source": config_entries.SOURCE_DHCP
    }
    assert mock_init.mock_calls[1][2]["data"] == {
        dhcp.IP_ADDRESS: "192.168.210.56",
        dhcp.HOSTNAME: "irobot-abcdef",
        dhcp.MAC_ADDRESS: "b8b7f16db533",
    }


async def test_aiodiscover_finds_new_hosts_after_interval(opp):
    """Test aiodiscover finds new host after interval."""
    with patch.object(opp.config_entries.flow, "async_init") as mock_init, patch(
        "openpeerpower.components.dhcp.DiscoverHosts.async_discover",
        return_value=[],
    ):
        device_tracker_watcher = dhcp.NetworkWatcher(
            opp,
            {},
            [{"domain": "mock-domain", "hostname": "connect", "macaddress": "B8B7F1*"}],
        )
        await device_tracker_watcher.async_start()
        await opp.async_block_till_done()

    assert len(mock_init.mock_calls) == 0

    with patch.object(opp.config_entries.flow, "async_init") as mock_init, patch(
        "openpeerpower.components.dhcp.DiscoverHosts.async_discover",
        return_value=[
            {
                dhcp.DISCOVERY_IP_ADDRESS: "192.168.210.56",
                dhcp.DISCOVERY_HOSTNAME: "connect",
                dhcp.DISCOVERY_MAC_ADDRESS: "b8b7f16db533",
            }
        ],
    ):
        async_fire_time_changed(opp, dt_util.utcnow() + datetime.timedelta(minutes=65))
        await opp.async_block_till_done()
        await device_tracker_watcher.async_stop()
        await opp.async_block_till_done()

    assert len(mock_init.mock_calls) == 1
    assert mock_init.mock_calls[0][1][0] == "mock-domain"
    assert mock_init.mock_calls[0][2]["context"] == {
        "source": config_entries.SOURCE_DHCP
    }
    assert mock_init.mock_calls[0][2]["data"] == {
        dhcp.IP_ADDRESS: "192.168.210.56",
        dhcp.HOSTNAME: "connect",
        dhcp.MAC_ADDRESS: "b8b7f16db533",
    }
