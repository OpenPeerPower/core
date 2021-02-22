"""The tests for the automation component."""
import asyncio
import logging
from unittest.mock import Mock, patch

import pytest

from openpeerpower.components import logbook
import openpeerpower.components.automation as automation
from openpeerpower.components.automation import (
    ATTR_SOURCE,
    DOMAIN,
    EVENT_AUTOMATION_RELOADED,
    EVENT_AUTOMATION_TRIGGERED,
    SERVICE_TRIGGER,
)
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_NAME,
    EVENT_OPENPEERPOWER_STARTED,
    SERVICE_RELOAD,
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from openpeerpower.core import Context, CoreState, State, callback
from openpeerpower.exceptions import OpenPeerPowerError, Unauthorized
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util

from tests.common import assert_setup_component, async_mock_service, mock_restore_cache
from tests.components.logbook.test_init import MockLazyEventPartialState


@pytest.fixture
def calls.opp):
    """Track calls to a mock service."""
    return async_mock_service.opp, "test", "automation")


async def test_service_data_not_a_dict.opp, calls):
    """Test service data not dict."""
    with assert_setup_component(0, automation.DOMAIN):
        assert await async_setup_component(
            opp.
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "action": {"service": "test.automation", "data": 100},
                }
            },
        )


async def test_service_specify_data.opp, calls):
    """Test service data."""
    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "alias": "hello",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {
                    "service": "test.automation",
                    "data_template": {
                        "some": "{{ trigger.platform }} - "
                        "{{ trigger.event.event_type }}"
                    },
                },
            }
        },
    )

    time = dt_util.utcnow()

    with patch("openpeerpower.helpers.script.utcnow", return_value=time):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].data["some"] == "event - test_event"
    state = opp.states.get("automation.hello")
    assert state is not None
    assert state.attributes.get("last_triggered") == time


async def test_service_specify_entity_id.opp, calls):
    """Test service data."""
    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {"service": "test.automation", "entity_id": "hello.world"},
            }
        },
    )

    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert ["hello.world"] == calls[0].data.get(ATTR_ENTITY_ID)


async def test_service_specify_entity_id_list.opp, calls):
    """Test service data."""
    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {
                    "service": "test.automation",
                    "entity_id": ["hello.world", "hello.world2"],
                },
            }
        },
    )

    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert ["hello.world", "hello.world2"] == calls[0].data.get(ATTR_ENTITY_ID)


async def test_two_triggers.opp, calls):
    """Test triggers."""
    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": [
                    {"platform": "event", "event_type": "test_event"},
                    {"platform": "state", "entity_id": "test.entity"},
                ],
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 1
    opp.states.async_set("test.entity", "hello")
    await opp.async_block_till_done()
    assert len(calls) == 2


async def test_trigger_service_ignoring_condition.opp, caplog, calls):
    """Test triggers."""
    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "alias": "test",
                "trigger": [{"platform": "event", "event_type": "test_event"}],
                "condition": {
                    "condition": "numeric_state",
                    "entity_id": "non.existing",
                    "above": "1",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    caplog.clear()
    caplog.set_level(logging.WARNING)

    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 0

    assert len(caplog.record_tuples) == 1
    assert caplog.record_tuples[0][1] == logging.WARNING

    await opp.services.async_call(
        "automation", "trigger", {"entity_id": "automation.test"}, blocking=True
    )
    assert len(calls) == 1

    await opp.services.async_call(
        "automation",
        "trigger",
        {"entity_id": "automation.test", "skip_condition": True},
        blocking=True,
    )
    assert len(calls) == 2

    await opp.services.async_call(
        "automation",
        "trigger",
        {"entity_id": "automation.test", "skip_condition": False},
        blocking=True,
    )
    assert len(calls) == 2


async def test_two_conditions_with_and.opp, calls):
    """Test two and conditions."""
    entity_id = "test.entity"
    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": [{"platform": "event", "event_type": "test_event"}],
                "condition": [
                    {"condition": "state", "entity_id": entity_id, "state": "100"},
                    {
                        "condition": "numeric_state",
                        "entity_id": entity_id,
                        "below": 150,
                    },
                ],
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.states.async_set(entity_id, 100)
    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 1

    opp.states.async_set(entity_id, 101)
    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 1

    opp.states.async_set(entity_id, 151)
    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_shorthand_conditions_template.opp, calls):
    """Test shorthand nation form in conditions."""
    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": [{"platform": "event", "event_type": "test_event"}],
                "condition": "{{ is_state('test.entity', 'hello') }}",
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.states.async_set("test.entity", "hello")
    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 1

    opp.states.async_set("test.entity", "goodbye")
    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_automation_list_setting.opp, calls):
    """Event is not a valid condition."""
    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "action": {"service": "test.automation"},
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event_2"},
                    "action": {"service": "test.automation"},
                },
            ]
        },
    )

    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 1

    opp.bus.async_fire("test_event_2")
    await opp.async_block_till_done()
    assert len(calls) == 2


