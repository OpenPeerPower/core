"""Philips Hue sensors platform tests."""
import asyncio
from unittest.mock import Mock

import aiohue

from openpeerpower.components.hue.hue_event import CONF_HUE_EVENT

from .conftest import create_mock_bridge, setup_bridge_for_sensors as setup_bridge

PRESENCE_SENSOR_1_PRESENT = {
    "state": {"presence": True, "lastupdated": "2019-01-01T01:00:00"},
    "swupdate": {"state": "noupdates", "lastinstall": "2019-01-01T00:00:00"},
    "config": {
        "on": True,
        "battery": 100,
        "reachable": True,
        "alert": "none",
        "ledindication": False,
        "usertest": False,
        "sensitivity": 2,
        "sensitivitymax": 2,
        "pending": [],
    },
    "name": "Living room sensor",
    "type": "ZLLPresence",
    "modelid": "SML001",
    "manufacturername": "Philips",
    "productname": "Hue motion sensor",
    "swversion": "6.1.1.27575",
    "uniqueid": "00:11:22:33:44:55:66:77-02-0406",
    "capabilities": {"certified": True},
}
LIGHT_LEVEL_SENSOR_1 = {
    "state": {
        "lightlevel": 1,
        "dark": True,
        "daylight": True,
        "lastupdated": "2019-01-01T01:00:00",
    },
    "swupdate": {"state": "noupdates", "lastinstall": "2019-01-01T00:00:00"},
    "config": {
        "on": True,
        "battery": 100,
        "reachable": True,
        "alert": "none",
        "tholddark": 12467,
        "tholdoffset": 7000,
        "ledindication": False,
        "usertest": False,
        "pending": [],
    },
    "name": "Hue ambient light sensor 1",
    "type": "ZLLLightLevel",
    "modelid": "SML001",
    "manufacturername": "Philips",
    "productname": "Hue ambient light sensor",
    "swversion": "6.1.1.27575",
    "uniqueid": "00:11:22:33:44:55:66:77-02-0400",
    "capabilities": {"certified": True},
}
TEMPERATURE_SENSOR_1 = {
    "state": {"temperature": 1775, "lastupdated": "2019-01-01T01:00:00"},
    "swupdate": {"state": "noupdates", "lastinstall": "2019-01-01T01:00:00"},
    "config": {
        "on": True,
        "battery": 100,
        "reachable": True,
        "alert": "none",
        "ledindication": False,
        "usertest": False,
        "pending": [],
    },
    "name": "Hue temperature sensor 1",
    "type": "ZLLTemperature",
    "modelid": "SML001",
    "manufacturername": "Philips",
    "productname": "Hue temperature sensor",
    "swversion": "6.1.1.27575",
    "uniqueid": "00:11:22:33:44:55:66:77-02-0402",
    "capabilities": {"certified": True},
}
PRESENCE_SENSOR_2_NOT_PRESENT = {
    "state": {"presence": False, "lastupdated": "2019-01-01T00:00:00"},
    "swupdate": {"state": "noupdates", "lastinstall": "2019-01-01T01:00:00"},
    "config": {
        "on": True,
        "battery": 100,
        "reachable": True,
        "alert": "none",
        "ledindication": False,
        "usertest": False,
        "sensitivity": 2,
        "sensitivitymax": 2,
        "pending": [],
    },
    "name": "Kitchen sensor",
    "type": "ZLLPresence",
    "modelid": "SML001",
    "manufacturername": "Philips",
    "productname": "Hue motion sensor",
    "swversion": "6.1.1.27575",
    "uniqueid": "00:11:22:33:44:55:66:88-02-0406",
    "capabilities": {"certified": True},
}
LIGHT_LEVEL_SENSOR_2 = {
    "state": {
        "lightlevel": 10001,
        "dark": True,
        "daylight": True,
        "lastupdated": "2019-01-01T01:00:00",
    },
    "swupdate": {"state": "noupdates", "lastinstall": "2019-01-01T00:00:00"},
    "config": {
        "on": True,
        "battery": 100,
        "reachable": True,
        "alert": "none",
        "tholddark": 12467,
        "tholdoffset": 7000,
        "ledindication": False,
        "usertest": False,
        "pending": [],
    },
    "name": "Hue ambient light sensor 2",
    "type": "ZLLLightLevel",
    "modelid": "SML001",
    "manufacturername": "Philips",
    "productname": "Hue ambient light sensor",
    "swversion": "6.1.1.27575",
    "uniqueid": "00:11:22:33:44:55:66:88-02-0400",
    "capabilities": {"certified": True},
}
TEMPERATURE_SENSOR_2 = {
    "state": {"temperature": 1875, "lastupdated": "2019-01-01T01:00:00"},
    "swupdate": {"state": "noupdates", "lastinstall": "2019-01-01T01:00:00"},
    "config": {
        "on": True,
        "battery": 100,
        "reachable": True,
        "alert": "none",
        "ledindication": False,
        "usertest": False,
        "pending": [],
    },
    "name": "Hue temperature sensor 2",
    "type": "ZLLTemperature",
    "modelid": "SML001",
    "manufacturername": "Philips",
    "productname": "Hue temperature sensor",
    "swversion": "6.1.1.27575",
    "uniqueid": "00:11:22:33:44:55:66:88-02-0402",
    "capabilities": {"certified": True},
}
PRESENCE_SENSOR_3_PRESENT = {
    "state": {"presence": True, "lastupdated": "2019-01-01T01:00:00"},
    "swupdate": {"state": "noupdates", "lastinstall": "2019-01-01T00:00:00"},
    "config": {
        "on": True,
        "battery": 100,
        "reachable": True,
        "alert": "none",
        "ledindication": False,
        "usertest": False,
        "sensitivity": 2,
        "sensitivitymax": 2,
        "pending": [],
    },
    "name": "Bedroom sensor",
    "type": "ZLLPresence",
    "modelid": "SML001",
    "manufacturername": "Philips",
    "productname": "Hue motion sensor",
    "swversion": "6.1.1.27575",
    "uniqueid": "00:11:22:33:44:55:66:99-02-0406",
    "capabilities": {"certified": True},
}
LIGHT_LEVEL_SENSOR_3 = {
    "state": {
        "lightlevel": 1,
        "dark": True,
        "daylight": True,
        "lastupdated": "2019-01-01T01:00:00",
    },
    "swupdate": {"state": "noupdates", "lastinstall": "2019-01-01T00:00:00"},
    "config": {
        "on": True,
        "battery": 100,
        "reachable": True,
        "alert": "none",
        "tholddark": 12467,
        "tholdoffset": 7000,
        "ledindication": False,
        "usertest": False,
        "pending": [],
    },
    "name": "Hue ambient light sensor 3",
    "type": "ZLLLightLevel",
    "modelid": "SML001",
    "manufacturername": "Philips",
    "productname": "Hue ambient light sensor",
    "swversion": "6.1.1.27575",
    "uniqueid": "00:11:22:33:44:55:66:99-02-0400",
    "capabilities": {"certified": True},
}
TEMPERATURE_SENSOR_3 = {
    "state": {"temperature": 1775, "lastupdated": "2019-01-01T01:00:00"},
    "swupdate": {"state": "noupdates", "lastinstall": "2019-01-01T01:00:00"},
    "config": {
        "on": True,
        "battery": 100,
        "reachable": True,
        "alert": "none",
        "ledindication": False,
        "usertest": False,
        "pending": [],
    },
    "name": "Hue temperature sensor 3",
    "type": "ZLLTemperature",
    "modelid": "SML001",
    "manufacturername": "Philips",
    "productname": "Hue temperature sensor",
    "swversion": "6.1.1.27575",
    "uniqueid": "00:11:22:33:44:55:66:99-02-0402",
    "capabilities": {"certified": True},
}
UNSUPPORTED_SENSOR = {
    "state": {"status": 0, "lastupdated": "2019-01-01T01:00:00"},
    "config": {"on": True, "reachable": True},
    "name": "Unsupported sensor",
    "type": "CLIPGenericStatus",
    "modelid": "PHWA01",
    "manufacturername": "Philips",
    "swversion": "1.0",
    "uniqueid": "arbitrary",
    "recycle": True,
}
HUE_TAP_REMOTE_1 = {
    "state": {"buttonevent": 17, "lastupdated": "2019-06-22T14:43:50"},
    "swupdate": {"state": "notupdatable", "lastinstall": None},
    "config": {"on": True},
    "name": "Hue Tap",
    "type": "ZGPSwitch",
    "modelid": "ZGPSWITCH",
    "manufacturername": "Philips",
    "productname": "Hue tap switch",
    "diversityid": "d8cde5d5-0eef-4b95-b0f0-71ddd2952af4",
    "uniqueid": "00:00:00:00:00:44:23:08-f2",
    "capabilities": {"certified": True, "primary": True, "inputs": []},
}
HUE_DIMMER_REMOTE_1 = {
    "state": {"buttonevent": 4002, "lastupdated": "2019-12-28T21:58:02"},
    "swupdate": {"state": "noupdates", "lastinstall": "2019-10-13T13:16:15"},
    "config": {"on": True, "battery": 100, "reachable": True, "pending": []},
    "name": "Hue dimmer switch 1",
    "type": "ZLLSwitch",
    "modelid": "RWL021",
    "manufacturername": "Philips",
    "productname": "Hue dimmer switch",
    "diversityid": "73bbabea-3420-499a-9856-46bf437e119b",
    "swversion": "6.1.1.28573",
    "uniqueid": "00:17:88:01:10:3e:3a:dc-02-fc00",
    "capabilities": {"certified": True, "primary": True, "inputs": []},
}
SENSOR_RESPONSE = {
    "1": PRESENCE_SENSOR_1_PRESENT,
    "2": LIGHT_LEVEL_SENSOR_1,
    "3": TEMPERATURE_SENSOR_1,
    "4": PRESENCE_SENSOR_2_NOT_PRESENT,
    "5": LIGHT_LEVEL_SENSOR_2,
    "6": TEMPERATURE_SENSOR_2,
    "7": HUE_TAP_REMOTE_1,
    "8": HUE_DIMMER_REMOTE_1,
}


