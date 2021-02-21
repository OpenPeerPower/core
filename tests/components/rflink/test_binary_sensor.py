"""
Test for RFlink sensor components.

Test setup of rflink sensor component/platform. Verify manual and
automatic sensor creation.
"""
from datetime import timedelta
from unittest.mock import patch

from openpeerpower.components.rflink import CONF_RECONNECT_INTERVAL
from openpeerpower.const import (
    EVENT_STATE_CHANGED,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
import openpeerpowerr.core as ha
import openpeerpowerr.util.dt as dt_util

from tests.common import async_fire_time_changed
from tests.components.rflink.test_init import mock_rflink

DOMAIN = "binary_sensor"

CONFIG = {
    "rflink": {
        "port": "/dev/ttyABC0",
        "ignore_devices": ["ignore_wildcard_*", "ignore_sensor"],
    },
    DOMAIN: {
        "platform": "rflink",
        "devices": {
            "test": {"name": "test", "device_class": "door"},
            "test2": {
                "name": "test2",
                "device_class": "motion",
                "off_delay": 30,
                "force_update": True,
            },
        },
    },
}


async def test_default_setup.opp, monkeypatch):
    """Test all basic functionality of the rflink sensor component."""
    # setup mocking rflink module
    event_callback, create, _, _ = await mock_rflink.opp, CONFIG, DOMAIN, monkeypatch)

    # make sure arguments are passed
    assert create.call_args_list[0][1]["ignore"]

    # test default state of sensor loaded from config
    config_sensor = opp.states.get("binary_sensor.test")
    assert config_sensor
    assert config_sensor.state == STATE_OFF
    assert config_sensor.attributes["device_class"] == "door"

    # test on event for config sensor
    event_callback({"id": "test", "command": "on"})
    await.opp.async_block_till_done()

    assert.opp.states.get("binary_sensor.test").state == STATE_ON

    # test off event for config sensor
    event_callback({"id": "test", "command": "off"})
    await.opp.async_block_till_done()

    assert.opp.states.get("binary_sensor.test").state == STATE_OFF

    # test allon event for config sensor
    event_callback({"id": "test", "command": "allon"})
    await.opp.async_block_till_done()

    assert.opp.states.get("binary_sensor.test").state == STATE_ON

    # test alloff event for config sensor
    event_callback({"id": "test", "command": "alloff"})
    await.opp.async_block_till_done()

    assert.opp.states.get("binary_sensor.test").state == STATE_OFF


async def test_entity_availability.opp, monkeypatch):
    """If Rflink device is disconnected, entities should become unavailable."""
    # Make sure Rflink mock does not 'recover' to quickly from the
    # disconnect or else the unavailability cannot be measured
    config = CONFIG
    failures = [True, True]
    config[CONF_RECONNECT_INTERVAL] = 60

    # Create platform and entities
    _, _, _, disconnect_callback = await mock_rflink(
       .opp, config, DOMAIN, monkeypatch, failures=failures
    )

    # Entities are available by default
    assert.opp.states.get("binary_sensor.test").state == STATE_OFF

    # Mock a disconnect of the Rflink device
    disconnect_callback()

    # Wait for dispatch events to propagate
    await.opp.async_block_till_done()

    # Entity should be unavailable
    assert.opp.states.get("binary_sensor.test").state == STATE_UNAVAILABLE

    # Reconnect the Rflink device
    disconnect_callback()

    # Wait for dispatch events to propagate
    await.opp.async_block_till_done()

    # Entities should be available again
    assert.opp.states.get("binary_sensor.test").state == STATE_OFF


async def test_off_delay.opp, legacy_patchable_time, monkeypatch):
    """Test off_delay option."""
    # setup mocking rflink module
    event_callback, create, _, _ = await mock_rflink.opp, CONFIG, DOMAIN, monkeypatch)

    # make sure arguments are passed
    assert create.call_args_list[0][1]["ignore"]

    events = []

    on_event = {"id": "test2", "command": "on"}

    @op.callback
    def callback(event):
        """Verify event got called."""
        events.append(event)

   .opp.bus.async_listen(EVENT_STATE_CHANGED, callback)

    now = dt_util.utcnow()
    # fake time and turn on sensor
    future = now + timedelta(seconds=0)
    with patch(("openpeerpowerr.helpers.event.dt_util.utcnow"), return_value=future):
        async_fire_time_changed.opp, future)
        event_callback(on_event)
        await.opp.async_block_till_done()
        await.opp.async_block_till_done()
    state = opp.states.get("binary_sensor.test2")
    assert state.state == STATE_ON
    assert len(events) == 1

    # fake time and turn on sensor again
    future = now + timedelta(seconds=15)
    with patch(("openpeerpowerr.helpers.event.dt_util.utcnow"), return_value=future):
        async_fire_time_changed.opp, future)
        event_callback(on_event)
        await.opp.async_block_till_done()
        await.opp.async_block_till_done()
    state = opp.states.get("binary_sensor.test2")
    assert state.state == STATE_ON
    assert len(events) == 2

    # fake time and verify sensor still on (de-bounce)
    future = now + timedelta(seconds=35)
    with patch(("openpeerpowerr.helpers.event.dt_util.utcnow"), return_value=future):
        async_fire_time_changed.opp, future)
        await.opp.async_block_till_done()
        await.opp.async_block_till_done()
    state = opp.states.get("binary_sensor.test2")
    assert state.state == STATE_ON
    assert len(events) == 2

    # fake time and verify sensor is off
    future = now + timedelta(seconds=45)
    with patch(("openpeerpowerr.helpers.event.dt_util.utcnow"), return_value=future):
        async_fire_time_changed.opp, future)
        await.opp.async_block_till_done()
        await.opp.async_block_till_done()
    state = opp.states.get("binary_sensor.test2")
    assert state.state == STATE_OFF
    assert len(events) == 3