async def test_automation_calling_two_actions.opp, calls):
    """Test if we can call two actions from automation async definition."""
    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": [
                    {"service": "test.automation", "data": {"position": 0}},
                    {"service": "test.automation", "data": {"position": 1}},
                ],
            }
        },
    )

    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()

    assert len(calls) == 2
    assert calls[0].data["position"] == 0
    assert calls[1].data["position"] == 1


async def test_shared_context.opp, calls):
    """Test that the shared context is passed down the chain."""
    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "alias": "hello",
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "action": {"event": "test_event2"},
                },
                {
                    "alias": "bye",
                    "trigger": {"platform": "event", "event_type": "test_event2"},
                    "action": {"service": "test.automation"},
                },
            ]
        },
    )

    context = Context()
    first_automation_listener = Mock()
    event_mock = Mock()

    opp.bus.async_listen("test_event2", first_automation_listener)
    opp.bus.async_listen(EVENT_AUTOMATION_TRIGGERED, event_mock)
    opp.bus.async_fire("test_event", context=context)
    await opp.async_block_till_done()

    # Ensure events was fired
    assert first_automation_listener.call_count == 1
    assert event_mock.call_count == 2

    # Verify automation triggered evenet for 'hello' automation
    args, _ = event_mock.call_args_list[0]
    first_trigger_context = args[0].context
    assert first_trigger_context.parent_id == context.id
    # Ensure event data has all attributes set
    assert args[0].data.get(ATTR_NAME) is not None
    assert args[0].data.get(ATTR_ENTITY_ID) is not None
    assert args[0].data.get(ATTR_SOURCE) is not None

    # Ensure context set correctly for event fired by 'hello' automation
    args, _ = first_automation_listener.call_args
    assert args[0].context is first_trigger_context

    # Ensure the 'hello' automation state has the right context
    state = opp.states.get("automation.hello")
    assert state is not None
    assert state.context is first_trigger_context

    # Verify automation triggered evenet for 'bye' automation
    args, _ = event_mock.call_args_list[1]
    second_trigger_context = args[0].context
    assert second_trigger_context.parent_id == first_trigger_context.id
    # Ensure event data has all attributes set
    assert args[0].data.get(ATTR_NAME) is not None
    assert args[0].data.get(ATTR_ENTITY_ID) is not None
    assert args[0].data.get(ATTR_SOURCE) is not None

    # Ensure the service call from the second automation
    # shares the same context
    assert len(calls) == 1
    assert calls[0].context is second_trigger_context