async def test_no_sensors.opp, mock_bridge):
    """Test the update_items function when no sensors are found."""
    mock_bridge.allow_groups = True
    mock_bridge.mock_sensor_responses.append({})
    await setup_bridge.opp, mock_bridge)
    assert len(mock_bridge.mock_requests) == 1
    assert len.opp.states.async_all()) == 0


async def test_sensors_with_multiple_bridges.opp, mock_bridge):
    """Test the update_items function with some sensors."""
    mock_bridge_2 = create_mock_bridge.opp)
    mock_bridge_2.mock_sensor_responses.append(
        {
            "1": PRESENCE_SENSOR_3_PRESENT,
            "2": LIGHT_LEVEL_SENSOR_3,
            "3": TEMPERATURE_SENSOR_3,
        }
    )
    mock_bridge.mock_sensor_responses.append(SENSOR_RESPONSE)
    await setup_bridge.opp, mock_bridge)
    await setup_bridge.opp, mock_bridge_2, hostname="mock-bridge-2")

    assert len(mock_bridge.mock_requests) == 1
    assert len(mock_bridge_2.mock_requests) == 1
    # 3 "physical" sensors with 3 virtual sensors each + 1 battery sensor
    assert len.opp.states.async_all()) == 10


async def test_sensors.opp, mock_bridge):
    """Test the update_items function with some sensors."""
    mock_bridge.mock_sensor_responses.append(SENSOR_RESPONSE)
    await setup_bridge.opp, mock_bridge)
    assert len(mock_bridge.mock_requests) == 1
    # 2 "physical" sensors with 3 virtual sensors each
    assert len.opp.states.async_all()) == 7

    presence_sensor_1 = opp.states.get("binary_sensor.living_room_sensor_motion")
    light_level_sensor_1 = opp.states.get("sensor.living_room_sensor_light_level")
    temperature_sensor_1 = opp.states.get("sensor.living_room_sensor_temperature")
    assert presence_sensor_1 is not None
    assert presence_sensor_1.state == "on"
    assert light_level_sensor_1 is not None
    assert light_level_sensor_1.state == "1.0"
    assert light_level_sensor_1.name == "Living room sensor light level"
    assert temperature_sensor_1 is not None
    assert temperature_sensor_1.state == "17.75"
    assert temperature_sensor_1.name == "Living room sensor temperature"

    presence_sensor_2 = opp.states.get("binary_sensor.kitchen_sensor_motion")
    light_level_sensor_2 = opp.states.get("sensor.kitchen_sensor_light_level")
    temperature_sensor_2 = opp.states.get("sensor.kitchen_sensor_temperature")
    assert presence_sensor_2 is not None
    assert presence_sensor_2.state == "off"
    assert light_level_sensor_2 is not None
    assert light_level_sensor_2.state == "10.0"
    assert light_level_sensor_2.name == "Kitchen sensor light level"
    assert temperature_sensor_2 is not None
    assert temperature_sensor_2.state == "18.75"
    assert temperature_sensor_2.name == "Kitchen sensor temperature"

    battery_remote_1 = opp.states.get("sensor.hue_dimmer_switch_1_battery_level")
    assert battery_remote_1 is not None
    assert battery_remote_1.state == "100"
    assert battery_remote_1.name == "Hue dimmer switch 1 battery level"


