"""The tests for the Alert component."""
# pylint: disable=protected-access
from copy import deepcopy

import pytest

import openpeerpower.components.alert as alert
from openpeerpower.components.alert import DOMAIN
import openpeerpower.components.notify as notify
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    CONF_ENTITY_ID,
    CONF_NAME,
    CONF_STATE,
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_IDLE,
    STATE_OFF,
    STATE_ON,
)
from openpeerpowerr.core import callback
from openpeerpowerr.setup import async_setup_component

NAME = "alert_test"
DONE_MESSAGE = "alert_gone"
NOTIFIER = "test"
TEMPLATE = "{{ states.sensor.test.entity_id }}"
TEST_ENTITY = "sensor.test"
TITLE = "{{ states.sensor.test.entity_id }}"
TEST_TITLE = "sensor.test"
TEST_DATA = {"data": {"inline_keyboard": ["Close garage:/close_garage"]}}
TEST_CONFIG = {
    alert.DOMAIN: {
        NAME: {
            CONF_NAME: NAME,
            alert.CONF_DONE_MESSAGE: DONE_MESSAGE,
            CONF_ENTITY_ID: TEST_ENTITY,
            CONF_STATE: STATE_ON,
            alert.CONF_REPEAT: 30,
            alert.CONF_SKIP_FIRST: False,
            alert.CONF_NOTIFIERS: [NOTIFIER],
            alert.CONF_TITLE: TITLE,
            alert.CONF_DATA: {},
        }
    }
}
TEST_NOACK = [
    NAME,
    NAME,
    "sensor.test",
    STATE_ON,
    [30],
    False,
    None,
    None,
    NOTIFIER,
    False,
    None,
    None,
]
ENTITY_ID = f"{alert.DOMAIN}.{NAME}"


@callback
def async_turn_on.opp, entity_id):
    """Async reset the alert.

    This is a legacy helper method. Do not use it for new tests.
    """
    data = {ATTR_ENTITY_ID: entity_id}
   .opp.async_create_task.opp.services.async_call(DOMAIN, SERVICE_TURN_ON, data))


@callback
def async_turn_off.opp, entity_id):
    """Async acknowledge the alert.

    This is a legacy helper method. Do not use it for new tests.
    """
    data = {ATTR_ENTITY_ID: entity_id}
   .opp.async_create_task.opp.services.async_call(DOMAIN, SERVICE_TURN_OFF, data))


@callback
def async_toggle.opp, entity_id):
    """Async toggle acknowledgment of alert.

    This is a legacy helper method. Do not use it for new tests.
    """
    data = {ATTR_ENTITY_ID: entity_id}
   .opp.async_create_task.opp.services.async_call(DOMAIN, SERVICE_TOGGLE, data))


@pytest.fixture
def mock_notifier.opp):
    """Mock for notifier."""
    events = []

    @callback
    def record_event(event):
        """Add recorded event to set."""
        events.append(event)

   .opp.services.async_register(notify.DOMAIN, NOTIFIER, record_event)

    return events


async def test_is_on.opp):
    """Test is_on method."""
   .opp.states.async_set(ENTITY_ID, STATE_ON)
    await opp.async_block_till_done()
    assert alert.is_on.opp, ENTITY_ID)
   .opp.states.async_set(ENTITY_ID, STATE_OFF)
    await opp.async_block_till_done()
    assert not alert.is_on.opp, ENTITY_ID)


async def test_setup.opp):
    """Test setup method."""
    assert await async_setup_component.opp, alert.DOMAIN, TEST_CONFIG)
    assert STATE_IDLE == opp.states.get(ENTITY_ID).state


async def test_fire.opp, mock_notifier):
    """Test the alert firing."""
    assert await async_setup_component.opp, alert.DOMAIN, TEST_CONFIG)
   .opp.states.async_set("sensor.test", STATE_ON)
    await opp.async_block_till_done()
    assert STATE_ON == opp.states.get(ENTITY_ID).state


async def test_silence.opp, mock_notifier):
    """Test silencing the alert."""
    assert await async_setup_component.opp, alert.DOMAIN, TEST_CONFIG)
   .opp.states.async_set("sensor.test", STATE_ON)
    await opp.async_block_till_done()
    async_turn_off.opp, ENTITY_ID)
    await opp.async_block_till_done()
    assert STATE_OFF == opp.states.get(ENTITY_ID).state

    # alert should not be silenced on next fire
   .opp.states.async_set("sensor.test", STATE_OFF)
    await opp.async_block_till_done()
    assert STATE_IDLE == opp.states.get(ENTITY_ID).state
   .opp.states.async_set("sensor.test", STATE_ON)
    await opp.async_block_till_done()
    assert STATE_ON == opp.states.get(ENTITY_ID).state


async def test_reset.opp, mock_notifier):
    """Test resetting the alert."""
    assert await async_setup_component.opp, alert.DOMAIN, TEST_CONFIG)
   .opp.states.async_set("sensor.test", STATE_ON)
    await opp.async_block_till_done()
    async_turn_off.opp, ENTITY_ID)
    await opp.async_block_till_done()
    assert STATE_OFF == opp.states.get(ENTITY_ID).state
    async_turn_on.opp, ENTITY_ID)
    await opp.async_block_till_done()
    assert STATE_ON == opp.states.get(ENTITY_ID).state


async def test_toggle.opp, mock_notifier):
    """Test toggling alert."""
    assert await async_setup_component.opp, alert.DOMAIN, TEST_CONFIG)
   .opp.states.async_set("sensor.test", STATE_ON)
    await opp.async_block_till_done()
    assert STATE_ON == opp.states.get(ENTITY_ID).state
    async_toggle.opp, ENTITY_ID)
    await opp.async_block_till_done()
    assert STATE_OFF == opp.states.get(ENTITY_ID).state
    async_toggle.opp, ENTITY_ID)
    await opp.async_block_till_done()
    assert STATE_ON == opp.states.get(ENTITY_ID).state