async def test_services.opp, calls):
    """Test the automation services for turning entities on/off."""
    entity_id = "automation.hello"

    assert.opp.states.get(entity_id) is None
    assert not automation.is_on.opp, entity_id)

    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "alias": "hello",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {"service": "test.automation"},
            }
        },
    )

    assert.opp.states.get(entity_id) is not None
    assert automation.is_on.opp, entity_id)

    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 1

    await opp.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {
            ATTR_ENTITY_ID: entity_id,
        },
        blocking=True,
    )

    assert not automation.is_on.opp, entity_id)
    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 1

    await opp.services.async_call(
        automation.DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )

    assert automation.is_on.opp, entity_id)
    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 2

    await opp.services.async_call(
        automation.DOMAIN,
        SERVICE_TOGGLE,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    assert not automation.is_on.opp, entity_id)
    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 2

    await opp.services.async_call(
        automation.DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    await opp.services.async_call(
        automation.DOMAIN, SERVICE_TRIGGER, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    assert len(calls) == 3

    await opp.services.async_call(
        automation.DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    await opp.services.async_call(
        automation.DOMAIN, SERVICE_TRIGGER, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    assert len(calls) == 4

    await opp.services.async_call(
        automation.DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    assert automation.is_on.opp, entity_id)


async def test_reload_config_service.opp, calls, opp_admin_user, opp_read_only_user):
    """Test the reload config service."""
    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "alias": "hello",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {
                    "service": "test.automation",
                    "data_template": {"event": "{{ trigger.event.event_type }}"},
                },
            }
        },
    )
    assert.opp.states.get("automation.hello") is not None
    assert.opp.states.get("automation.bye") is None
    listeners = opp.bus.async_listeners()
    assert listeners.get("test_event") == 1
    assert listeners.get("test_event2") is None

    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].data.get("event") == "test_event"

    test_reload_event = []
    opp.bus.async_listen(
        EVENT_AUTOMATION_RELOADED, lambda event: test_reload_event.append(event)
    )

    with patch(
        "openpeerpower.config.load_yaml_config_file",
        autospec=True,
        return_value={
            automation.DOMAIN: {
                "alias": "bye",
                "trigger": {"platform": "event", "event_type": "test_event2"},
                "action": {
                    "service": "test.automation",
                    "data_template": {"event": "{{ trigger.event.event_type }}"},
                },
            }
        },
    ):
        with pytest.raises(Unauthorized):
            await opp.services.async_call(
                automation.DOMAIN,
                SERVICE_RELOAD,
                context=Context(user_id.opp_read_only_user.id),
                blocking=True,
            )
        await opp.services.async_call(
            automation.DOMAIN,
            SERVICE_RELOAD,
            context=Context(user_id.opp_admin_user.id),
            blocking=True,
        )
        # De-flake ?!
        await opp.async_block_till_done()

    assert len(test_reload_event) == 1

    assert.opp.states.get("automation.hello") is None
    assert.opp.states.get("automation.bye") is not None
    listeners = opp.bus.async_listeners()
    assert listeners.get("test_event") is None
    assert listeners.get("test_event2") == 1

    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 1

    opp.bus.async_fire("test_event2")
    await opp.async_block_till_done()
    assert len(calls) == 2
    assert calls[1].data.get("event") == "test_event2"


async def test_reload_config_when_invalid_config(opp, calls):
    """Test the reload config service handling invalid config."""
    with assert_setup_component(1, automation.DOMAIN):
        assert await async_setup_component(
            opp.
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "hello",
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "action": {
                        "service": "test.automation",
                        "data_template": {"event": "{{ trigger.event.event_type }}"},
                    },
                }
            },
        )
    assert.opp.states.get("automation.hello") is not None

    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].data.get("event") == "test_event"

    with patch(
        "openpeerpower.config.load_yaml_config_file",
        autospec=True,
        return_value={automation.DOMAIN: "not valid"},
    ):
        await opp.services.async_call(automation.DOMAIN, SERVICE_RELOAD, blocking=True)

    assert.opp.states.get("automation.hello") is None

    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_reload_config_handles_load_fails.opp, calls):
    """Test the reload config service."""
    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "alias": "hello",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {
                    "service": "test.automation",
                    "data_template": {"event": "{{ trigger.event.event_type }}"},
                },
            }
        },
    )
    assert.opp.states.get("automation.hello") is not None

    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].data.get("event") == "test_event"

    with patch(
        "openpeerpower.config.load_yaml_config_file",
        side_effect=OpenPeerPowerError("bla"),
    ):
        await opp.services.async_call(automation.DOMAIN, SERVICE_RELOAD, blocking=True)

    assert.opp.states.get("automation.hello") is not None

    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 2