async def test_unsupported_sensors.opp, mock_bridge):
    """Test that unsupported sensors don't get added and don't fail."""
    response_with_unsupported = dict(SENSOR_RESPONSE)
    response_with_unsupported["7"] = UNSUPPORTED_SENSOR
    mock_bridge.mock_sensor_responses.append(response_with_unsupported)
    await setup_bridge.opp, mock_bridge)
    assert len(mock_bridge.mock_requests) == 1
    # 2 "physical" sensors with 3 virtual sensors each + 1 battery sensor
    assert len.opp.states.async_all()) == 7


async def test_new_sensor_discovered.opp, mock_bridge):
    """Test if 2nd update has a new sensor."""
    mock_bridge.mock_sensor_responses.append(SENSOR_RESPONSE)

    await setup_bridge.opp, mock_bridge)
    assert len(mock_bridge.mock_requests) == 1
    assert len.opp.states.async_all()) == 7

    new_sensor_response = dict(SENSOR_RESPONSE)
    new_sensor_response.update(
        {
            "9": PRESENCE_SENSOR_3_PRESENT,
            "10": LIGHT_LEVEL_SENSOR_3,
            "11": TEMPERATURE_SENSOR_3,
        }
    )

    mock_bridge.mock_sensor_responses.append(new_sensor_response)

    # Force updates to run again
    await mock_bridge.sensor_manager.coordinator.async_refresh()
    await.opp.async_block_till_done()

    assert len(mock_bridge.mock_requests) == 2
    assert len.opp.states.async_all()) == 10

    presence = opp.states.get("binary_sensor.bedroom_sensor_motion")
    assert presence is not None
    assert presence.state == "on"
    temperature = opp.states.get("sensor.bedroom_sensor_temperature")
    assert temperature is not None
    assert temperature.state == "17.75"


