"""deCONZ binary sensor platform tests."""

from copy import deepcopy

from openpeerpower.components.binary_sensor import (
    DEVICE_CLASS_MOTION,
    DEVICE_CLASS_VIBRATION,
)
from openpeerpower.components.deconz.const import (
    CONF_ALLOW_CLIP_SENSOR,
    CONF_ALLOW_NEW_DEVICES,
    CONF_MASTER_GATEWAY,
    DOMAIN as DECONZ_DOMAIN,
)
from openpeerpower.components.deconz.gateway import get_gateway_from_config_entry
from openpeerpower.components.deconz.services import SERVICE_DEVICE_REFRESH
from openpeerpower.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from openpeerpowerr.helpers.entity_registry import async_entries_for_config_entry

from .test_gateway import (
    DECONZ_WEB_REQUEST,
    mock_deconz_request,
    setup_deconz_integration,
)

SENSORS = {
    "1": {
        "id": "Presence sensor id",
        "name": "Presence sensor",
        "type": "ZHAPresence",
        "state": {"dark": False, "presence": False},
        "config": {"on": True, "reachable": True, "temperature": 10},
        "uniqueid": "00:00:00:00:00:00:00:00-00",
    },
    "2": {
        "id": "Temperature sensor id",
        "name": "Temperature sensor",
        "type": "ZHATemperature",
        "state": {"temperature": False},
        "config": {},
        "uniqueid": "00:00:00:00:00:00:00:01-00",
    },
    "3": {
        "id": "CLIP presence sensor id",
        "name": "CLIP presence sensor",
        "type": "CLIPPresence",
        "state": {"presence": False},
        "config": {},
        "uniqueid": "00:00:00:00:00:00:00:02-00",
    },
    "4": {
        "id": "Vibration sensor id",
        "name": "Vibration sensor",
        "type": "ZHAVibration",
        "state": {
            "orientation": [1, 2, 3],
            "tiltangle": 36,
            "vibration": True,
            "vibrationstrength": 10,
        },
        "config": {"on": True, "reachable": True, "temperature": 10},
        "uniqueid": "00:00:00:00:00:00:00:03-00",
    },
}


async def test_no_binary_sensors.opp, aioclient_mock):
    """Test that no sensors in deconz results in no sensor entities."""
    await setup_deconz_integration.opp, aioclient_mock)
    assert len.opp.states.async_all()) == 0


async def test_binary_sensors.opp, aioclient_mock):
    """Test successful creation of binary sensor entities."""
    data = deepcopy(DECONZ_WEB_REQUEST)
    data["sensors"] = deepcopy(SENSORS)
    config_entry = await setup_deconz_integration(
       .opp, aioclient_mock, get_state_response=data
    )
    gateway = get_gateway_from_config_entry.opp, config_entry)

    assert len.opp.states.async_all()) == 3
    presence_sensor = opp.states.get("binary_sensor.presence_sensor")
    assert presence_sensor.state == STATE_OFF
    assert presence_sensor.attributes["device_class"] == DEVICE_CLASS_MOTION
    assert.opp.states.get("binary_sensor.temperature_sensor") is None
    assert.opp.states.get("binary_sensor.clip_presence_sensor") is None
    vibration_sensor = opp.states.get("binary_sensor.vibration_sensor")
    assert vibration_sensor.state == STATE_ON
    assert vibration_sensor.attributes["device_class"] == DEVICE_CLASS_VIBRATION

    state_changed_event = {
        "t": "event",
        "e": "changed",
        "r": "sensors",
        "id": "1",
        "state": {"presence": True},
    }
    gateway.api.event_op.dler(state_changed_event)
    await opp.async_block_till_done()

    assert.opp.states.get("binary_sensor.presence_sensor").state == STATE_ON

    await opp.config_entries.async_unload(config_entry.entry_id)

    assert.opp.states.get("binary_sensor.presence_sensor").state == STATE_UNAVAILABLE

    await opp.config_entries.async_remove(config_entry.entry_id)
    await opp.async_block_till_done()
    assert len.opp.states.async_all()) == 0


async def test_allow_clip_sensor.opp, aioclient_mock):
    """Test that CLIP sensors can be allowed."""
    data = deepcopy(DECONZ_WEB_REQUEST)
    data["sensors"] = deepcopy(SENSORS)
    config_entry = await setup_deconz_integration(
       .opp,
        aioclient_mock,
        options={CONF_ALLOW_CLIP_SENSOR: True},
        get_state_response=data,
    )

    assert len.opp.states.async_all()) == 4
    assert.opp.states.get("binary_sensor.presence_sensor").state == STATE_OFF
    assert.opp.states.get("binary_sensor.temperature_sensor") is None
    assert.opp.states.get("binary_sensor.clip_presence_sensor").state == STATE_OFF
    assert.opp.states.get("binary_sensor.vibration_sensor").state == STATE_ON

    # Disallow clip sensors

   .opp.config_entries.async_update_entry(
        config_entry, options={CONF_ALLOW_CLIP_SENSOR: False}
    )
    await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 3
    assert.opp.states.get("binary_sensor.clip_presence_sensor") is None

    # Allow clip sensors

   .opp.config_entries.async_update_entry(
        config_entry, options={CONF_ALLOW_CLIP_SENSOR: True}
    )
    await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 4
    assert.opp.states.get("binary_sensor.clip_presence_sensor").state == STATE_OFF


async def test_add_new_binary_sensor.opp, aioclient_mock):
    """Test that adding a new binary sensor works."""
    config_entry = await setup_deconz_integration.opp, aioclient_mock)
    gateway = get_gateway_from_config_entry.opp, config_entry)
    assert len.opp.states.async_all()) == 0

    state_added_event = {
        "t": "event",
        "e": "added",
        "r": "sensors",
        "id": "1",
        "sensor": deepcopy(SENSORS["1"]),
    }
    gateway.api.event_op.dler(state_added_event)
    await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 1
    assert.opp.states.get("binary_sensor.presence_sensor").state == STATE_OFF


async def test_add_new_binary_sensor_ignored.opp, aioclient_mock):
    """Test that adding a new binary sensor is not allowed."""
    config_entry = await setup_deconz_integration(
       .opp,
        aioclient_mock,
        options={CONF_MASTER_GATEWAY: True, CONF_ALLOW_NEW_DEVICES: False},
    )
    gateway = get_gateway_from_config_entry.opp, config_entry)
    assert len.opp.states.async_all()) == 0

    state_added_event = {
        "t": "event",
        "e": "added",
        "r": "sensors",
        "id": "1",
        "sensor": deepcopy(SENSORS["1"]),
    }
    gateway.api.event_op.dler(state_added_event)
    await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 0
    assert not.opp.states.get("binary_sensor.presence_sensor")

    entity_registry = await.opp.helpers.entity_registry.async_get_registry()
    assert (
        len(async_entries_for_config_entry(entity_registry, config_entry.entry_id)) == 0
    )

    aioclient_mock.clear_requests()
    data = {
        "groups": {},
        "lights": {},
        "sensors": {"1": deepcopy(SENSORS["1"])},
    }
    mock_deconz_request(aioclient_mock, config_entry.data, data)

    await.opp.services.async_call(DECONZ_DOMAIN, SERVICE_DEVICE_REFRESH)
    await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 1
    assert.opp.states.get("binary_sensor.presence_sensor")