@pytest.mark.parametrize("service", ["turn_off_stop", "turn_off_no_stop", "reload"])
async def test_automation_stops.opp, calls, service):
    """Test that turning off / reloading stops any running actions as appropriate."""
    entity_id = "automation.hello"
    test_entity = "test.entity"

    config = {
        automation.DOMAIN: {
            "alias": "hello",
            "trigger": {"platform": "event", "event_type": "test_event"},
            "action": [
                {"event": "running"},
                {"wait_template": "{{ is_state('test.entity', 'goodbye') }}"},
                {"service": "test.automation"},
            ],
        }
    }
    assert await async_setup_component.opp, automation.DOMAIN, config)

    running = asyncio.Event()

    @callback
    def running_cb(event):
        running.set()

    opp.bus.async_listen_once("running", running_cb)
    opp.states.async_set(test_entity, "hello")

    opp.bus.async_fire("test_event")
    await running.wait()

    if service == "turn_off_stop":
        await opp.services.async_call(
            automation.DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
    elif service == "turn_off_no_stop":
        await opp.services.async_call(
            automation.DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id, automation.CONF_STOP_ACTIONS: False},
            blocking=True,
        )
    else:
        with patch(
            "openpeerpower.config.load_yaml_config_file",
            autospec=True,
            return_value=config,
        ):
            await opp.services.async_call(
                automation.DOMAIN, SERVICE_RELOAD, blocking=True
            )

    opp.states.async_set(test_entity, "goodbye")
    await opp.async_block_till_done()

    assert len(calls) == (1 if service == "turn_off_no_stop" else 0)


async def test_automation_restore_state.opp):
    """Ensure states are restored on startup."""
    time = dt_util.utcnow()

    mock_restore_cache(
        opp.
        (
            State("automation.hello", STATE_ON),
            State("automation.bye", STATE_OFF, {"last_triggered": time}),
        ),
    )

    config = {
        automation.DOMAIN: [
            {
                "alias": "hello",
                "trigger": {"platform": "event", "event_type": "test_event_hello"},
                "action": {"service": "test.automation"},
            },
            {
                "alias": "bye",
                "trigger": {"platform": "event", "event_type": "test_event_bye"},
                "action": {"service": "test.automation"},
            },
        ]
    }

    assert await async_setup_component.opp, automation.DOMAIN, config)

    state = opp.states.get("automation.hello")
    assert state
    assert state.state == STATE_ON
    assert state.attributes["last_triggered"] is None

    state = opp.states.get("automation.bye")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes["last_triggered"] == time

    calls = async_mock_service.opp, "test", "automation")

    assert automation.is_on.opp, "automation.bye") is False

    opp.bus.async_fire("test_event_bye")
    await opp.async_block_till_done()
    assert len(calls) == 0

    assert automation.is_on.opp, "automation.hello")

    opp.bus.async_fire("test_event_hello")
    await opp.async_block_till_done()

    assert len(calls) == 1


async def test_initial_value_off.opp):
    """Test initial value off."""
    calls = async_mock_service.opp, "test", "automation")

    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "alias": "hello",
                "initial_state": "off",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {"service": "test.automation", "entity_id": "hello.world"},
            }
        },
    )
    assert not automation.is_on.opp, "automation.hello")

    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 0


async def test_initial_value_on.opp):
    """Test initial value on."""
    opp.state = CoreState.not_running
    calls = async_mock_service.opp, "test", "automation")

    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "alias": "hello",
                "initial_state": "on",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {
                    "service": "test.automation",
                    "entity_id": ["hello.world", "hello.world2"],
                },
            }
        },
    )
    assert automation.is_on.opp, "automation.hello")

    await opp.async_start()
    await opp.async_block_till_done()
    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_initial_value_off_but_restore_on.opp):
    """Test initial value off and restored state is turned on."""
    opp.state = CoreState.not_running
    calls = async_mock_service.opp, "test", "automation")
    mock_restore_cache.opp, (State("automation.hello", STATE_ON),))

    await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "alias": "hello",
                "initial_state": "off",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {"service": "test.automation", "entity_id": "hello.world"},
            }
        },
    )
    assert not automation.is_on.opp, "automation.hello")

    await opp.async_start()
    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 0