async def test_sensor_removed.opp, mock_bridge):
    """Test if 2nd update has removed sensor."""
    mock_bridge.mock_sensor_responses.append(SENSOR_RESPONSE)

    await setup_bridge.opp, mock_bridge)
    assert len(mock_bridge.mock_requests) == 1
    assert len.opp.states.async_all()) == 7

    mock_bridge.mock_sensor_responses.clear()
    keys = ("1", "2", "3")
    mock_bridge.mock_sensor_responses.append({k: SENSOR_RESPONSE[k] for k in keys})

    # Force updates to run again
    await mock_bridge.sensor_manager.coordinator.async_refresh()

    # To flush out the service call to update the group
    await.opp.async_block_till_done()

    assert len(mock_bridge.mock_requests) == 2
    assert len.opp.states.async_all()) == 3

    sensor = opp.states.get("binary_sensor.living_room_sensor_motion")
    assert sensor is not None

    removed_sensor = opp.states.get("binary_sensor.kitchen_sensor_motion")
    assert removed_sensor is None


async def test_update_timeout.opp, mock_bridge):
    """Test bridge marked as not available if timeout error during update."""
    mock_bridge.api.sensors.update = Mock(side_effect=asyncio.TimeoutError)
    await setup_bridge.opp, mock_bridge)
    assert len(mock_bridge.mock_requests) == 0
    assert len.opp.states.async_all()) == 0


async def test_update_unauthorized.opp, mock_bridge):
    """Test bridge marked as not authorized if unauthorized during update."""
    mock_bridge.api.sensors.update = Mock(side_effect=aiohue.Unauthorized)
    await setup_bridge.opp, mock_bridge)
    assert len(mock_bridge.mock_requests) == 0
    assert len.opp.states.async_all()) == 0
    assert len(mock_bridge.handle_unauthorized_error.mock_calls) == 1


