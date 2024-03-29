"""The tests for the Rfxtrx component."""

from unittest.mock import call

from openpeerpower.components.rfxtrx import DOMAIN
from openpeerpower.components.rfxtrx.const import EVENT_RFXTRX_EVENT
from openpeerpower.core import callback
from openpeerpower.helpers import device_registry as dr
from openpeerpower.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.components.rfxtrx.conftest import create_rfx_test_cfg


async def test_valid_config(opp):
    """Test configuration."""
    assert await async_setup_component(
        opp,
        "rfxtrx",
        {
            "rfxtrx": {
                "device": "/dev/serial/by-id/usb"
                + "-RFXCOM_RFXtrx433_A1Y0NJGR-if00-port0",
            }
        },
    )


async def test_valid_config2(opp):
    """Test configuration."""
    assert await async_setup_component(
        opp,
        "rfxtrx",
        {
            "rfxtrx": {
                "device": "/dev/serial/by-id/usb"
                + "-RFXCOM_RFXtrx433_A1Y0NJGR-if00-port0",
                "debug": True,
            }
        },
    )


async def test_invalid_config(opp):
    """Test configuration."""
    assert not await async_setup_component(opp, "rfxtrx", {"rfxtrx": {}})

    assert not await async_setup_component(
        opp,
        "rfxtrx",
        {
            "rfxtrx": {
                "device": "/dev/serial/by-id/usb"
                + "-RFXCOM_RFXtrx433_A1Y0NJGR-if00-port0",
                "invalid_key": True,
            }
        },
    )


async def test_fire_event(opp, rfxtrx):
    """Test fire event."""
    entry_data = create_rfx_test_cfg(
        device="/dev/serial/by-id/usb-RFXCOM_RFXtrx433_A1Y0NJGR-if00-port0",
        automatic_add=True,
        devices={
            "0b1100cd0213c7f210010f51": {"fire_event": True},
            "0716000100900970": {"fire_event": True},
        },
    )
    mock_entry = MockConfigEntry(domain="rfxtrx", unique_id=DOMAIN, data=entry_data)

    mock_entry.add_to_opp(opp)

    await opp.config_entries.async_setup(mock_entry.entry_id)
    await opp.async_block_till_done()
    await opp.async_start()

    device_registry: dr.DeviceRegistry = dr.async_get(opp)

    calls = []

    @callback
    def record_event(event):
        """Add recorded event to set."""
        assert event.event_type == "rfxtrx_event"
        calls.append(event.data)

    opp.bus.async_listen(EVENT_RFXTRX_EVENT, record_event)

    await rfxtrx.signal("0b1100cd0213c7f210010f51")
    await rfxtrx.signal("0716000100900970")

    device_id_1 = device_registry.async_get_device(
        identifiers={("rfxtrx", "11", "0", "213c7f2:16")}
    )
    assert device_id_1

    device_id_2 = device_registry.async_get_device(
        identifiers={("rfxtrx", "16", "0", "00:90")}
    )
    assert device_id_2

    assert calls == [
        {
            "packet_type": 17,
            "sub_type": 0,
            "type_string": "AC",
            "id_string": "213c7f2:16",
            "data": "0b1100cd0213c7f210010f51",
            "values": {"Command": "On", "Rssi numeric": 5},
            "device_id": device_id_1.id,
        },
        {
            "packet_type": 22,
            "sub_type": 0,
            "type_string": "Byron SX",
            "id_string": "00:90",
            "data": "0716000100900970",
            "values": {"Command": "Chime", "Rssi numeric": 7, "Sound": 9},
            "device_id": device_id_2.id,
        },
    ]


async def test_send(opp, rfxtrx):
    """Test configuration."""
    entry_data = create_rfx_test_cfg(device="/dev/null", devices={})
    mock_entry = MockConfigEntry(domain="rfxtrx", unique_id=DOMAIN, data=entry_data)

    mock_entry.add_to_opp(opp)

    await opp.config_entries.async_setup(mock_entry.entry_id)
    await opp.async_block_till_done()

    await opp.services.async_call(
        "rfxtrx", "send", {"event": "0a520802060101ff0f0269"}, blocking=True
    )

    assert rfxtrx.transport.send.mock_calls == [
        call(bytearray(b"\x0a\x52\x08\x02\x06\x01\x01\xff\x0f\x02\x69"))
    ]