async def test_initial_value_on_but_restore_off.opp):
    """Test initial value on and restored state is turned off."""
    calls = async_mock_service.opp, "test", "automation")
    mock_restore_cache.opp, (State("automation.hello", STATE_OFF),))

    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "alias": "hello",
                "initial_state": "on",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {"service": "test.automation", "entity_id": "hello.world"},
            }
        },
    )
    assert automation.is_on.opp, "automation.hello")

    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_no_initial_value_and_restore_off.opp):
    """Test initial value off and restored state is turned on."""
    calls = async_mock_service.opp, "test", "automation")
    mock_restore_cache.opp, (State("automation.hello", STATE_OFF),))

    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "alias": "hello",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {"service": "test.automation", "entity_id": "hello.world"},
            }
        },
    )
    assert not automation.is_on.opp, "automation.hello")

    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 0


async def test_automation_is_on_if_no_initial_state_or_restore.opp):
    """Test initial value is on when no initial state or restored state."""
    calls = async_mock_service.opp, "test", "automation")

    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "alias": "hello",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {"service": "test.automation", "entity_id": "hello.world"},
            }
        },
    )
    assert automation.is_on.opp, "automation.hello")

    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_automation_not_trigger_on_bootstrap.opp):
    """Test if automation is not trigger on bootstrap."""
    opp.state = CoreState.not_running
    calls = async_mock_service.opp, "test", "automation")

    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "alias": "hello",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {"service": "test.automation", "entity_id": "hello.world"},
            }
        },
    )
    assert automation.is_on.opp, "automation.hello")

    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 0

    opp.bus.async_fire(EVENT_OPENPEERPOWER_STARTED)
    await opp.async_block_till_done()
    assert automation.is_on.opp, "automation.hello")

    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()

    assert len(calls) == 1
    assert ["hello.world"] == calls[0].data.get(ATTR_ENTITY_ID)


async def test_automation_bad_trigger.opp, caplog):
    """Test bad trigger configuration."""
    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "alias": "hello",
                "trigger": {"platform": "automation"},
                "action": [],
            }
        },
    )
    assert "Integration 'automation' does not provide trigger support." in caplog.text


async def test_automation_with_error_in_script.opp, caplog):
    """Test automation with an error in script."""
    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "alias": "hello",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {"service": "test.automation", "entity_id": "hello.world"},
            }
        },
    )

    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert "Service not found" in caplog.text
    assert "Traceback" not in caplog.text


async def test_automation_with_error_in_script_2.opp, caplog):
    """Test automation with an error in script."""
    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "alias": "hello",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {"service": None, "entity_id": "hello.world"},
            }
        },
    )

    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert "string value is None" in caplog.text


async def test_automation_restore_last_triggered_with_initial_state.opp):
    """Ensure last_triggered is restored, even when initial state is set."""
    time = dt_util.utcnow()

    mock_restore_cache(
        opp.
        (
            State("automation.hello", STATE_ON),
            State("automation.bye", STATE_ON, {"last_triggered": time}),
            State("automation.solong", STATE_OFF, {"last_triggered": time}),
        ),
    )

    config = {
        automation.DOMAIN: [
            {
                "alias": "hello",
                "initial_state": "off",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {"service": "test.automation"},
            },
            {
                "alias": "bye",
                "initial_state": "off",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {"service": "test.automation"},
            },
            {
                "alias": "solong",
                "initial_state": "on",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {"service": "test.automation"},
            },
        ]
    }

    await async_setup_component.opp, automation.DOMAIN, config)

    state = opp.states.get("automation.hello")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes["last_triggered"] is None

    state = opp.states.get("automation.bye")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes["last_triggered"] == time

    state = opp.states.get("automation.solong")
    assert state
    assert state.state == STATE_ON
    assert state.attributes["last_triggered"] == time


async def test_extraction_functions.opp):
    """Test extraction functions."""
    assert await async_setup_component(
        opp.
        DOMAIN,
        {
            DOMAIN: [
                {
                    "alias": "test1",
                    "trigger": {"platform": "state", "entity_id": "sensor.trigger_1"},
                    "condition": {
                        "condition": "state",
                        "entity_id": "light.condition_state",
                        "state": "on",
                    },
                    "action": [
                        {
                            "service": "test.script",
                            "data": {"entity_id": "light.in_both"},
                        },
                        {
                            "service": "test.script",
                            "data": {"entity_id": "light.in_first"},
                        },
                        {
                            "domain": "light",
                            "device_id": "device-in-both",
                            "entity_id": "light.bla",
                            "type": "turn_on",
                        },
                    ],
                },
                {
                    "alias": "test2",
                    "trigger": {
                        "platform": "device",
                        "domain": "light",
                        "type": "turned_on",
                        "entity_id": "light.trigger_2",
                        "device_id": "trigger-device-2",
                    },
                    "condition": {
                        "condition": "device",
                        "device_id": "condition-device",
                        "domain": "light",
                        "type": "is_on",
                        "entity_id": "light.bla",
                    },
                    "action": [
                        {
                            "service": "test.script",
                            "data": {"entity_id": "light.in_both"},
                        },
                        {
                            "condition": "state",
                            "entity_id": "sensor.condition",
                            "state": "100",
                        },
                        {"scene": "scene.hello"},
                        {
                            "domain": "light",
                            "device_id": "device-in-both",
                            "entity_id": "light.bla",
                            "type": "turn_on",
                        },
                        {
                            "domain": "light",
                            "device_id": "device-in-last",
                            "entity_id": "light.bla",
                            "type": "turn_on",
                        },
                    ],
                },
            ]
        },
    )

    assert set(automation.automations_with_entity.opp, "light.in_both")) == {
        "automation.test1",
        "automation.test2",
    }
    assert set(automation.entities_in_automation.opp, "automation.test1")) == {
        "sensor.trigger_1",
        "light.condition_state",
        "light.in_both",
        "light.in_first",
    }
    assert set(automation.automations_with_device.opp, "device-in-both")) == {
        "automation.test1",
        "automation.test2",
    }
    assert set(automation.devices_in_automation.opp, "automation.test2")) == {
        "trigger-device-2",
        "condition-device",
        "device-in-both",
        "device-in-last",
    }


async def test_logbook_humanify_automation_triggered_event.opp):
    """Test humanifying Automation Trigger event."""
    opp.config.components.add("recorder")
    await async_setup_component.opp, automation.DOMAIN, {})
    await async_setup_component.opp, "logbook", {})
    entity_attr_cache = logbook.EntityAttributeCache.opp)

    event1, event2 = list(
        logbook.humanify(
            opp.
            [
                MockLazyEventPartialState(
                    EVENT_AUTOMATION_TRIGGERED,
                    {ATTR_ENTITY_ID: "automation.hello", ATTR_NAME: "Hello Automation"},
                ),
                MockLazyEventPartialState(
                    EVENT_AUTOMATION_TRIGGERED,
                    {
                        ATTR_ENTITY_ID: "automation.bye",
                        ATTR_NAME: "Bye Automation",
                        ATTR_SOURCE: "source of trigger",
                    },
                ),
            ],
            entity_attr_cache,
            {},
        )
    )

    assert event1["name"] == "Hello Automation"
    assert event1["domain"] == "automation"
    assert event1["message"] == "has been triggered"
    assert event1["entity_id"] == "automation.hello"

    assert event2["name"] == "Bye Automation"
    assert event2["domain"] == "automation"
    assert event2["message"] == "has been triggered by source of trigger"
    assert event2["entity_id"] == "automation.bye"


