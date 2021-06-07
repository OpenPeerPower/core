"""UniFi sensor platform tests."""

from datetime import datetime
from unittest.mock import patch

from aiounifi.controller import MESSAGE_CLIENT, MESSAGE_CLIENT_REMOVED

from openpeerpower.components.device_tracker import DOMAIN as TRACKER_DOMAIN
from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.components.unifi.const import (
    CONF_ALLOW_BANDWIDTH_SENSORS,
    CONF_ALLOW_UPTIME_SENSORS,
    CONF_TRACK_CLIENTS,
    CONF_TRACK_DEVICES,
    DOMAIN as UNIFI_DOMAIN,
)
from openpeerpower.helpers.dispatcher import async_dispatcher_send
import openpeerpower.util.dt as dt_util

from .test_controller import setup_unifi_integration


async def test_no_clients(opp, aioclient_mock):
    """Test the update_clients function when no clients are found."""
    await setup_unifi_integration(
        opp,
        aioclient_mock,
        options={
            CONF_ALLOW_BANDWIDTH_SENSORS: True,
            CONF_ALLOW_UPTIME_SENSORS: True,
        },
    )

    assert len(opp.states.async_entity_ids(SENSOR_DOMAIN)) == 0


async def test_bandwidth_sensors(opp, aioclient_mock, mock_unifi_websocket):
    """Verify that bandwidth sensors are working as expected."""
    wired_client = {
        "hostname": "Wired client",
        "is_wired": True,
        "mac": "00:00:00:00:00:01",
        "oui": "Producer",
        "wired-rx_bytes": 1234000000,
        "wired-tx_bytes": 5678000000,
    }
    wireless_client = {
        "is_wired": False,
        "mac": "00:00:00:00:00:02",
        "name": "Wireless client",
        "oui": "Producer",
        "rx_bytes": 2345000000,
        "tx_bytes": 6789000000,
    }
    options = {
        CONF_ALLOW_BANDWIDTH_SENSORS: True,
        CONF_ALLOW_UPTIME_SENSORS: False,
        CONF_TRACK_CLIENTS: False,
        CONF_TRACK_DEVICES: False,
    }

    config_entry = await setup_unifi_integration(
        opp,
        aioclient_mock,
        options=options,
        clients_response=[wired_client, wireless_client],
    )

    assert len(opp.states.async_all()) == 5
    assert len(opp.states.async_entity_ids(SENSOR_DOMAIN)) == 4
    assert opp.states.get("sensor.wired_client_rx").state == "1234.0"
    assert opp.states.get("sensor.wired_client_tx").state == "5678.0"
    assert opp.states.get("sensor.wireless_client_rx").state == "2345.0"
    assert opp.states.get("sensor.wireless_client_tx").state == "6789.0"

    # Verify state update

    wireless_client["rx_bytes"] = 3456000000
    wireless_client["tx_bytes"] = 7891000000

    mock_unifi_websocket(
        data={
            "meta": {"message": MESSAGE_CLIENT},
            "data": [wireless_client],
        }
    )
    await opp.async_block_till_done()

    assert opp.states.get("sensor.wireless_client_rx").state == "3456.0"
    assert opp.states.get("sensor.wireless_client_tx").state == "7891.0"

    # Disable option

    options[CONF_ALLOW_BANDWIDTH_SENSORS] = False
    opp.config_entries.async_update_entry(config_entry, options=options.copy())
    await opp.async_block_till_done()

    assert len(opp.states.async_all()) == 1
    assert len(opp.states.async_entity_ids(SENSOR_DOMAIN)) == 0
    assert opp.states.get("sensor.wireless_client_rx") is None
    assert opp.states.get("sensor.wireless_client_tx") is None
    assert opp.states.get("sensor.wired_client_rx") is None
    assert opp.states.get("sensor.wired_client_tx") is None

    # Enable option

    options[CONF_ALLOW_BANDWIDTH_SENSORS] = True
    opp.config_entries.async_update_entry(config_entry, options=options.copy())
    await opp.async_block_till_done()

    assert len(opp.states.async_all()) == 5
    assert len(opp.states.async_entity_ids(SENSOR_DOMAIN)) == 4
    assert opp.states.get("sensor.wireless_client_rx")
    assert opp.states.get("sensor.wireless_client_tx")
    assert opp.states.get("sensor.wired_client_rx")
    assert opp.states.get("sensor.wired_client_tx")

    # Try to add the sensors again, using a signal

    clients_connected = {wired_client["mac"], wireless_client["mac"]}
    devices_connected = set()

    controller = opp.data[UNIFI_DOMAIN][config_entry.entry_id]

    async_dispatcher_send(
        opp,
        controller.signal_update,
        clients_connected,
        devices_connected,
    )
    await opp.async_block_till_done()

    assert len(opp.states.async_all()) == 5
    assert len(opp.states.async_entity_ids(SENSOR_DOMAIN)) == 4


async def test_uptime_sensors(opp, aioclient_mock, mock_unifi_websocket):
    """Verify that uptime sensors are working as expected."""
    client1 = {
        "mac": "00:00:00:00:00:01",
        "name": "client1",
        "oui": "Producer",
        "uptime": 1609506061,
    }
    client2 = {
        "hostname": "Client2",
        "mac": "00:00:00:00:00:02",
        "oui": "Producer",
        "uptime": 60,
    }
    options = {
        CONF_ALLOW_BANDWIDTH_SENSORS: False,
        CONF_ALLOW_UPTIME_SENSORS: True,
        CONF_TRACK_CLIENTS: False,
        CONF_TRACK_DEVICES: False,
    }

    now = datetime(2021, 1, 1, 1, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.now", return_value=now):
        config_entry = await setup_unifi_integration(
            opp,
            aioclient_mock,
            options=options,
            clients_response=[client1, client2],
        )

    assert len(opp.states.async_all()) == 3
    assert len(opp.states.async_entity_ids(SENSOR_DOMAIN)) == 2
    assert opp.states.get("sensor.client1_uptime").state == "2021-01-01T13:01:01+00:00"
    assert opp.states.get("sensor.client2_uptime").state == "2021-01-01T00:59:00+00:00"

    # Verify state update

    client1["uptime"] = 1609506062
    mock_unifi_websocket(
        data={
            "meta": {"message": MESSAGE_CLIENT},
            "data": [client1],
        }
    )
    await opp.async_block_till_done()

    assert opp.states.get("sensor.client1_uptime").state == "2021-01-01T13:01:02+00:00"

    # Disable option

    options[CONF_ALLOW_UPTIME_SENSORS] = False
    opp.config_entries.async_update_entry(config_entry, options=options.copy())
    await opp.async_block_till_done()

    assert len(opp.states.async_all()) == 1
    assert len(opp.states.async_entity_ids(SENSOR_DOMAIN)) == 0
    assert opp.states.get("sensor.client1_uptime") is None
    assert opp.states.get("sensor.client2_uptime") is None

    # Enable option

    options[CONF_ALLOW_UPTIME_SENSORS] = True
    with patch("openpeerpower.util.dt.now", return_value=now):
        opp.config_entries.async_update_entry(config_entry, options=options.copy())
        await opp.async_block_till_done()

    assert len(opp.states.async_all()) == 3
    assert len(opp.states.async_entity_ids(SENSOR_DOMAIN)) == 2
    assert opp.states.get("sensor.client1_uptime")
    assert opp.states.get("sensor.client2_uptime")

    # Try to add the sensors again, using a signal

    clients_connected = {client1["mac"], client2["mac"]}
    devices_connected = set()

    controller = opp.data[UNIFI_DOMAIN][config_entry.entry_id]

    async_dispatcher_send(
        opp,
        controller.signal_update,
        clients_connected,
        devices_connected,
    )
    await opp.async_block_till_done()

    assert len(opp.states.async_all()) == 3
    assert len(opp.states.async_entity_ids(SENSOR_DOMAIN)) == 2


async def test_remove_sensors(opp, aioclient_mock, mock_unifi_websocket):
    """Verify removing of clients work as expected."""
    wired_client = {
        "hostname": "Wired client",
        "is_wired": True,
        "mac": "00:00:00:00:00:01",
        "oui": "Producer",
        "wired-rx_bytes": 1234000000,
        "wired-tx_bytes": 5678000000,
        "uptime": 1600094505,
    }
    wireless_client = {
        "is_wired": False,
        "mac": "00:00:00:00:00:02",
        "name": "Wireless client",
        "oui": "Producer",
        "rx_bytes": 2345000000,
        "tx_bytes": 6789000000,
        "uptime": 60,
    }

    await setup_unifi_integration(
        opp,
        aioclient_mock,
        options={
            CONF_ALLOW_BANDWIDTH_SENSORS: True,
            CONF_ALLOW_UPTIME_SENSORS: True,
        },
        clients_response=[wired_client, wireless_client],
    )

    assert len(opp.states.async_all()) == 9
    assert len(opp.states.async_entity_ids(SENSOR_DOMAIN)) == 6
    assert len(opp.states.async_entity_ids(TRACKER_DOMAIN)) == 2
    assert opp.states.get("sensor.wired_client_rx")
    assert opp.states.get("sensor.wired_client_tx")
    assert opp.states.get("sensor.wired_client_uptime")
    assert opp.states.get("sensor.wireless_client_rx")
    assert opp.states.get("sensor.wireless_client_tx")
    assert opp.states.get("sensor.wireless_client_uptime")

    # Remove wired client

    mock_unifi_websocket(
        data={
            "meta": {"message": MESSAGE_CLIENT_REMOVED},
            "data": [wired_client],
        }
    )
    await opp.async_block_till_done()

    assert len(opp.states.async_all()) == 5
    assert len(opp.states.async_entity_ids(SENSOR_DOMAIN)) == 3
    assert len(opp.states.async_entity_ids(TRACKER_DOMAIN)) == 1
    assert opp.states.get("sensor.wired_client_rx") is None
    assert opp.states.get("sensor.wired_client_tx") is None
    assert opp.states.get("sensor.wired_client_uptime") is None
    assert opp.states.get("sensor.wireless_client_rx")
    assert opp.states.get("sensor.wireless_client_tx")
    assert opp.states.get("sensor.wireless_client_uptime")
