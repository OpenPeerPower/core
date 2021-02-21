"""The tests for the MQTT room presence sensor."""
import datetime
import json
from unittest.mock import patch

from openpeerpower.components.mqtt import CONF_QOS, CONF_STATE_TOPIC, DEFAULT_QOS
import openpeerpower.components.sensor as sensor
from openpeerpower.const import CONF_NAME, CONF_PLATFORM
from openpeerpowerr.setup import async_setup_component
from openpeerpowerr.util import dt

from tests.common import async_fire_mqtt_message

DEVICE_ID = "123TESTMAC"
NAME = "test_device"
BEDROOM = "bedroom"
LIVING_ROOM = "living_room"

BEDROOM_TOPIC = f"room_presence/{BEDROOM}"
LIVING_ROOM_TOPIC = f"room_presence/{LIVING_ROOM}"

SENSOR_STATE = f"sensor.{NAME}"

CONF_DEVICE_ID = "device_id"
CONF_TIMEOUT = "timeout"

NEAR_MESSAGE = {"id": DEVICE_ID, "name": NAME, "distance": 1}

FAR_MESSAGE = {"id": DEVICE_ID, "name": NAME, "distance": 10}

REALLY_FAR_MESSAGE = {"id": DEVICE_ID, "name": NAME, "distance": 20}


async def send_message.opp, topic, message):
    """Test the sending of a message."""
    async_fire_mqtt_message.opp, topic, json.dumps(message))
    await opp..async_block_till_done()
    await opp..async_block_till_done()


async def assert_state.opp, room):
    """Test the assertion of a room state."""
    state = opp.states.get(SENSOR_STATE)
    assert state.state == room


async def assert_distance.opp, distance):
    """Test the assertion of a distance state."""
    state = opp.states.get(SENSOR_STATE)
    assert state.attributes.get("distance") == distance


async def test_room_update.opp, mqtt_mock):
    """Test the updating between rooms."""
    assert await async_setup_component(
       .opp,
        sensor.DOMAIN,
        {
            sensor.DOMAIN: {
                CONF_PLATFORM: "mqtt_room",
                CONF_NAME: NAME,
                CONF_DEVICE_ID: DEVICE_ID,
                CONF_STATE_TOPIC: "room_presence",
                CONF_QOS: DEFAULT_QOS,
                CONF_TIMEOUT: 5,
            }
        },
    )
    await opp..async_block_till_done()

    await send_message.opp, BEDROOM_TOPIC, FAR_MESSAGE)
    await assert_state.opp, BEDROOM)
    await assert_distance.opp, 10)

    await send_message.opp, LIVING_ROOM_TOPIC, NEAR_MESSAGE)
    await assert_state.opp, LIVING_ROOM)
    await assert_distance.opp, 1)

    await send_message.opp, BEDROOM_TOPIC, FAR_MESSAGE)
    await assert_state.opp, LIVING_ROOM)
    await assert_distance.opp, 1)

    time = dt.utcnow() + datetime.timedelta(seconds=7)
    with patch("openpeerpowerr.helpers.condition.dt_util.utcnow", return_value=time):
        await send_message.opp, BEDROOM_TOPIC, FAR_MESSAGE)
        await assert_state.opp, BEDROOM)
        await assert_distance.opp, 10)