async def test_hue_events.opp, mock_bridge):
    """Test that hue remotes fire events when pressed."""
    mock_bridge.mock_sensor_responses.append(SENSOR_RESPONSE)

    mock_listener = Mock()
    unsub = opp.bus.async_listen(CONF_HUE_EVENT, mock_listener)

    await setup_bridge.opp, mock_bridge)
    assert len(mock_bridge.mock_requests) == 1
    assert len.opp.states.async_all()) == 7
    assert len(mock_listener.mock_calls) == 0

    new_sensor_response = dict(SENSOR_RESPONSE)
    new_sensor_response["7"]["state"] = {
        "buttonevent": 18,
        "lastupdated": "2019-12-28T22:58:02",
    }
    mock_bridge.mock_sensor_responses.append(new_sensor_response)

    # Force updates to run again
    await mock_bridge.sensor_manager.coordinator.async_refresh()
    await.opp.async_block_till_done()

    assert len(mock_bridge.mock_requests) == 2
    assert len.opp.states.async_all()) == 7
    assert len(mock_listener.mock_calls) == 1
    assert mock_listener.mock_calls[0][1][0].data == {
        "id": "hue_tap",
        "unique_id": "00:00:00:00:00:44:23:08-f2",
        "event": 18,
        "last_updated": "2019-12-28T22:58:02",
    }

    new_sensor_response = dict(new_sensor_response)
    new_sensor_response["8"]["state"] = {
        "buttonevent": 3002,
        "lastupdated": "2019-12-28T22:58:01",
    }
    mock_bridge.mock_sensor_responses.append(new_sensor_response)

    # Force updates to run again
    await mock_bridge.sensor_manager.coordinator.async_refresh()
    await.opp.async_block_till_done()

    assert len(mock_bridge.mock_requests) == 3
    assert len.opp.states.async_all()) == 7
    assert len(mock_listener.mock_calls) == 2
    assert mock_listener.mock_calls[1][1][0].data == {
        "id": "hue_dimmer_switch_1",
        "unique_id": "00:17:88:01:10:3e:3a:dc-02-fc00",
        "event": 3002,
        "last_updated": "2019-12-28T22:58:01",
    }

    # Add a new remote. In discovery the new event is registered **but not fired**
    new_sensor_response = dict(new_sensor_response)
    new_sensor_response["21"] = {
        "state": {
            "rotaryevent": 2,
            "expectedrotation": 208,
            "expectedeventduration": 400,
            "lastupdated": "2020-01-31T15:56:19",
        },
        "swupdate": {"state": "noupdates", "lastinstall": "2019-11-26T03:35:21"},
        "config": {"on": True, "battery": 100, "reachable": True, "pending": []},
        "name": "Lutron Aurora 1",
        "type": "ZLLRelativeRotary",
        "modelid": "Z3-1BRL",
        "manufacturername": "Lutron",
        "productname": "Lutron Aurora",
        "diversityid": "2c3a75ff-55c4-4e4d-8c44-82d330b8eb9b",
        "swversion": "3.4",
        "uniqueid": "ff:ff:00:0f:e7:fd:bc:b7-01-fc00-0014",
        "capabilities": {
            "certified": True,
            "primary": True,
            "inputs": [
                {
                    "repeatintervals": [400],
                    "events": [
                        {"rotaryevent": 1, "eventtype": "start"},
                        {"rotaryevent": 2, "eventtype": "repeat"},
                    ],
                }
            ],
        },
    }
    mock_bridge.mock_sensor_responses.append(new_sensor_response)

    # Force updates to run again
    await mock_bridge.sensor_manager.coordinator.async_refresh()
    await.opp.async_block_till_done()

    assert len(mock_bridge.mock_requests) == 4
    assert len.opp.states.async_all()) == 8
    assert len(mock_listener.mock_calls) == 2

    # A new press fires the event
    new_sensor_response["21"]["state"]["lastupdated"] = "2020-01-31T15:57:19"
    mock_bridge.mock_sensor_responses.append(new_sensor_response)

    # Force updates to run again
    await mock_bridge.sensor_manager.coordinator.async_refresh()
    await.opp.async_block_till_done()

    assert len(mock_bridge.mock_requests) == 5
    assert len.opp.states.async_all()) == 8
    assert len(mock_listener.mock_calls) == 3
    assert mock_listener.mock_calls[2][1][0].data == {
        "id": "lutron_aurora_1",
        "unique_id": "ff:ff:00:0f:e7:fd:bc:b7-01-fc00-0014",
        "event": 2,
        "last_updated": "2020-01-31T15:57:19",
    }

    unsub()