async def test_automation_variables.opp, caplog):
    """Test automation variables."""
    calls = async_mock_service.opp, "test", "automation")

    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "variables": {
                        "test_var": "defined_in_config",
                        "event_type": "{{ trigger.event.event_type }}",
                    },
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "action": {
                        "service": "test.automation",
                        "data": {
                            "value": "{{ test_var }}",
                            "event_type": "{{ event_type }}",
                        },
                    },
                },
                {
                    "variables": {
                        "test_var": "defined_in_config",
                    },
                    "trigger": {"platform": "event", "event_type": "test_event_2"},
                    "condition": {
                        "condition": "template",
                        "value_template": "{{ trigger.event.data.pass_condition }}",
                    },
                    "action": {
                        "service": "test.automation",
                    },
                },
                {
                    "variables": {
                        "test_var": "{{ trigger.event.data.break + 1 }}",
                    },
                    "trigger": {"platform": "event", "event_type": "test_event_3"},
                    "action": {
                        "service": "test.automation",
                    },
                },
            ]
        },
    )
    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["value"] == "defined_in_config"
    assert calls[0].data["event_type"] == "test_event"

    opp.bus.async_fire("test_event_2")
    await opp.async_block_till_done()
    assert len(calls) == 1

    opp.bus.async_fire("test_event_2", {"pass_condition": True})
    await opp.async_block_till_done()
    assert len(calls) == 2

    assert "Error rendering variables" not in caplog.text
    opp.bus.async_fire("test_event_3")
    await opp.async_block_till_done()
    assert len(calls) == 2
    assert "Error rendering variables" in caplog.text

    opp.bus.async_fire("test_event_3", {"break": 0})
    await opp.async_block_till_done()
    assert len(calls) == 3


async def test_automation_trigger_variables.opp, caplog):
    """Test automation trigger variables."""
    calls = async_mock_service.opp, "test", "automation")

    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "variables": {
                        "event_type": "{{ trigger.event.event_type }}",
                    },
                    "trigger_variables": {
                        "test_var": "defined_in_config",
                    },
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "action": {
                        "service": "test.automation",
                        "data": {
                            "value": "{{ test_var }}",
                            "event_type": "{{ event_type }}",
                        },
                    },
                },
                {
                    "variables": {
                        "event_type": "{{ trigger.event.event_type }}",
                        "test_var": "overridden_in_config",
                    },
                    "trigger_variables": {
                        "test_var": "defined_in_config",
                    },
                    "trigger": {"platform": "event", "event_type": "test_event_2"},
                    "action": {
                        "service": "test.automation",
                        "data": {
                            "value": "{{ test_var }}",
                            "event_type": "{{ event_type }}",
                        },
                    },
                },
            ]
        },
    )
    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["value"] == "defined_in_config"
    assert calls[0].data["event_type"] == "test_event"

    opp.bus.async_fire("test_event_2")
    await opp.async_block_till_done()
    assert len(calls) == 2
    assert calls[1].data["value"] == "overridden_in_config"
    assert calls[1].data["event_type"] == "test_event_2"

    assert "Error rendering variables" not in caplog.text


async def test_automation_bad_trigger_variables.opp, caplog):
    """Test automation trigger variables accessing.opp is rejected."""
    calls = async_mock_service.opp, "test", "automation")

    assert await async_setup_component(
        opp.
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger_variables": {
                        "test_var": "{{ states('foo.bar') }}",
                    },
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "action": {
                        "service": "test.automation",
                    },
                },
            ]
        },
    )
    opp.bus.async_fire("test_event")
    assert "Use of 'states' is not supported in limited templates" in caplog.text

    await opp.async_block_till_done()
    assert len(calls) == 0


async def test_blueprint_automation.opp, calls):
    """Test blueprint automation."""
    assert await async_setup_component(
        opp.
        "automation",
        {
            "automation": {
                "use_blueprint": {
                    "path": "test_event_service.yaml",
                    "input": {
                        "trigger_event": "blueprint_event",
                        "service_to_call": "test.automation",
                    },
                }
            }
        },
    )
    opp.bus.async_fire("blueprint_event")
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert automation.entities_in_automation.opp, "automation.automation_0") == [
        "light.kitchen"
    ]