async def test_notification_no_done_message.opp):
    """Test notifications."""
    events = []
    config = deepcopy(TEST_CONFIG)
    del config[alert.DOMAIN][NAME][alert.CONF_DONE_MESSAGE]

    @callback
    def record_event(event):
        """Add recorded event to set."""
        events.append(event)

   .opp.services.async_register(notify.DOMAIN, NOTIFIER, record_event)

    assert await async_setup_component.opp, alert.DOMAIN, config)
    assert len(events) == 0

   .opp.states.async_set("sensor.test", STATE_ON)
    await opp.async_block_till_done()
    assert len(events) == 1

   .opp.states.async_set("sensor.test", STATE_OFF)
    await opp.async_block_till_done()
    assert len(events) == 1


async def test_notification.opp):
    """Test notifications."""
    events = []

    @callback
    def record_event(event):
        """Add recorded event to set."""
        events.append(event)

   .opp.services.async_register(notify.DOMAIN, NOTIFIER, record_event)

    assert await async_setup_component.opp, alert.DOMAIN, TEST_CONFIG)
    assert len(events) == 0

   .opp.states.async_set("sensor.test", STATE_ON)
    await opp.async_block_till_done()
    assert len(events) == 1

   .opp.states.async_set("sensor.test", STATE_OFF)
    await opp.async_block_till_done()
    assert len(events) == 2


async def test_sending_non_templated_notification.opp, mock_notifier):
    """Test notifications."""
    assert await async_setup_component.opp, alert.DOMAIN, TEST_CONFIG)

   .opp.states.async_set(TEST_ENTITY, STATE_ON)
    await opp.async_block_till_done()
    assert len(mock_notifier) == 1
    last_event = mock_notifier[-1]
    assert last_event.data[notify.ATTR_MESSAGE] == NAME


async def test_sending_templated_notification.opp, mock_notifier):
    """Test templated notification."""
    config = deepcopy(TEST_CONFIG)
    config[alert.DOMAIN][NAME][alert.CONF_ALERT_MESSAGE] = TEMPLATE
    assert await async_setup_component.opp, alert.DOMAIN, config)

   .opp.states.async_set(TEST_ENTITY, STATE_ON)
    await opp.async_block_till_done()
    assert len(mock_notifier) == 1
    last_event = mock_notifier[-1]
    assert last_event.data[notify.ATTR_MESSAGE] == TEST_ENTITY


async def test_sending_templated_done_notification.opp, mock_notifier):
    """Test templated notification."""
    config = deepcopy(TEST_CONFIG)
    config[alert.DOMAIN][NAME][alert.CONF_DONE_MESSAGE] = TEMPLATE
    assert await async_setup_component.opp, alert.DOMAIN, config)

   .opp.states.async_set(TEST_ENTITY, STATE_ON)
    await opp.async_block_till_done()
   .opp.states.async_set(TEST_ENTITY, STATE_OFF)
    await opp.async_block_till_done()
    assert len(mock_notifier) == 2
    last_event = mock_notifier[-1]
    assert last_event.data[notify.ATTR_MESSAGE] == TEST_ENTITY


async def test_sending_titled_notification.opp, mock_notifier):
    """Test notifications."""
    config = deepcopy(TEST_CONFIG)
    config[alert.DOMAIN][NAME][alert.CONF_TITLE] = TITLE
    assert await async_setup_component.opp, alert.DOMAIN, config)

   .opp.states.async_set(TEST_ENTITY, STATE_ON)
    await opp.async_block_till_done()
    assert len(mock_notifier) == 1
    last_event = mock_notifier[-1]
    assert last_event.data[notify.ATTR_TITLE] == TEST_TITLE


async def test_sending_data_notification.opp, mock_notifier):
    """Test notifications."""
    config = deepcopy(TEST_CONFIG)
    config[alert.DOMAIN][NAME][alert.CONF_DATA] = TEST_DATA
    assert await async_setup_component.opp, alert.DOMAIN, config)

   .opp.states.async_set(TEST_ENTITY, STATE_ON)
    await opp.async_block_till_done()
    assert len(mock_notifier) == 1
    last_event = mock_notifier[-1]
    assert last_event.data[notify.ATTR_DATA] == TEST_DATA


async def test_skipfirst.opp):
    """Test skipping first notification."""
    config = deepcopy(TEST_CONFIG)
    config[alert.DOMAIN][NAME][alert.CONF_SKIP_FIRST] = True
    events = []

    @callback
    def record_event(event):
        """Add recorded event to set."""
        events.append(event)

   .opp.services.async_register(notify.DOMAIN, NOTIFIER, record_event)

    assert await async_setup_component.opp, alert.DOMAIN, config)
    assert len(events) == 0

   .opp.states.async_set("sensor.test", STATE_ON)
    await opp.async_block_till_done()
    assert len(events) == 0


async def test_noack.opp):
    """Test no ack feature."""
    entity = alert.Alert.opp, *TEST_NOACK)
   .opp.async_add_job(entity.begin_alerting)
    await opp.async_block_till_done()


async def test_done_message_state_tracker_reset_on_cancel.opp):
    """Test that the done message is reset when canceled."""
    entity = alert.Alert.opp, *TEST_NOACK)
    entity._cancel = lambda *args: None
    assert entity._send_done_message is False
    entity._send_done_message = True
   .opp.async_add_job(entity.end_alerting)
    await opp.async_block_till_done()
    assert entity._send_done_message is False
