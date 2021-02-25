"""Test Z-Wave JS (value notification) events."""
from zwave_js_server.event import Event

from tests.common import async_capture_events


async def test_scenes(opp, hank_binary_switch, integration, client):
    """Test scene events."""
    # just pick a random node to fake the value notification events
    node = hank_binary_switch
    events = async_capture_events.opp, "zwave_js_event")

    # Publish fake Basic Set value notification
    event = Event(
        type="value notification",
        data={
            "source": "node",
            "event": "value notification",
            "nodeId": 32,
            "args": {
                "commandClassName": "Basic",
                "commandClass": 32,
                "endpoint": 0,
                "property": "event",
                "propertyName": "event",
                "value": 255,
                "metadata": {
                    "type": "number",
                    "readable": True,
                    "writeable": False,
                    "min": 0,
                    "max": 255,
                    "label": "Event value",
                },
                "ccVersion": 1,
            },
        },
    )
    node.receive_event(event)
    # wait for the event
    await opp.async_block_till_done()
    assert len(events) == 1
    assert events[0].data["home_id"] == client.driver.controller.home_id
    assert events[0].data["node_id"] == 32
    assert events[0].data["endpoint"] == 0
    assert events[0].data["command_class"] == 32
    assert events[0].data["command_class_name"] == "Basic"
    assert events[0].data["label"] == "Event value"
    assert events[0].data["value"] == 255

    # Publish fake Scene Activation value notification
    event = Event(
        type="value notification",
        data={
            "source": "node",
            "event": "value notification",
            "nodeId": 32,
            "args": {
                "commandClassName": "Scene Activation",
                "commandClass": 43,
                "endpoint": 0,
                "property": "SceneID",
                "propertyName": "SceneID",
                "value": 16,
                "metadata": {
                    "type": "number",
                    "readable": True,
                    "writeable": False,
                    "min": 0,
                    "max": 255,
                    "label": "Scene ID",
                },
                "ccVersion": 3,
            },
        },
    )
    node.receive_event(event)
    # wait for the event
    await opp.async_block_till_done()
    assert len(events) == 2
    assert events[1].data["command_class"] == 43
    assert events[1].data["command_class_name"] == "Scene Activation"
    assert events[1].data["label"] == "Scene ID"
    assert events[1].data["value"] == 16

    # Publish fake Central Scene value notification
    event = Event(
        type="value notification",
        data={
            "source": "node",
            "event": "value notification",
            "nodeId": 32,
            "args": {
                "commandClassName": "Central Scene",
                "commandClass": 91,
                "endpoint": 0,
                "property": "scene",
                "propertyKey": "001",
                "propertyName": "scene",
                "propertyKeyName": "001",
                "value": 4,
                "metadata": {
                    "type": "number",
                    "readable": True,
                    "writeable": False,
                    "min": 0,
                    "max": 255,
                    "label": "Scene 001",
                    "states": {
                        "0": "KeyPressed",
                        "1": "KeyReleased",
                        "2": "KeyHeldDown",
                        "3": "KeyPressed2x",
                        "4": "KeyPressed3x",
                        "5": "KeyPressed4x",
                        "6": "KeyPressed5x",
                    },
                },
                "ccVersion": 3,
            },
        },
    )
    node.receive_event(event)
    # wait for the event
    await opp.async_block_till_done()
    assert len(events) == 3
    assert events[2].data["command_class"] == 91
    assert events[2].data["command_class_name"] == "Central Scene"
    assert events[2].data["label"] == "Scene 001"
    assert events[2].data["value"] == "KeyPressed3x"


async def test_notifications.opp, hank_binary_switch, integration, client):
    """Test notification events."""
    # just pick a random node to fake the value notification events
    node = hank_binary_switch
    events = async_capture_events.opp, "zwave_js_event")

    # Publish fake Basic Set value notification
    event = Event(
        type="notification",
        data={
            "source": "node",
            "event": "notification",
            "nodeId": 23,
            "notificationLabel": "Keypad lock operation",
            "parameters": {"userId": 1},
        },
    )
    node.receive_event(event)
    # wait for the event
    await opp.async_block_till_done()
    assert len(events) == 1
    assert events[0].data["type"] == "notification"
    assert events[0].data["home_id"] == client.driver.controller.home_id
    assert events[0].data["node_id"] == 32
    assert events[0].data["label"] == "Keypad lock operation"
    assert events[0].data["parameters"]["userId"] == 1
