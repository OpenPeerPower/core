"""Test the Z-Wave JS Websocket API."""
import json
from unittest.mock import patch

import pytest
from zwave_js_server.const import LogLevel
from zwave_js_server.event import Event
from zwave_js_server.exceptions import (
    FailedCommand,
    InvalidNewValue,
    NotFoundError,
    SetValueFailed,
)

from openpeerpower.components.websocket_api.const import ERR_NOT_FOUND
from openpeerpower.components.zwave_js.api import (
    COMMAND_CLASS_ID,
    CONFIG,
    ENABLED,
    ENTRY_ID,
    ERR_NOT_LOADED,
    FILENAME,
    FORCE_CONSOLE,
    ID,
    LEVEL,
    LOG_TO_FILE,
    NODE_ID,
    OPTED_IN,
    PROPERTY,
    PROPERTY_KEY,
    TYPE,
    VALUE,
)
from openpeerpower.components.zwave_js.const import (
    CONF_DATA_COLLECTION_OPTED_IN,
    DOMAIN,
)
from openpeerpower.helpers import device_registry as dr


async def test_network_status(opp, integration, opp_ws_client):
    """Test the network status websocket command."""
    entry = integration
    ws_client = await opp_ws_client(opp)

    await ws_client.send_json(
        {ID: 2, TYPE: "zwave_js/network_status", ENTRY_ID: entry.entry_id}
    )
    msg = await ws_client.receive_json()
    result = msg["result"]

    assert result["client"]["ws_server_url"] == "ws://test:3000/zjs"
    assert result["client"]["server_version"] == "1.0.0"

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {ID: 3, TYPE: "zwave_js/network_status", ENTRY_ID: entry.entry_id}
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED


async def test_node_status(opp, multisensor_6, integration, opp_ws_client):
    """Test the node status websocket command."""
    entry = integration
    ws_client = await opp_ws_client(opp)

    node = multisensor_6
    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/node_status",
            ENTRY_ID: entry.entry_id,
            NODE_ID: node.node_id,
        }
    )
    msg = await ws_client.receive_json()
    result = msg["result"]

    assert result[NODE_ID] == 52
    assert result["ready"]
    assert result["is_routing"]
    assert not result["is_secure"]
    assert result["status"] == 1

    # Test getting non-existent node fails
    await ws_client.send_json(
        {
            ID: 4,
            TYPE: "zwave_js/node_status",
            ENTRY_ID: entry.entry_id,
            NODE_ID: 99999,
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 5,
            TYPE: "zwave_js/node_status",
            ENTRY_ID: entry.entry_id,
            NODE_ID: node.node_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED


async def test_node_metadata(opp, wallmote_central_scene, integration, opp_ws_client):
    """Test the node metadata websocket command."""
    entry = integration
    ws_client = await opp_ws_client(opp)

    node = wallmote_central_scene
    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/node_metadata",
            ENTRY_ID: entry.entry_id,
            NODE_ID: node.node_id,
        }
    )
    msg = await ws_client.receive_json()
    result = msg["result"]

    assert result[NODE_ID] == 35
    assert result["inclusion"] == (
        "To add the ZP3111 to the Z-Wave network (inclusion), place the Z-Wave "
        "primary controller into inclusion mode. Press the Program Switch of ZP3111 "
        "for sending the NIF. After sending NIF, Z-Wave will send the auto inclusion, "
        "otherwise, ZP3111 will go to sleep after 20 seconds."
    )
    assert result["exclusion"] == (
        "To remove the ZP3111 from the Z-Wave network (exclusion), place the Z-Wave "
        "primary controller into \u201cexclusion\u201d mode, and following its "
        "instruction to delete the ZP3111 to the controller. Press the Program Switch "
        "of ZP3111 once to be excluded."
    )
    assert result["reset"] == (
        "Remove cover to triggered tamper switch, LED flash once & send out Alarm "
        "Report. Press Program Switch 10 times within 10 seconds, ZP3111 will send "
        "the \u201cDevice Reset Locally Notification\u201d command and reset to the "
        "factory default. (Remark: This is to be used only in the case of primary "
        "controller being inoperable or otherwise unavailable.)"
    )
    assert result["manual"] == (
        "https://products.z-wavealliance.org/ProductManual/File?folder=&filename=MarketCertificationFiles/2479/ZP3111-5_R2_20170316.pdf"
    )
    assert not result["wakeup"]
    assert (
        result["device_database_url"]
        == "https://devices.zwave-js.io/?jumpTo=0x0086:0x0002:0x0082:0.0"
    )

    # Test getting non-existent node fails
    await ws_client.send_json(
        {
            ID: 4,
            TYPE: "zwave_js/node_metadata",
            ENTRY_ID: entry.entry_id,
            NODE_ID: 99999,
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 5,
            TYPE: "zwave_js/node_metadata",
            ENTRY_ID: entry.entry_id,
            NODE_ID: node.node_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED


async def test_ping_node(
    opp, wallmote_central_scene, integration, client, opp_ws_client
):
    """Test the ping_node websocket command."""
    entry = integration
    ws_client = await opp_ws_client(opp)
    node = wallmote_central_scene

    client.async_send_command.return_value = {"responded": True}

    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/ping_node",
            ENTRY_ID: entry.entry_id,
            NODE_ID: node.node_id,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"]

    # Test getting non-existent node fails
    await ws_client.send_json(
        {
            ID: 4,
            TYPE: "zwave_js/ping_node",
            ENTRY_ID: entry.entry_id,
            NODE_ID: 99999,
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 5,
            TYPE: "zwave_js/ping_node",
            ENTRY_ID: entry.entry_id,
            NODE_ID: node.node_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED


async def test_add_node(
    opp, nortek_thermostat_added_event, integration, client, opp_ws_client
):
    """Test the add_node websocket command."""
    entry = integration
    ws_client = await opp_ws_client(opp)

    client.async_send_command.return_value = {"success": True}

    await ws_client.send_json(
        {ID: 3, TYPE: "zwave_js/add_node", ENTRY_ID: entry.entry_id}
    )

    msg = await ws_client.receive_json()
    assert msg["success"]

    event = Event(
        type="inclusion started",
        data={
            "source": "controller",
            "event": "inclusion started",
            "secure": False,
        },
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "inclusion started"

    client.driver.receive_event(nortek_thermostat_added_event)
    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "node added"
    node_details = {
        "node_id": 67,
        "status": 0,
        "ready": False,
    }
    assert msg["event"]["node"] == node_details

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "device registered"
    # Check the keys of the device item
    assert list(msg["event"]["device"]) == ["name", "id", "manufacturer", "model"]

    # Test receiving interview events
    event = Event(
        type="interview started",
        data={"source": "node", "event": "interview started", "nodeId": 67},
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "interview started"

    event = Event(
        type="interview stage completed",
        data={
            "source": "node",
            "event": "interview stage completed",
            "stageName": "NodeInfo",
            "nodeId": 67,
        },
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "interview stage completed"
    assert msg["event"]["stage"] == "NodeInfo"

    event = Event(
        type="interview completed",
        data={"source": "node", "event": "interview completed", "nodeId": 67},
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "interview completed"

    event = Event(
        type="interview failed",
        data={"source": "node", "event": "interview failed", "nodeId": 67},
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "interview failed"

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {ID: 4, TYPE: "zwave_js/add_node", ENTRY_ID: entry.entry_id}
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED


async def test_cancel_inclusion_exclusion(opp, integration, client, opp_ws_client):
    """Test cancelling the inclusion and exclusion process."""
    entry = integration
    ws_client = await opp_ws_client(opp)

    client.async_send_command.return_value = {"success": True}

    await ws_client.send_json(
        {ID: 4, TYPE: "zwave_js/stop_inclusion", ENTRY_ID: entry.entry_id}
    )

    msg = await ws_client.receive_json()
    assert msg["success"]

    await ws_client.send_json(
        {ID: 5, TYPE: "zwave_js/stop_exclusion", ENTRY_ID: entry.entry_id}
    )

    msg = await ws_client.receive_json()
    assert msg["success"]

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {ID: 6, TYPE: "zwave_js/stop_inclusion", ENTRY_ID: entry.entry_id}
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED

    await ws_client.send_json(
        {ID: 7, TYPE: "zwave_js/stop_exclusion", ENTRY_ID: entry.entry_id}
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED


async def test_remove_node(
    opp,
    integration,
    client,
    opp_ws_client,
    nortek_thermostat,
    nortek_thermostat_removed_event,
):
    """Test the remove_node websocket command."""
    entry = integration
    ws_client = await opp_ws_client(opp)

    client.async_send_command.return_value = {"success": True}

    await ws_client.send_json(
        {ID: 3, TYPE: "zwave_js/remove_node", ENTRY_ID: entry.entry_id}
    )

    msg = await ws_client.receive_json()
    assert msg["success"]

    event = Event(
        type="exclusion started",
        data={
            "source": "controller",
            "event": "exclusion started",
            "secure": False,
        },
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "exclusion started"

    dev_reg = dr.async_get(opp)

    # Create device registry entry for mock node
    device = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "3245146787-67")},
        name="Node 67",
    )

    # Fire node removed event
    client.driver.receive_event(nortek_thermostat_removed_event)
    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "node removed"

    # Verify device was removed from device registry
    device = dev_reg.async_get_device(
        identifiers={(DOMAIN, "3245146787-67")},
    )
    assert device is None

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {ID: 4, TYPE: "zwave_js/remove_node", ENTRY_ID: entry.entry_id}
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED


async def test_replace_failed_node(
    opp,
    nortek_thermostat,
    integration,
    client,
    opp_ws_client,
    nortek_thermostat_added_event,
    nortek_thermostat_removed_event,
):
    """Test the replace_failed_node websocket command."""
    entry = integration
    ws_client = await opp_ws_client(opp)

    dev_reg = dr.async_get(opp)

    # Create device registry entry for mock node
    dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "3245146787-67")},
        name="Node 67",
    )

    client.async_send_command.return_value = {"success": True}

    # Order of events we receive for a successful replacement is `inclusion started`,
    # `inclusion stopped`, `node removed`, `node added`, then interview stages.
    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/replace_failed_node",
            ENTRY_ID: entry.entry_id,
            NODE_ID: 67,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"]

    event = Event(
        type="inclusion started",
        data={
            "source": "controller",
            "event": "inclusion started",
            "secure": False,
        },
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "inclusion started"

    event = Event(
        type="inclusion stopped",
        data={
            "source": "controller",
            "event": "inclusion stopped",
            "secure": False,
        },
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "inclusion stopped"

    # Fire node removed event
    client.driver.receive_event(nortek_thermostat_removed_event)
    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "node removed"

    # Verify device was removed from device registry
    device = dev_reg.async_get_device(
        identifiers={(DOMAIN, "3245146787-67")},
    )
    assert device is None

    client.driver.receive_event(nortek_thermostat_added_event)
    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "node added"
    node_details = {
        "node_id": 67,
        "status": 0,
        "ready": False,
    }
    assert msg["event"]["node"] == node_details

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "device registered"
    # Check the keys of the device item
    assert list(msg["event"]["device"]) == ["name", "id", "manufacturer", "model"]

    # Test receiving interview events
    event = Event(
        type="interview started",
        data={"source": "node", "event": "interview started", "nodeId": 67},
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "interview started"

    event = Event(
        type="interview stage completed",
        data={
            "source": "node",
            "event": "interview stage completed",
            "stageName": "NodeInfo",
            "nodeId": 67,
        },
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "interview stage completed"
    assert msg["event"]["stage"] == "NodeInfo"

    event = Event(
        type="interview completed",
        data={"source": "node", "event": "interview completed", "nodeId": 67},
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "interview completed"

    event = Event(
        type="interview failed",
        data={"source": "node", "event": "interview failed", "nodeId": 67},
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "interview failed"

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 4,
            TYPE: "zwave_js/replace_failed_node",
            ENTRY_ID: entry.entry_id,
            NODE_ID: 67,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED


async def test_remove_failed_node(
    opp,
    nortek_thermostat,
    integration,
    client,
    opp_ws_client,
    nortek_thermostat_removed_event,
):
    """Test the remove_failed_node websocket command."""
    entry = integration
    ws_client = await opp_ws_client(opp)

    client.async_send_command.return_value = {"success": True}

    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/remove_failed_node",
            ENTRY_ID: entry.entry_id,
            NODE_ID: 67,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]

    dev_reg = dr.async_get(opp)

    # Create device registry entry for mock node
    device = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "3245146787-67")},
        name="Node 67",
    )

    # Fire node removed event
    client.driver.receive_event(nortek_thermostat_removed_event)
    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "node removed"

    # Verify device was removed from device registry
    device = dev_reg.async_get_device(
        identifiers={(DOMAIN, "3245146787-67")},
    )
    assert device is None

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 4,
            TYPE: "zwave_js/remove_failed_node",
            ENTRY_ID: entry.entry_id,
            NODE_ID: 67,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED


async def test_begin_healing_network(
    opp,
    integration,
    client,
    opp_ws_client,
):
    """Test the begin_healing_network websocket command."""
    entry = integration
    ws_client = await opp_ws_client(opp)

    client.async_send_command.return_value = {"success": True}

    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/begin_healing_network",
            ENTRY_ID: entry.entry_id,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"]

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 4,
            TYPE: "zwave_js/begin_healing_network",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED


async def test_subscribe_heal_network_progress(
    opp, integration, client, opp_ws_client
):
    """Test the subscribe_heal_network_progress command."""
    entry = integration
    ws_client = await opp_ws_client(opp)

    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/subscribe_heal_network_progress",
            ENTRY_ID: entry.entry_id,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]

    # Fire heal network progress
    event = Event(
        "heal network progress",
        {
            "source": "controller",
            "event": "heal network progress",
            "progress": {67: "pending"},
        },
    )
    client.driver.controller.receive_event(event)
    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "heal network progress"
    assert msg["event"]["heal_node_status"] == {"67": "pending"}

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 4,
            TYPE: "zwave_js/subscribe_heal_network_progress",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED


async def test_stop_healing_network(
    opp,
    integration,
    client,
    opp_ws_client,
):
    """Test the stop_healing_network websocket command."""
    entry = integration
    ws_client = await opp_ws_client(opp)

    client.async_send_command.return_value = {"success": True}

    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/stop_healing_network",
            ENTRY_ID: entry.entry_id,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"]

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 4,
            TYPE: "zwave_js/stop_healing_network",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED


async def test_heal_node(
    opp,
    integration,
    client,
    opp_ws_client,
):
    """Test the heal_node websocket command."""
    entry = integration
    ws_client = await opp_ws_client(opp)

    client.async_send_command.return_value = {"success": True}

    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/heal_node",
            ENTRY_ID: entry.entry_id,
            NODE_ID: 67,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"]

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 4,
            TYPE: "zwave_js/heal_node",
            ENTRY_ID: entry.entry_id,
            NODE_ID: 67,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED


async def test_refresh_node_info(
    opp, client, multisensor_6, integration, opp_ws_client
):
    """Test that the refresh_node_info WS API call works."""
    entry = integration
    ws_client = await opp_ws_client(opp)

    client.async_send_command_no_wait.return_value = None
    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/refresh_node_info",
            ENTRY_ID: entry.entry_id,
            NODE_ID: 52,
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "node.refresh_info"
    assert args["nodeId"] == 52

    event = Event(
        type="interview started",
        data={"source": "node", "event": "interview started", "nodeId": 52},
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "interview started"

    event = Event(
        type="interview stage completed",
        data={
            "source": "node",
            "event": "interview stage completed",
            "stageName": "NodeInfo",
            "nodeId": 52,
        },
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "interview stage completed"
    assert msg["event"]["stage"] == "NodeInfo"

    event = Event(
        type="interview completed",
        data={"source": "node", "event": "interview completed", "nodeId": 52},
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "interview completed"

    event = Event(
        type="interview failed",
        data={"source": "node", "event": "interview failed", "nodeId": 52},
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "interview failed"

    client.async_send_command_no_wait.reset_mock()

    # Test getting non-existent node fails
    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "zwave_js/refresh_node_info",
            ENTRY_ID: entry.entry_id,
            NODE_ID: 9999,
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/refresh_node_info",
            ENTRY_ID: entry.entry_id,
            NODE_ID: 52,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED


async def test_refresh_node_values(
    opp, client, multisensor_6, integration, opp_ws_client
):
    """Test that the refresh_node_values WS API call works."""
    entry = integration
    ws_client = await opp_ws_client(opp)

    client.async_send_command_no_wait.return_value = None
    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/refresh_node_values",
            ENTRY_ID: entry.entry_id,
            NODE_ID: 52,
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "node.refresh_values"
    assert args["nodeId"] == 52

    client.async_send_command_no_wait.reset_mock()

    # Test getting non-existent node fails
    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "zwave_js/refresh_node_values",
            ENTRY_ID: entry.entry_id,
            NODE_ID: 99999,
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND

    # Test getting non-existent entry fails
    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/refresh_node_values",
            ENTRY_ID: "fake_entry_id",
            NODE_ID: 52,
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND


async def test_refresh_node_cc_values(
    opp, client, multisensor_6, integration, opp_ws_client
):
    """Test that the refresh_node_cc_values WS API call works."""
    entry = integration
    ws_client = await opp_ws_client(opp)

    client.async_send_command_no_wait.return_value = None
    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/refresh_node_cc_values",
            ENTRY_ID: entry.entry_id,
            NODE_ID: 52,
            COMMAND_CLASS_ID: 112,
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "node.refresh_cc_values"
    assert args["nodeId"] == 52
    assert args["commandClass"] == 112

    client.async_send_command_no_wait.reset_mock()

    # Test using invalid CC ID fails
    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "zwave_js/refresh_node_cc_values",
            ENTRY_ID: entry.entry_id,
            NODE_ID: 52,
            COMMAND_CLASS_ID: 9999,
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND

    # Test getting non-existent node fails
    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/refresh_node_cc_values",
            ENTRY_ID: entry.entry_id,
            NODE_ID: 9999,
            COMMAND_CLASS_ID: 112,
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 4,
            TYPE: "zwave_js/refresh_node_cc_values",
            ENTRY_ID: entry.entry_id,
            NODE_ID: 52,
            COMMAND_CLASS_ID: 112,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED


async def test_set_config_parameter(
    opp, client, opp_ws_client, multisensor_6, integration
):
    """Test the set_config_parameter service."""
    entry = integration
    ws_client = await opp_ws_client(opp)

    client.async_send_command_no_wait.return_value = None

    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/set_config_parameter",
            ENTRY_ID: entry.entry_id,
            NODE_ID: 52,
            PROPERTY: 102,
            PROPERTY_KEY: 1,
            VALUE: 1,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 52
    assert args["valueId"] == {
        "commandClassName": "Configuration",
        "commandClass": 112,
        "endpoint": 0,
        "property": 102,
        "propertyName": "Group 2: Send battery reports",
        "propertyKey": 1,
        "metadata": {
            "type": "number",
            "readable": True,
            "writeable": True,
            "valueSize": 4,
            "min": 0,
            "max": 1,
            "default": 1,
            "format": 0,
            "allowManualEntry": True,
            "label": "Group 2: Send battery reports",
            "description": "Include battery information in periodic reports to Group 2",
            "isFromConfig": True,
        },
        "value": 0,
    }
    assert args["value"] == 1

    client.async_send_command_no_wait.reset_mock()

    with patch(
        "openpeerpower.components.zwave_js.api.async_set_config_parameter",
    ) as set_param_mock:
        set_param_mock.side_effect = InvalidNewValue("test")
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "zwave_js/set_config_parameter",
                ENTRY_ID: entry.entry_id,
                NODE_ID: 52,
                PROPERTY: 102,
                PROPERTY_KEY: 1,
                VALUE: 1,
            }
        )

        msg = await ws_client.receive_json()

        assert len(client.async_send_command_no_wait.call_args_list) == 0
        assert not msg["success"]
        assert msg["error"]["code"] == "not_supported"
        assert msg["error"]["message"] == "test"

        set_param_mock.side_effect = NotFoundError("test")
        await ws_client.send_json(
            {
                ID: 3,
                TYPE: "zwave_js/set_config_parameter",
                ENTRY_ID: entry.entry_id,
                NODE_ID: 52,
                PROPERTY: 102,
                PROPERTY_KEY: 1,
                VALUE: 1,
            }
        )

        msg = await ws_client.receive_json()

        assert len(client.async_send_command_no_wait.call_args_list) == 0
        assert not msg["success"]
        assert msg["error"]["code"] == "not_found"
        assert msg["error"]["message"] == "test"

        set_param_mock.side_effect = SetValueFailed("test")
        await ws_client.send_json(
            {
                ID: 4,
                TYPE: "zwave_js/set_config_parameter",
                ENTRY_ID: entry.entry_id,
                NODE_ID: 52,
                PROPERTY: 102,
                PROPERTY_KEY: 1,
                VALUE: 1,
            }
        )

        msg = await ws_client.receive_json()

        assert len(client.async_send_command_no_wait.call_args_list) == 0
        assert not msg["success"]
        assert msg["error"]["code"] == "unknown_error"
        assert msg["error"]["message"] == "test"

    # Test getting non-existent node fails
    await ws_client.send_json(
        {
            ID: 5,
            TYPE: "zwave_js/set_config_parameter",
            ENTRY_ID: entry.entry_id,
            NODE_ID: 9999,
            PROPERTY: 102,
            PROPERTY_KEY: 1,
            VALUE: 1,
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 6,
            TYPE: "zwave_js/set_config_parameter",
            ENTRY_ID: entry.entry_id,
            NODE_ID: 52,
            PROPERTY: 102,
            PROPERTY_KEY: 1,
            VALUE: 1,
        }
    )

    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED


async def test_get_config_parameters(opp, multisensor_6, integration, opp_ws_client):
    """Test the get config parameters websocket command."""
    entry = integration
    ws_client = await opp_ws_client(opp)
    node = multisensor_6

    # Test getting configuration parameter values
    await ws_client.send_json(
        {
            ID: 4,
            TYPE: "zwave_js/get_config_parameters",
            ENTRY_ID: entry.entry_id,
            NODE_ID: node.node_id,
        }
    )
    msg = await ws_client.receive_json()
    result = msg["result"]

    assert len(result) == 61
    key = "52-112-0-2"
    assert result[key]["property"] == 2
    assert result[key]["property_key"] is None
    assert result[key]["metadata"]["type"] == "number"
    assert result[key]["configuration_value_type"] == "enumerated"
    assert result[key]["metadata"]["states"]

    key = "52-112-0-201-255"
    assert result[key]["property_key"] == 255

    # Test getting non-existent node config params fails
    await ws_client.send_json(
        {
            ID: 5,
            TYPE: "zwave_js/get_config_parameters",
            ENTRY_ID: entry.entry_id,
            NODE_ID: 99999,
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 6,
            TYPE: "zwave_js/get_config_parameters",
            ENTRY_ID: entry.entry_id,
            NODE_ID: node.node_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED


async def test_dump_view(integration, opp_client):
    """Test the HTTP dump view."""
    client = await opp_client()
    with patch(
        "zwave_js_server.dump.dump_msgs",
        return_value=[{"hello": "world"}, {"second": "msg"}],
    ):
        resp = await client.get(f"/api/zwave_js/dump/{integration.entry_id}")
    assert resp.status == 200
    assert json.loads(await resp.text()) == [{"hello": "world"}, {"second": "msg"}]


async def test_firmware_upload_view(
    opp, multisensor_6, integration, opp_client, firmware_file
):
    """Test the HTTP firmware upload view."""
    client = await opp_client()
    with patch(
        "openpeerpower.components.zwave_js.api.begin_firmware_update",
    ) as mock_cmd:
        resp = await client.post(
            f"/api/zwave_js/firmware/upload/{integration.entry_id}/{multisensor_6.node_id}",
            data={"file": firmware_file},
        )
        assert mock_cmd.call_args[0][1:4] == (multisensor_6, "file", bytes(10))
        assert json.loads(await resp.text()) is None


async def test_firmware_upload_view_failed_command(
    opp, multisensor_6, integration, opp_client, firmware_file
):
    """Test failed command for the HTTP firmware upload view."""
    client = await opp_client()
    with patch(
        "openpeerpower.components.zwave_js.api.begin_firmware_update",
        side_effect=FailedCommand("test", "test"),
    ):
        resp = await client.post(
            f"/api/zwave_js/firmware/upload/{integration.entry_id}/{multisensor_6.node_id}",
            data={"file": firmware_file},
        )
        assert resp.status == 400


async def test_firmware_upload_view_invalid_payload(
    opp, multisensor_6, integration, opp_client
):
    """Test an invalid payload for the HTTP firmware upload view."""
    client = await opp_client()
    resp = await client.post(
        f"/api/zwave_js/firmware/upload/{integration.entry_id}/{multisensor_6.node_id}",
        data={"wrong_key": bytes(10)},
    )
    assert resp.status == 400


@pytest.mark.parametrize(
    "method, url",
    [
        ("get", "/api/zwave_js/dump/INVALID"),
        ("post", "/api/zwave_js/firmware/upload/INVALID/1"),
    ],
)
async def test_view_invalid_entry_id(integration, opp_client, method, url):
    """Test an invalid config entry id parameter."""
    client = await opp_client()
    resp = await client.request(method, url)
    assert resp.status == 400


@pytest.mark.parametrize(
    "method, url", [("post", "/api/zwave_js/firmware/upload/{}/111")]
)
async def test_view_invalid_node_id(integration, opp_client, method, url):
    """Test an invalid config entry id parameter."""
    client = await opp_client()
    resp = await client.request(method, url.format(integration.entry_id))
    assert resp.status == 404


async def test_subscribe_logs(opp, integration, client, opp_ws_client):
    """Test the subscribe_logs websocket command."""
    entry = integration
    ws_client = await opp_ws_client(opp)

    client.async_send_command.return_value = {}

    await ws_client.send_json(
        {ID: 1, TYPE: "zwave_js/subscribe_logs", ENTRY_ID: entry.entry_id}
    )

    msg = await ws_client.receive_json()
    assert msg["success"]

    event = Event(
        type="logging",
        data={
            "source": "driver",
            "event": "logging",
            "message": "test",
            "formattedMessage": "test",
            "direction": ">",
            "level": "debug",
            "primaryTags": "tag",
            "secondaryTags": "tag2",
            "secondaryTagPadding": 0,
            "multiline": False,
            "timestamp": "time",
            "label": "label",
        },
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"] == {
        "message": ["test"],
        "level": "debug",
        "primary_tags": "tag",
        "timestamp": "time",
    }

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {ID: 2, TYPE: "zwave_js/subscribe_logs", ENTRY_ID: entry.entry_id}
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED


async def test_update_log_config(opp, client, integration, opp_ws_client):
    """Test that the update_log_config WS API call works and that schema validation works."""
    entry = integration
    ws_client = await opp_ws_client(opp)

    # Test we can set log level
    client.async_send_command.return_value = {"success": True}
    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/update_log_config",
            ENTRY_ID: entry.entry_id,
            CONFIG: {LEVEL: "Error"},
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "driver.update_log_config"
    assert args["config"] == {"level": "error"}

    client.async_send_command.reset_mock()

    # Test we can set logToFile to True
    client.async_send_command.return_value = {"success": True}
    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "zwave_js/update_log_config",
            ENTRY_ID: entry.entry_id,
            CONFIG: {LOG_TO_FILE: True, FILENAME: "/test"},
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "driver.update_log_config"
    assert args["config"] == {"logToFile": True, "filename": "/test"}

    client.async_send_command.reset_mock()

    # Test all parameters
    client.async_send_command.return_value = {"success": True}
    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/update_log_config",
            ENTRY_ID: entry.entry_id,
            CONFIG: {
                LEVEL: "Error",
                LOG_TO_FILE: True,
                FILENAME: "/test",
                FORCE_CONSOLE: True,
                ENABLED: True,
            },
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "driver.update_log_config"
    assert args["config"] == {
        "level": "error",
        "logToFile": True,
        "filename": "/test",
        "forceConsole": True,
        "enabled": True,
    }

    client.async_send_command.reset_mock()

    # Test error when setting unrecognized log level
    await ws_client.send_json(
        {
            ID: 4,
            TYPE: "zwave_js/update_log_config",
            ENTRY_ID: entry.entry_id,
            CONFIG: {LEVEL: "bad_log_level"},
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert "error" in msg and "value must be one of" in msg["error"]["message"]

    # Test error without service data
    await ws_client.send_json(
        {
            ID: 5,
            TYPE: "zwave_js/update_log_config",
            ENTRY_ID: entry.entry_id,
            CONFIG: {},
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert "error" in msg and "must contain at least one of" in msg["error"]["message"]

    # Test error if we set logToFile to True without providing filename
    await ws_client.send_json(
        {
            ID: 6,
            TYPE: "zwave_js/update_log_config",
            ENTRY_ID: entry.entry_id,
            CONFIG: {LOG_TO_FILE: True},
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert (
        "error" in msg
        and "must be provided if logging to file" in msg["error"]["message"]
    )

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 7,
            TYPE: "zwave_js/update_log_config",
            ENTRY_ID: entry.entry_id,
            CONFIG: {LEVEL: "Error"},
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED


async def test_get_log_config(opp, client, integration, opp_ws_client):
    """Test that the get_log_config WS API call works."""
    entry = integration
    ws_client = await opp_ws_client(opp)

    # Test we can get log configuration
    client.async_send_command.return_value = {
        "success": True,
        "config": {
            "enabled": True,
            "level": "error",
            "logToFile": False,
            "filename": "/test.txt",
            "forceConsole": False,
        },
    }
    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/get_log_config",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()
    assert msg["result"]
    assert msg["success"]

    log_config = msg["result"]
    assert log_config["enabled"]
    assert log_config["level"] == LogLevel.ERROR
    assert log_config["log_to_file"] is False
    assert log_config["filename"] == "/test.txt"
    assert log_config["force_console"] is False

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "zwave_js/get_log_config",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED


async def test_data_collection(opp, client, integration, opp_ws_client):
    """Test that the data collection WS API commands work."""
    entry = integration
    ws_client = await opp_ws_client(opp)

    client.async_send_command.return_value = {"statisticsEnabled": False}
    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/data_collection_status",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()
    result = msg["result"]
    assert result == {"opted_in": None, "enabled": False}

    assert len(client.async_send_command.call_args_list) == 1
    assert client.async_send_command.call_args[0][0] == {
        "command": "driver.is_statistics_enabled"
    }

    assert CONF_DATA_COLLECTION_OPTED_IN not in entry.data

    client.async_send_command.reset_mock()

    client.async_send_command.return_value = {}
    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "zwave_js/update_data_collection_preference",
            ENTRY_ID: entry.entry_id,
            OPTED_IN: True,
        }
    )
    msg = await ws_client.receive_json()
    result = msg["result"]
    assert result is None

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "driver.enable_statistics"
    assert args["applicationName"] == "Open Peer Power"
    assert entry.data[CONF_DATA_COLLECTION_OPTED_IN]

    client.async_send_command.reset_mock()

    client.async_send_command.return_value = {}
    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/update_data_collection_preference",
            ENTRY_ID: entry.entry_id,
            OPTED_IN: False,
        }
    )
    msg = await ws_client.receive_json()
    result = msg["result"]
    assert result is None

    assert len(client.async_send_command.call_args_list) == 1
    assert client.async_send_command.call_args[0][0] == {
        "command": "driver.disable_statistics"
    }
    assert not entry.data[CONF_DATA_COLLECTION_OPTED_IN]

    client.async_send_command.reset_mock()

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 4,
            TYPE: "zwave_js/data_collection_status",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED

    await ws_client.send_json(
        {
            ID: 5,
            TYPE: "zwave_js/update_data_collection_preference",
            ENTRY_ID: entry.entry_id,
            OPTED_IN: True,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED


async def test_abort_firmware_update(
    opp, client, multisensor_6, integration, opp_ws_client
):
    """Test that the abort_firmware_update WS API call works."""
    entry = integration
    ws_client = await opp_ws_client(opp)

    client.async_send_command_no_wait.return_value = {}
    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/abort_firmware_update",
            ENTRY_ID: entry.entry_id,
            NODE_ID: multisensor_6.node_id,
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "node.abort_firmware_update"
    assert args["nodeId"] == multisensor_6.node_id


async def test_abort_firmware_update_failures(
    opp, integration, multisensor_6, client, opp_ws_client
):
    """Test failures for the abort_firmware_update websocket command."""
    entry = integration
    ws_client = await opp_ws_client(opp)
    # Test sending command with improper entry ID fails
    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/abort_firmware_update",
            ENTRY_ID: "fake_entry_id",
            NODE_ID: multisensor_6.node_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND

    # Test sending command with improper node ID fails
    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "zwave_js/abort_firmware_update",
            ENTRY_ID: entry.entry_id,
            NODE_ID: multisensor_6.node_id + 100,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/abort_firmware_update",
            ENTRY_ID: entry.entry_id,
            NODE_ID: multisensor_6.node_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED


async def test_subscribe_firmware_update_status(
    opp, integration, multisensor_6, client, opp_ws_client
):
    """Test the subscribe_firmware_update_status websocket command."""
    entry = integration
    ws_client = await opp_ws_client(opp)

    client.async_send_command_no_wait.return_value = {}

    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/subscribe_firmware_update_status",
            ENTRY_ID: entry.entry_id,
            NODE_ID: multisensor_6.node_id,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]

    event = Event(
        type="firmware update progress",
        data={
            "source": "node",
            "event": "firmware update progress",
            "nodeId": multisensor_6.node_id,
            "sentFragments": 1,
            "totalFragments": 10,
        },
    )
    multisensor_6.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"] == {
        "event": "firmware update progress",
        "sent_fragments": 1,
        "total_fragments": 10,
    }

    event = Event(
        type="firmware update finished",
        data={
            "source": "node",
            "event": "firmware update finished",
            "nodeId": multisensor_6.node_id,
            "status": 255,
            "waitTime": 10,
        },
    )
    multisensor_6.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"] == {
        "event": "firmware update finished",
        "status": 255,
        "wait_time": 10,
    }


async def test_subscribe_firmware_update_status_failures(
    opp, integration, multisensor_6, client, opp_ws_client
):
    """Test failures for the subscribe_firmware_update_status websocket command."""
    entry = integration
    ws_client = await opp_ws_client(opp)
    # Test sending command with improper entry ID fails
    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/subscribe_firmware_update_status",
            ENTRY_ID: "fake_entry_id",
            NODE_ID: multisensor_6.node_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND

    # Test sending command with improper node ID fails
    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "zwave_js/subscribe_firmware_update_status",
            ENTRY_ID: entry.entry_id,
            NODE_ID: multisensor_6.node_id + 100,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/subscribe_firmware_update_status",
            ENTRY_ID: entry.entry_id,
            NODE_ID: multisensor_6.node_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED


async def test_check_for_config_updates(opp, client, integration, opp_ws_client):
    """Test that the check_for_config_updates WS API call works."""
    entry = integration
    ws_client = await opp_ws_client(opp)

    # Test we can get log configuration
    client.async_send_command.return_value = {
        "updateAvailable": True,
        "newVersion": "test",
    }
    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/check_for_config_updates",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()
    assert msg["result"]
    assert msg["success"]

    config_update = msg["result"]
    assert config_update["update_available"]
    assert config_update["new_version"] == "test"

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "zwave_js/check_for_config_updates",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED

    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/check_for_config_updates",
            ENTRY_ID: "INVALID",
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND


async def test_install_config_update(opp, client, integration, opp_ws_client):
    """Test that the install_config_update WS API call works."""
    entry = integration
    ws_client = await opp_ws_client(opp)

    # Test we can get log configuration
    client.async_send_command.return_value = {"success": True}
    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/install_config_update",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()
    assert msg["result"]
    assert msg["success"]

    # Test sending command with not loaded entry fails
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "zwave_js/install_config_update",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED

    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/install_config_update",
            ENTRY_ID: "INVALID",
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND
