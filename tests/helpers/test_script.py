"""The tests for the Script component."""
# pylint: disable=protected-access
import asyncio
from contextlib import contextmanager
from datetime import timedelta
import logging
from types import MappingProxyType
from unittest import mock
from unittest.mock import patch

from async_timeout import timeout
import pytest
import voluptuous as vol

# Otherwise can't test just this file (import order issue)
from openpeerpower import exceptions
import openpeerpower.components.scene as scene
from openpeerpower.const import ATTR_ENTITY_ID, SERVICE_TURN_ON
from openpeerpowerr.core import Context, CoreState, callback
from openpeerpowerr.helpers import config_validation as cv, script
from openpeerpowerr.setup import async_setup_component
import openpeerpowerr.util.dt as dt_util

from tests.common import (
    async_capture_events,
    async_fire_time_changed,
    async_mock_service,
)

ENTITY_ID = "script.test"


def async_watch_for_action(script_obj, message):
    """Watch for message in last_action."""
    flag = asyncio.Event()

    @callback
    def check_action():
        if script_obj.last_action and message in script_obj.last_action:
            flag.set()

    script_obj.change_listener = check_action
    assert script_obj.change_listener is check_action
    return flag


async def test_firing_event_basic.opp, caplog):
    """Test the firing of events."""
    event = "test_event"
    context = Context()
    events = async_capture_events.opp, event)

    sequence = cv.SCRIPT_SCHEMA({"event": event, "event_data": {"hello": "world"}})
    script_obj = script.Script(
       .opp, sequence, "Test Name", "test_domain", running_description="test script"
    )

    await script_obj.async_run(context=context)
    await opp.async_block_till_done()

    assert len(events) == 1
    assert events[0].context is context
    assert events[0].data.get("hello") == "world"
    assert ".test_name:" in caplog.text
    assert "Test Name: Running test script" in caplog.text


async def test_firing_event_template.opp):
    """Test the firing of events."""
    event = "test_event"
    context = Context()
    events = async_capture_events.opp, event)

    sequence = cv.SCRIPT_SCHEMA(
        {
            "event": event,
            "event_data": {
                "dict": {
                    1: "{{ is_world }}",
                    2: "{{ is_world }}{{ is_world }}",
                    3: "{{ is_world }}{{ is_world }}{{ is_world }}",
                },
                "list": ["{{ is_world }}", "{{ is_world }}{{ is_world }}"],
            },
            "event_data_template": {
                "dict2": {
                    1: "{{ is_world }}",
                    2: "{{ is_world }}{{ is_world }}",
                    3: "{{ is_world }}{{ is_world }}{{ is_world }}",
                },
                "list2": ["{{ is_world }}", "{{ is_world }}{{ is_world }}"],
            },
        }
    )
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")

    await script_obj.async_run(MappingProxyType({"is_world": "yes"}), context=context)
    await opp.async_block_till_done()

    assert len(events) == 1
    assert events[0].context is context
    assert events[0].data == {
        "dict": {1: "yes", 2: "yesyes", 3: "yesyesyes"},
        "list": ["yes", "yesyes"],
        "dict2": {1: "yes", 2: "yesyes", 3: "yesyesyes"},
        "list2": ["yes", "yesyes"],
    }


async def test_calling_service_basic.opp):
    """Test the calling of a service."""
    context = Context()
    calls = async_mock_service.opp, "test", "script")

    sequence = cv.SCRIPT_SCHEMA({"service": "test.script", "data": {"hello": "world"}})
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")

    await script_obj.async_run(context=context)
    await opp.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].context is context
    assert calls[0].data.get("hello") == "world"


async def test_calling_service_template.opp):
    """Test the calling of a service."""
    context = Context()
    calls = async_mock_service.opp, "test", "script")

    sequence = cv.SCRIPT_SCHEMA(
        {
            "service_template": """
            {% if True %}
                test.script
            {% else %}
                test.not_script
            {% endif %}""",
            "data_template": {
                "hello": """
                {% if is_world == 'yes' %}
                    world
                {% else %}
                    not world
                {% endif %}
            """
            },
        }
    )
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")

    await script_obj.async_run(MappingProxyType({"is_world": "yes"}), context=context)
    await opp.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].context is context
    assert calls[0].data.get("hello") == "world"


async def test_data_template_with_templated_key.opp):
    """Test the calling of a service with a data_template with a templated key."""
    context = Context()
    calls = async_mock_service.opp, "test", "script")

    sequence = cv.SCRIPT_SCHEMA(
        {"service": "test.script", "data_template": {"{{ hello_var }}": "world"}}
    )
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")

    await script_obj.async_run(
        MappingProxyType({"hello_var": "hello"}), context=context
    )
    await opp.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].context is context
    assert "hello" in calls[0].data


async def test_multiple_runs_no_wait.opp):
    """Test multiple runs with no wait in script."""
    logger = logging.getLogger("TEST")
    calls = []
    heard_event = asyncio.Event()

    async def async_simulate_long_service(service):
        """Simulate a service that takes a not insignificant time."""
        fire = service.data.get("fire")
        listen = service.data.get("listen")
        service_done = asyncio.Event()

        @callback
        def service_done_cb(event):
            logger.debug("simulated service (%s:%s) done", fire, listen)
            service_done.set()

        calls.append(service)
        logger.debug("simulated service (%s:%s) started", fire, listen)
        unsub = opp.bus.async_listen(str(listen), service_done_cb)
       .opp.bus.async_fire(str(fire))
        await service_done.wait()
        unsub()

   .opp.services.async_register("test", "script", async_simulate_long_service)

    @callback
    def heard_event_cb(event):
        logger.debug("heard: %s", event)
        heard_event.set()

    sequence = cv.SCRIPT_SCHEMA(
        [
            {
                "service": "test.script",
                "data_template": {"fire": "{{ fire1 }}", "listen": "{{ listen1 }}"},
            },
            {
                "service": "test.script",
                "data_template": {"fire": "{{ fire2 }}", "listen": "{{ listen2 }}"},
            },
        ]
    )
    script_obj = script.Script(
       .opp, sequence, "Test Name", "test_domain", script_mode="parallel", max_runs=2
    )

    # Start script twice in such a way that second run will be started while first run
    # is in the middle of the first service call.

    unsub = opp.bus.async_listen("1", heard_event_cb)
    logger.debug("starting 1st script")
   .opp.async_create_task(
        script_obj.async_run(
            MappingProxyType(
                {"fire1": "1", "listen1": "2", "fire2": "3", "listen2": "4"}
            ),
            Context(),
        )
    )
    await asyncio.wait_for(heard_event.wait(), 1)
    unsub()

    logger.debug("starting 2nd script")
    await script_obj.async_run(
        MappingProxyType({"fire1": "2", "listen1": "3", "fire2": "4", "listen2": "4"}),
        Context(),
    )
    await opp.async_block_till_done()

    assert len(calls) == 4


async def test_activating_scene.opp):
    """Test the activation of a scene."""
    context = Context()
    calls = async_mock_service.opp, scene.DOMAIN, SERVICE_TURN_ON)

    sequence = cv.SCRIPT_SCHEMA({"scene": "scene.hello"})
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")

    await script_obj.async_run(context=context)
    await opp.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].context is context
    assert calls[0].data.get(ATTR_ENTITY_ID) == "scene.hello"


@pytest.mark.parametrize("count", [1, 3])
async def test_stop_no_wait.opp, count):
    """Test stopping script."""
    service_started_sem = asyncio.Semaphore(0)
    finish_service_event = asyncio.Event()
    event = "test_event"
    events = async_capture_events.opp, event)

    async def async_simulate_long_service(service):
        """Simulate a service that takes a not insignificant time."""
        service_started_sem.release()
        await finish_service_event.wait()

   .opp.services.async_register("test", "script", async_simulate_long_service)

    sequence = cv.SCRIPT_SCHEMA([{"service": "test.script"}, {"event": event}])
    script_obj = script.Script(
       .opp,
        sequence,
        "Test Name",
        "test_domain",
        script_mode="parallel",
        max_runs=count,
    )

    # Get script started specified number of times and wait until the test.script
    # service has started for each run.
    tasks = []
    for _ in range(count):
       .opp.async_create_task(script_obj.async_run(context=Context()))
        tasks.append.opp.async_create_task(service_started_sem.acquire()))
    await asyncio.wait_for(asyncio.gather(*tasks), 1)

    # Can't assert just yet because we haven't verified stopping works yet.
    # If assert fails we can hang test if async_stop doesn't work.
    script_was_runing = script_obj.is_running
    were_no_events = len(events) == 0

    # Begin the process of stopping the script (which should stop all runs), and then
    # let the service calls complete.
   .opp.async_create_task(script_obj.async_stop())
    finish_service_event.set()

    await opp.async_block_till_done()

    assert script_was_runing
    assert were_no_events
    assert not script_obj.is_running
    assert len(events) == 0


async def test_delay_basic.opp):
    """Test the delay."""
    delay_alias = "delay step"
    sequence = cv.SCRIPT_SCHEMA({"delay": {"seconds": 5}, "alias": delay_alias})
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")
    delay_started_flag = async_watch_for_action(script_obj, delay_alias)

    try:
       .opp.async_create_task(script_obj.async_run(context=Context()))
        await asyncio.wait_for(delay_started_flag.wait(), 1)

        assert script_obj.is_running
        assert script_obj.last_action == delay_alias
    except (AssertionError, asyncio.TimeoutError):
        await script_obj.async_stop()
        raise
    else:
        async_fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=5))
        await opp.async_block_till_done()

        assert not script_obj.is_running
        assert script_obj.last_action is None


async def test_multiple_runs_delay.opp):
    """Test multiple runs with delay in script."""
    event = "test_event"
    events = async_capture_events.opp, event)
    delay = timedelta(seconds=5)
    sequence = cv.SCRIPT_SCHEMA(
        [
            {"event": event, "event_data": {"value": 1}},
            {"delay": delay},
            {"event": event, "event_data": {"value": 2}},
        ]
    )
    script_obj = script.Script(
       .opp, sequence, "Test Name", "test_domain", script_mode="parallel", max_runs=2
    )
    delay_started_flag = async_watch_for_action(script_obj, "delay")

    try:
       .opp.async_create_task(script_obj.async_run(context=Context()))
        await asyncio.wait_for(delay_started_flag.wait(), 1)

        assert script_obj.is_running
        assert len(events) == 1
        assert events[-1].data["value"] == 1
    except (AssertionError, asyncio.TimeoutError):
        await script_obj.async_stop()
        raise
    else:
        # Start second run of script while first run is in a delay.
        script_obj.sequence[1]["alias"] = "delay run 2"
        delay_started_flag = async_watch_for_action(script_obj, "delay run 2")
       .opp.async_create_task(script_obj.async_run(context=Context()))
        await asyncio.wait_for(delay_started_flag.wait(), 1)
        async_fire_time_changed.opp, dt_util.utcnow() + delay)
        await opp.async_block_till_done()

        assert not script_obj.is_running
        assert len(events) == 4
        assert events[-3].data["value"] == 1
        assert events[-2].data["value"] == 2
        assert events[-1].data["value"] == 2


async def test_delay_template_ok.opp):
    """Test the delay as a template."""
    sequence = cv.SCRIPT_SCHEMA({"delay": "00:00:{{ 5 }}"})
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")
    delay_started_flag = async_watch_for_action(script_obj, "delay")

    try:
       .opp.async_create_task(script_obj.async_run(context=Context()))
        await asyncio.wait_for(delay_started_flag.wait(), 1)

        assert script_obj.is_running
    except (AssertionError, asyncio.TimeoutError):
        await script_obj.async_stop()
        raise
    else:
        async_fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=5))
        await opp.async_block_till_done()

        assert not script_obj.is_running


async def test_delay_template_invalid.opp, caplog):
    """Test the delay as a template that fails."""
    event = "test_event"
    events = async_capture_events.opp, event)
    sequence = cv.SCRIPT_SCHEMA(
        [
            {"event": event},
            {"delay": "{{ invalid_delay }}"},
            {"delay": {"seconds": 5}},
            {"event": event},
        ]
    )
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")
    start_idx = len(caplog.records)

    await script_obj.async_run(context=Context())
    await opp.async_block_till_done()

    assert any(
        rec.levelname == "ERROR" and "Error rendering" in rec.message
        for rec in caplog.records[start_idx:]
    )

    assert not script_obj.is_running
    assert len(events) == 1


async def test_delay_template_complex_ok.opp):
    """Test the delay with a working complex template."""
    sequence = cv.SCRIPT_SCHEMA({"delay": {"seconds": "{{ 5 }}"}})
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")
    delay_started_flag = async_watch_for_action(script_obj, "delay")

    try:
       .opp.async_create_task(script_obj.async_run(context=Context()))
        await asyncio.wait_for(delay_started_flag.wait(), 1)
        assert script_obj.is_running
    except (AssertionError, asyncio.TimeoutError):
        await script_obj.async_stop()
        raise
    else:
        async_fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=5))
        await opp.async_block_till_done()

        assert not script_obj.is_running


async def test_delay_template_complex_invalid.opp, caplog):
    """Test the delay with a complex template that fails."""
    event = "test_event"
    events = async_capture_events.opp, event)
    sequence = cv.SCRIPT_SCHEMA(
        [
            {"event": event},
            {"delay": {"seconds": "{{ invalid_delay }}"}},
            {"delay": {"seconds": 5}},
            {"event": event},
        ]
    )
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")
    start_idx = len(caplog.records)

    await script_obj.async_run(context=Context())
    await opp.async_block_till_done()

    assert any(
        rec.levelname == "ERROR" and "Error rendering" in rec.message
        for rec in caplog.records[start_idx:]
    )

    assert not script_obj.is_running
    assert len(events) == 1


async def test_cancel_delay.opp):
    """Test the cancelling while the delay is present."""
    event = "test_event"
    events = async_capture_events.opp, event)
    sequence = cv.SCRIPT_SCHEMA([{"delay": {"seconds": 5}}, {"event": event}])
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")
    delay_started_flag = async_watch_for_action(script_obj, "delay")

    try:
       .opp.async_create_task(script_obj.async_run(context=Context()))
        await asyncio.wait_for(delay_started_flag.wait(), 1)

        assert script_obj.is_running
        assert len(events) == 0
    except (AssertionError, asyncio.TimeoutError):
        await script_obj.async_stop()
        raise
    else:
        await script_obj.async_stop()

        assert not script_obj.is_running

        # Make sure the script is really stopped.

        async_fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=5))
        await opp.async_block_till_done()

        assert not script_obj.is_running
        assert len(events) == 0


@pytest.mark.parametrize("action_type", ["template", "trigger"])
async def test_wait_basic.opp, action_type):
    """Test wait actions."""
    wait_alias = "wait step"
    action = {"alias": wait_alias}
    if action_type == "template":
        action["wait_template"] = "{{ states.switch.test.state == 'off' }}"
    else:
        action["wait_for_trigger"] = {
            "platform": "state",
            "entity_id": "switch.test",
            "to": "off",
        }
    sequence = cv.SCRIPT_SCHEMA(action)
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")
    wait_started_flag = async_watch_for_action(script_obj, wait_alias)

    try:
       .opp.states.async_set("switch.test", "on")
       .opp.async_create_task(script_obj.async_run(context=Context()))
        await asyncio.wait_for(wait_started_flag.wait(), 1)

        assert script_obj.is_running
        assert script_obj.last_action == wait_alias
    except (AssertionError, asyncio.TimeoutError):
        await script_obj.async_stop()
        raise
    else:
       .opp.states.async_set("switch.test", "off")
        await opp.async_block_till_done()

        assert not script_obj.is_running
        assert script_obj.last_action is None


async def test_wait_for_trigger_variables.opp):
    """Test variables are passed to wait_for_trigger action."""
    context = Context()
    wait_alias = "wait step"
    actions = [
        {
            "alias": "variables",
            "variables": {"seconds": 5},
        },
        {
            "alias": wait_alias,
            "wait_for_trigger": {
                "platform": "state",
                "entity_id": "switch.test",
                "to": "off",
                "for": {"seconds": "{{ seconds }}"},
            },
        },
    ]
    sequence = cv.SCRIPT_SCHEMA(actions)
    sequence = await script.async_validate_actions_config.opp, sequence)
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")
    wait_started_flag = async_watch_for_action(script_obj, wait_alias)

    try:
       .opp.states.async_set("switch.test", "on")
       .opp.async_create_task(script_obj.async_run(context=context))
        await asyncio.wait_for(wait_started_flag.wait(), 1)
        assert script_obj.is_running
        assert script_obj.last_action == wait_alias
       .opp.states.async_set("switch.test", "off")
        # the script task +  2 tasks created by wait_for_trigger script step
        await.opp.async_wait_for_task_count(3)
        async_fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=10))
        await opp.async_block_till_done()
    except (AssertionError, asyncio.TimeoutError):
        await script_obj.async_stop()
        raise
    else:
        assert not script_obj.is_running
        assert script_obj.last_action is None


@pytest.mark.parametrize("action_type", ["template", "trigger"])
async def test_wait_basic_times_out.opp, action_type):
    """Test wait actions times out when the action does not happen."""
    wait_alias = "wait step"
    action = {"alias": wait_alias}
    if action_type == "template":
        action["wait_template"] = "{{ states.switch.test.state == 'off' }}"
    else:
        action["wait_for_trigger"] = {
            "platform": "state",
            "entity_id": "switch.test",
            "to": "off",
        }
    sequence = cv.SCRIPT_SCHEMA(action)
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")
    wait_started_flag = async_watch_for_action(script_obj, wait_alias)
    timed_out = False

    try:
       .opp.states.async_set("switch.test", "on")
       .opp.async_create_task(script_obj.async_run(context=Context()))
        await asyncio.wait_for(wait_started_flag.wait(), 1)
        assert script_obj.is_running
        assert script_obj.last_action == wait_alias
       .opp.states.async_set("switch.test", "not_on")

        with timeout(0.1):
            await opp.async_block_till_done()
    except asyncio.TimeoutError:
        timed_out = True
        await script_obj.async_stop()

    assert timed_out


@pytest.mark.parametrize("action_type", ["template", "trigger"])
async def test_multiple_runs_wait.opp, action_type):
    """Test multiple runs with wait in script."""
    event = "test_event"
    events = async_capture_events.opp, event)
    if action_type == "template":
        action = {"wait_template": "{{ states.switch.test.state == 'off' }}"}
    else:
        action = {
            "wait_for_trigger": {
                "platform": "state",
                "entity_id": "switch.test",
                "to": "off",
            }
        }
    sequence = cv.SCRIPT_SCHEMA(
        [
            {"event": event, "event_data": {"value": 1}},
            action,
            {"event": event, "event_data": {"value": 2}},
        ]
    )
    script_obj = script.Script(
       .opp, sequence, "Test Name", "test_domain", script_mode="parallel", max_runs=2
    )
    wait_started_flag = async_watch_for_action(script_obj, "wait")

    try:
       .opp.states.async_set("switch.test", "on")
       .opp.async_create_task(script_obj.async_run(context=Context()))
        await asyncio.wait_for(wait_started_flag.wait(), 1)

        assert script_obj.is_running
        assert len(events) == 1
        assert events[-1].data["value"] == 1

        # Start second run of script while first run is in wait_template.
        wait_started_flag.clear()
       .opp.async_create_task(script_obj.async_run())
        await asyncio.wait_for(wait_started_flag.wait(), 1)
    except (AssertionError, asyncio.TimeoutError):
        await script_obj.async_stop()
        raise
    else:
       .opp.states.async_set("switch.test", "off")
        await opp.async_block_till_done()

        assert not script_obj.is_running
        assert len(events) == 4
        assert events[-3].data["value"] == 1
        assert events[-2].data["value"] == 2
        assert events[-1].data["value"] == 2


@pytest.mark.parametrize("action_type", ["template", "trigger"])
async def test_cancel_wait.opp, action_type):
    """Test the cancelling while wait is present."""
    event = "test_event"
    events = async_capture_events.opp, event)
    if action_type == "template":
        action = {"wait_template": "{{ states.switch.test.state == 'off' }}"}
    else:
        action = {
            "wait_for_trigger": {
                "platform": "state",
                "entity_id": "switch.test",
                "to": "off",
            }
        }
    sequence = cv.SCRIPT_SCHEMA([action, {"event": event}])
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")
    wait_started_flag = async_watch_for_action(script_obj, "wait")

    try:
       .opp.states.async_set("switch.test", "on")
       .opp.async_create_task(script_obj.async_run(context=Context()))
        await asyncio.wait_for(wait_started_flag.wait(), 1)

        assert script_obj.is_running
        assert len(events) == 0
    except (AssertionError, asyncio.TimeoutError):
        await script_obj.async_stop()
        raise
    else:
        await script_obj.async_stop()

        assert not script_obj.is_running

        # Make sure the script is really stopped.

       .opp.states.async_set("switch.test", "off")
        await opp.async_block_till_done()

        assert not script_obj.is_running
        assert len(events) == 0


async def test_wait_template_not_schedule.opp):
    """Test the wait template with correct condition."""
    event = "test_event"
    events = async_capture_events.opp, event)
    sequence = cv.SCRIPT_SCHEMA(
        [
            {"event": event},
            {"wait_template": "{{ states.switch.test.state == 'on' }}"},
            {"event": event},
        ]
    )
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")

   .opp.states.async_set("switch.test", "on")
    await script_obj.async_run(context=Context())
    await opp.async_block_till_done()

    assert not script_obj.is_running
    assert len(events) == 2


@pytest.mark.parametrize(
    "timeout_param", [5, "{{ 5 }}", {"seconds": 5}, {"seconds": "{{ 5 }}"}]
)
@pytest.mark.parametrize("action_type", ["template", "trigger"])
async def test_wait_timeout.opp, caplog, timeout_param, action_type):
    """Test the wait timeout option."""
    event = "test_event"
    events = async_capture_events.opp, event)
    if action_type == "template":
        action = {"wait_template": "{{ states.switch.test.state == 'off' }}"}
    else:
        action = {
            "wait_for_trigger": {
                "platform": "state",
                "entity_id": "switch.test",
                "to": "off",
            }
        }
    action["timeout"] = timeout_param
    action["continue_on_timeout"] = True
    sequence = cv.SCRIPT_SCHEMA([action, {"event": event}])
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")
    wait_started_flag = async_watch_for_action(script_obj, "wait")

    try:
       .opp.states.async_set("switch.test", "on")
       .opp.async_create_task(script_obj.async_run(context=Context()))
        await asyncio.wait_for(wait_started_flag.wait(), 1)

        assert script_obj.is_running
        assert len(events) == 0
    except (AssertionError, asyncio.TimeoutError):
        await script_obj.async_stop()
        raise
    else:
        cur_time = dt_util.utcnow()
        async_fire_time_changed.opp, cur_time + timedelta(seconds=4))
        await asyncio.sleep(0)

        assert len(events) == 0

        async_fire_time_changed.opp, cur_time + timedelta(seconds=5))
        await opp.async_block_till_done()

        assert not script_obj.is_running
        assert len(events) == 1
        assert "(timeout: 0:00:05)" in caplog.text


@pytest.mark.parametrize(
    "continue_on_timeout,n_events", [(False, 0), (True, 1), (None, 1)]
)
@pytest.mark.parametrize("action_type", ["template", "trigger"])
async def test_wait_continue_on_timeout(
   .opp, continue_on_timeout, n_events, action_type
):
    """Test the wait continue_on_timeout option."""
    event = "test_event"
    events = async_capture_events.opp, event)
    if action_type == "template":
        action = {"wait_template": "{{ states.switch.test.state == 'off' }}"}
    else:
        action = {
            "wait_for_trigger": {
                "platform": "state",
                "entity_id": "switch.test",
                "to": "off",
            }
        }
    action["timeout"] = 5
    if continue_on_timeout is not None:
        action["continue_on_timeout"] = continue_on_timeout
    sequence = cv.SCRIPT_SCHEMA([action, {"event": event}])
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")
    wait_started_flag = async_watch_for_action(script_obj, "wait")

    try:
       .opp.states.async_set("switch.test", "on")
       .opp.async_create_task(script_obj.async_run(context=Context()))
        await asyncio.wait_for(wait_started_flag.wait(), 1)

        assert script_obj.is_running
        assert len(events) == 0
    except (AssertionError, asyncio.TimeoutError):
        await script_obj.async_stop()
        raise
    else:
        async_fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=5))
        await opp.async_block_till_done()

        assert not script_obj.is_running
        assert len(events) == n_events


async def test_wait_template_variables_in.opp):
    """Test the wait template with input variables."""
    sequence = cv.SCRIPT_SCHEMA({"wait_template": "{{ is_state(data, 'off') }}"})
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")
    wait_started_flag = async_watch_for_action(script_obj, "wait")

    try:
       .opp.states.async_set("switch.test", "on")
       .opp.async_create_task(
            script_obj.async_run(MappingProxyType({"data": "switch.test"}), Context())
        )
        await asyncio.wait_for(wait_started_flag.wait(), 1)

        assert script_obj.is_running
    except (AssertionError, asyncio.TimeoutError):
        await script_obj.async_stop()
        raise
    else:
       .opp.states.async_set("switch.test", "off")
        await opp.async_block_till_done()

        assert not script_obj.is_running


async def test_wait_template_with_utcnow.opp):
    """Test the wait template with utcnow."""
    sequence = cv.SCRIPT_SCHEMA({"wait_template": "{{ utcnow().hour == 12 }}"})
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")
    wait_started_flag = async_watch_for_action(script_obj, "wait")
    start_time = dt_util.utcnow().replace(minute=1) + timedelta(hours=48)

    try:
        non_maching_time = start_time.replace(hour=3)
        with patch("openpeerpowerr.util.dt.utcnow", return_value=non_maching_time):
           .opp.async_create_task(script_obj.async_run(context=Context()))
            await asyncio.wait_for(wait_started_flag.wait(), 1)
            assert script_obj.is_running

        match_time = start_time.replace(hour=12)
        with patch("openpeerpowerr.util.dt.utcnow", return_value=match_time):
            async_fire_time_changed.opp, match_time)
    except (AssertionError, asyncio.TimeoutError):
        await script_obj.async_stop()
        raise
    else:
        await opp.async_block_till_done()
        assert not script_obj.is_running


async def test_wait_template_with_utcnow_no_match.opp):
    """Test the wait template with utcnow that does not match."""
    sequence = cv.SCRIPT_SCHEMA({"wait_template": "{{ utcnow().hour == 12 }}"})
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")
    wait_started_flag = async_watch_for_action(script_obj, "wait")
    start_time = dt_util.utcnow().replace(minute=1) + timedelta(hours=48)
    timed_out = False

    try:
        non_maching_time = start_time.replace(hour=3)
        with patch("openpeerpowerr.util.dt.utcnow", return_value=non_maching_time):
           .opp.async_create_task(script_obj.async_run(context=Context()))
            await asyncio.wait_for(wait_started_flag.wait(), 1)
            assert script_obj.is_running

        second_non_maching_time = start_time.replace(hour=4)
        with patch(
            "openpeerpowerr.util.dt.utcnow", return_value=second_non_maching_time
        ):
            async_fire_time_changed.opp, second_non_maching_time)

        with timeout(0.1):
            await opp.async_block_till_done()
    except asyncio.TimeoutError:
        timed_out = True
        await script_obj.async_stop()

    assert timed_out


@pytest.mark.parametrize("mode", ["no_timeout", "timeout_finish", "timeout_not_finish"])
@pytest.mark.parametrize("action_type", ["template", "trigger"])
async def test_wait_variables_out.opp, mode, action_type):
    """Test the wait output variable."""
    event = "test_event"
    events = async_capture_events.opp, event)
    if action_type == "template":
        action = {"wait_template": "{{ states.switch.test.state == 'off' }}"}
        event_key = "completed"
    else:
        action = {
            "wait_for_trigger": {
                "platform": "state",
                "entity_id": "switch.test",
                "to": "off",
            }
        }
        event_key = "trigger"
    if mode != "no_timeout":
        action["timeout"] = 5
        action["continue_on_timeout"] = True
    sequence = [
        action,
        {
            "event": event,
            "event_data_template": {
                event_key: f"{{{{ wait.{event_key} }}}}",
                "remaining": "{{ wait.remaining }}",
            },
        },
    ]
    sequence = cv.SCRIPT_SCHEMA(sequence)
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")
    wait_started_flag = async_watch_for_action(script_obj, "wait")

    try:
       .opp.states.async_set("switch.test", "on")
       .opp.async_create_task(script_obj.async_run(context=Context()))
        await asyncio.wait_for(wait_started_flag.wait(), 1)

        assert script_obj.is_running
        assert len(events) == 0
    except (AssertionError, asyncio.TimeoutError):
        await script_obj.async_stop()
        raise
    else:
        if mode == "timeout_not_finish":
            async_fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=5))
        else:
           .opp.states.async_set("switch.test", "off")
        await opp.async_block_till_done()

        assert not script_obj.is_running
        assert len(events) == 1
        if action_type == "template":
            assert events[0].data["completed"] == (mode != "timeout_not_finish")
        elif mode != "timeout_not_finish":
            assert "'to_state': <state switch.test=off" in events[0].data["trigger"]
        else:
            assert events[0].data["trigger"] is None
        remaining = events[0].data["remaining"]
        if mode == "no_timeout":
            assert remaining is None
        elif mode == "timeout_finish":
            assert 0.0 < float(remaining) < 5
        else:
            assert float(remaining) == 0.0


async def test_wait_for_trigger_bad.opp, caplog):
    """Test bad wait_for_trigger."""
    script_obj = script.Script(
       .opp,
        cv.SCRIPT_SCHEMA(
            {"wait_for_trigger": {"platform": "state", "entity_id": "sensor.abc"}}
        ),
        "Test Name",
        "test_domain",
    )

    async def async_attach_trigger_mock(*args, **kwargs):
        return None

    with mock.patch(
        "openpeerpower.components.openpeerpowerr.triggers.state.async_attach_trigger",
        wraps=async_attach_trigger_mock,
    ):
       .opp.async_create_task(script_obj.async_run())
        await opp.async_block_till_done()

    assert "Unknown error while setting up trigger" in caplog.text


async def test_wait_for_trigger_generated_exception.opp, caplog):
    """Test bad wait_for_trigger."""
    script_obj = script.Script(
       .opp,
        cv.SCRIPT_SCHEMA(
            {"wait_for_trigger": {"platform": "state", "entity_id": "sensor.abc"}}
        ),
        "Test Name",
        "test_domain",
    )

    async def async_attach_trigger_mock(*args, **kwargs):
        raise ValueError("something bad")

    with mock.patch(
        "openpeerpower.components.openpeerpowerr.triggers.state.async_attach_trigger",
        wraps=async_attach_trigger_mock,
    ):
       .opp.async_create_task(script_obj.async_run())
        await opp.async_block_till_done()

    assert "Error setting up trigger" in caplog.text
    assert "ValueError" in caplog.text
    assert "something bad" in caplog.text


async def test_condition_warning.opp, caplog):
    """Test warning on condition."""
    event = "test_event"
    events = async_capture_events.opp, event)
    sequence = cv.SCRIPT_SCHEMA(
        [
            {"event": event},
            {
                "condition": "numeric_state",
                "entity_id": "test.entity",
                "above": 0,
            },
            {"event": event},
        ]
    )
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")

    caplog.clear()
    caplog.set_level(logging.WARNING)

   .opp.states.async_set("test.entity", "string")
    await script_obj.async_run(context=Context())
    await opp.async_block_till_done()

    assert len(caplog.record_tuples) == 1
    assert caplog.record_tuples[0][1] == logging.WARNING

    assert len(events) == 1


async def test_condition_basic.opp):
    """Test if we can use conditions in a script."""
    event = "test_event"
    events = async_capture_events.opp, event)
    sequence = cv.SCRIPT_SCHEMA(
        [
            {"event": event},
            {
                "condition": "template",
                "value_template": "{{ states.test.entity.state == 'hello' }}",
            },
            {"event": event},
        ]
    )
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")

   .opp.states.async_set("test.entity", "hello")
    await script_obj.async_run(context=Context())
    await opp.async_block_till_done()

    assert len(events) == 2

   .opp.states.async_set("test.entity", "goodbye")

    await script_obj.async_run(context=Context())
    await opp.async_block_till_done()

    assert len(events) == 3


@patch("openpeerpowerr.helpers.script.condition.async_from_config")
async def test_condition_created_once(async_from_config,.opp):
    """Test that the conditions do not get created multiple times."""
    sequence = cv.SCRIPT_SCHEMA(
        {
            "condition": "template",
            "value_template": '{{ states.test.entity.state == "hello" }}',
        }
    )
    script_obj = script.Script(
       .opp, sequence, "Test Name", "test_domain", script_mode="parallel", max_runs=2
    )

    async_from_config.reset_mock()

   .opp.states.async_set("test.entity", "hello")
    await script_obj.async_run(context=Context())
    await script_obj.async_run(context=Context())
    await opp.async_block_till_done()

    async_from_config.assert_called_once()
    assert len(script_obj._config_cache) == 1


async def test_condition_all_cached.opp):
    """Test that multiple conditions get cached."""
    sequence = cv.SCRIPT_SCHEMA(
        [
            {
                "condition": "template",
                "value_template": '{{ states.test.entity.state == "hello" }}',
            },
            {
                "condition": "template",
                "value_template": '{{ states.test.entity.state != "hello" }}',
            },
        ]
    )
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")

   .opp.states.async_set("test.entity", "hello")
    await script_obj.async_run(context=Context())
    await opp.async_block_till_done()

    assert len(script_obj._config_cache) == 2


async def test_repeat_count.opp):
    """Test repeat action w/ count option."""
    event = "test_event"
    events = async_capture_events.opp, event)
    count = 3

    sequence = cv.SCRIPT_SCHEMA(
        {
            "repeat": {
                "count": count,
                "sequence": {
                    "event": event,
                    "event_data_template": {
                        "first": "{{ repeat.first }}",
                        "index": "{{ repeat.index }}",
                        "last": "{{ repeat.last }}",
                    },
                },
            }
        }
    )
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")

    await script_obj.async_run(context=Context())
    await opp.async_block_till_done()

    assert len(events) == count
    for index, event in enumerate(events):
        assert event.data.get("first") == (index == 0)
        assert event.data.get("index") == index + 1
        assert event.data.get("last") == (index == count - 1)


@pytest.mark.parametrize("condition", ["while", "until"])
async def test_repeat_condition_warning.opp, caplog, condition):
    """Test warning on repeat conditions."""
    event = "test_event"
    events = async_capture_events.opp, event)
    count = 0 if condition == "while" else 1

    sequence = {
        "repeat": {
            "sequence": [
                {
                    "event": event,
                },
            ],
        }
    }
    sequence["repeat"][condition] = {
        "condition": "numeric_state",
        "entity_id": "sensor.test",
        "value_template": "{{ unassigned_variable }}",
        "above": "0",
    }

    script_obj = script.Script(
       .opp, cv.SCRIPT_SCHEMA(sequence), f"Test {condition}", "test_domain"
    )

    # wait_started = async_watch_for_action(script_obj, "wait")
   .opp.states.async_set("sensor.test", "1")

    caplog.clear()
    caplog.set_level(logging.WARNING)

   .opp.async_create_task(script_obj.async_run(context=Context()))
    await asyncio.wait_for.opp.async_block_till_done(), 1)

    assert len(caplog.record_tuples) == 1
    assert caplog.record_tuples[0][1] == logging.WARNING

    assert len(events) == count


@pytest.mark.parametrize("condition", ["while", "until"])
@pytest.mark.parametrize("direct_template", [False, True])
async def test_repeat_conditional.opp, condition, direct_template):
    """Test repeat action w/ while option."""
    event = "test_event"
    events = async_capture_events.opp, event)
    count = 3

    sequence = {
        "repeat": {
            "sequence": [
                {
                    "event": event,
                    "event_data_template": {
                        "first": "{{ repeat.first }}",
                        "index": "{{ repeat.index }}",
                    },
                },
                {"wait_template": "{{ is_state('sensor.test', 'next') }}"},
                {"wait_template": "{{ not is_state('sensor.test', 'next') }}"},
            ],
        }
    }
    if condition == "while":
        template = "{{ not is_state('sensor.test', 'done') }}"
        if direct_template:
            sequence["repeat"]["while"] = template
        else:
            sequence["repeat"]["while"] = {
                "condition": "template",
                "value_template": template,
            }
    else:
        template = "{{ is_state('sensor.test', 'done') }}"
        if direct_template:
            sequence["repeat"]["until"] = template
        else:
            sequence["repeat"]["until"] = {
                "condition": "template",
                "value_template": template,
            }
    script_obj = script.Script(
       .opp, cv.SCRIPT_SCHEMA(sequence), "Test Name", "test_domain"
    )

    wait_started = async_watch_for_action(script_obj, "wait")
   .opp.states.async_set("sensor.test", "1")

   .opp.async_create_task(script_obj.async_run(context=Context()))
    try:
        for index in range(2, count + 1):
            await asyncio.wait_for(wait_started.wait(), 1)
            wait_started.clear()
           .opp.states.async_set("sensor.test", "next")
            await asyncio.wait_for(wait_started.wait(), 1)
            wait_started.clear()
           .opp.states.async_set("sensor.test", index)
        await asyncio.wait_for(wait_started.wait(), 1)
        wait_started.clear()
       .opp.states.async_set("sensor.test", "next")
        await asyncio.wait_for(wait_started.wait(), 1)
        wait_started.clear()
       .opp.states.async_set("sensor.test", "done")
        await asyncio.wait_for.opp.async_block_till_done(), 1)
    except asyncio.TimeoutError:
        await script_obj.async_stop()
        raise

    assert len(events) == count
    for index, event in enumerate(events):
        assert event.data.get("first") == (index == 0)
        assert event.data.get("index") == index + 1


@pytest.mark.parametrize("condition", ["while", "until"])
async def test_repeat_var_in_condition.opp, condition):
    """Test repeat action w/ while option."""
    event = "test_event"
    events = async_capture_events.opp, event)

    sequence = {"repeat": {"sequence": {"event": event}}}
    if condition == "while":
        sequence["repeat"]["while"] = {
            "condition": "template",
            "value_template": "{{ repeat.index <= 2 }}",
        }
    else:
        sequence["repeat"]["until"] = {
            "condition": "template",
            "value_template": "{{ repeat.index == 2 }}",
        }
    script_obj = script.Script(
       .opp, cv.SCRIPT_SCHEMA(sequence), "Test Name", "test_domain"
    )

    with mock.patch(
        "openpeerpowerr.helpers.condition._LOGGER.error",
        side_effect=AssertionError("Template Error"),
    ):
        await script_obj.async_run(context=Context())

    assert len(events) == 2


@pytest.mark.parametrize(
    "variables,first_last,inside_x",
    [
        (None, {"repeat": None, "x": None}, None),
        (MappingProxyType({"x": 1}), {"repeat": None, "x": 1}, 1),
    ],
)
async def test_repeat_nested.opp, variables, first_last, inside_x):
    """Test nested repeats."""
    event = "test_event"
    events = async_capture_events.opp, event)

    sequence = cv.SCRIPT_SCHEMA(
        [
            {
                "event": event,
                "event_data_template": {
                    "repeat": "{{ None if repeat is not defined else repeat }}",
                    "x": "{{ None if x is not defined else x }}",
                },
            },
            {
                "repeat": {
                    "count": 2,
                    "sequence": [
                        {
                            "event": event,
                            "event_data_template": {
                                "first": "{{ repeat.first }}",
                                "index": "{{ repeat.index }}",
                                "last": "{{ repeat.last }}",
                                "x": "{{ None if x is not defined else x }}",
                            },
                        },
                        {
                            "repeat": {
                                "count": 2,
                                "sequence": {
                                    "event": event,
                                    "event_data_template": {
                                        "first": "{{ repeat.first }}",
                                        "index": "{{ repeat.index }}",
                                        "last": "{{ repeat.last }}",
                                        "x": "{{ None if x is not defined else x }}",
                                    },
                                },
                            }
                        },
                        {
                            "event": event,
                            "event_data_template": {
                                "first": "{{ repeat.first }}",
                                "index": "{{ repeat.index }}",
                                "last": "{{ repeat.last }}",
                                "x": "{{ None if x is not defined else x }}",
                            },
                        },
                    ],
                }
            },
            {
                "event": event,
                "event_data_template": {
                    "repeat": "{{ None if repeat is not defined else repeat }}",
                    "x": "{{ None if x is not defined else x }}",
                },
            },
        ]
    )
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")

    with mock.patch(
        "openpeerpowerr.helpers.condition._LOGGER.error",
        side_effect=AssertionError("Template Error"),
    ):
        await script_obj.async_run(variables, Context())

    assert len(events) == 10
    assert events[0].data == first_last
    assert events[-1].data == first_last
    for index, result in enumerate(
        (
            (True, 1, False, inside_x),
            (True, 1, False, inside_x),
            (False, 2, True, inside_x),
            (True, 1, False, inside_x),
            (False, 2, True, inside_x),
            (True, 1, False, inside_x),
            (False, 2, True, inside_x),
            (False, 2, True, inside_x),
        ),
        1,
    ):
        assert events[index].data == {
            "first": result[0],
            "index": result[1],
            "last": result[2],
            "x": result[3],
        }


async def test_choose_warning.opp, caplog):
    """Test warning on choose."""
    event = "test_event"
    events = async_capture_events.opp, event)

    sequence = cv.SCRIPT_SCHEMA(
        {
            "choose": [
                {
                    "conditions": {
                        "condition": "numeric_state",
                        "entity_id": "test.entity",
                        "value_template": "{{ undefined_a + undefined_b }}",
                        "above": 1,
                    },
                    "sequence": {"event": event, "event_data": {"choice": "first"}},
                },
                {
                    "conditions": {
                        "condition": "numeric_state",
                        "entity_id": "test.entity",
                        "value_template": "{{ 'string' }}",
                        "above": 2,
                    },
                    "sequence": {"event": event, "event_data": {"choice": "second"}},
                },
            ],
            "default": {"event": event, "event_data": {"choice": "default"}},
        }
    )
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")

   .opp.states.async_set("test.entity", "9")
    await opp.async_block_till_done()

    caplog.clear()
    caplog.set_level(logging.WARNING)

    await script_obj.async_run(context=Context())
    await opp.async_block_till_done()

    assert len(caplog.record_tuples) == 2
    assert caplog.record_tuples[0][1] == logging.WARNING
    assert caplog.record_tuples[1][1] == logging.WARNING

    assert len(events) == 1
    assert events[0].data["choice"] == "default"


@pytest.mark.parametrize("var,result", [(1, "first"), (2, "second"), (3, "default")])
async def test_choose.opp, var, result):
    """Test choose action."""
    event = "test_event"
    events = async_capture_events.opp, event)
    sequence = cv.SCRIPT_SCHEMA(
        {
            "choose": [
                {
                    "conditions": {
                        "condition": "template",
                        "value_template": "{{ var == 1 }}",
                    },
                    "sequence": {"event": event, "event_data": {"choice": "first"}},
                },
                {
                    "conditions": "{{ var == 2 }}",
                    "sequence": {"event": event, "event_data": {"choice": "second"}},
                },
            ],
            "default": {"event": event, "event_data": {"choice": "default"}},
        }
    )
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")

    await script_obj.async_run(MappingProxyType({"var": var}), Context())
    await opp.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["choice"] == result


@pytest.mark.parametrize(
    "action",
    [
        {"repeat": {"count": 1, "sequence": {"event": "abc"}}},
        {"choose": {"conditions": [], "sequence": {"event": "abc"}}},
        {"choose": [], "default": {"event": "abc"}},
    ],
)
async def test_multiple_runs_repeat_choose.opp, caplog, action):
    """Test parallel runs with repeat & choose actions & max_runs > default."""
    max_runs = script.DEFAULT_MAX + 1
    script_obj = script.Script(
       .opp,
        cv.SCRIPT_SCHEMA(action),
        "Test Name",
        "test_domain",
        script_mode="parallel",
        max_runs=max_runs,
    )

    events = async_capture_events.opp, "abc")
    for _ in range(max_runs):
       .opp.async_create_task(script_obj.async_run(context=Context()))
    await opp.async_block_till_done()

    assert "WARNING" not in caplog.text
    assert "ERROR" not in caplog.text
    assert len(events) == max_runs


async def test_last_triggered.opp):
    """Test the last_triggered."""
    event = "test_event"
    sequence = cv.SCRIPT_SCHEMA({"event": event})
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")

    assert script_obj.last_triggered is None

    time = dt_util.utcnow()
    with mock.patch("openpeerpowerr.helpers.script.utcnow", return_value=time):
        await script_obj.async_run(context=Context())
        await opp.async_block_till_done()

    assert script_obj.last_triggered == time


async def test_propagate_error_service_not_found.opp):
    """Test that a script aborts when a service is not found."""
    event = "test_event"
    events = async_capture_events.opp, event)
    sequence = cv.SCRIPT_SCHEMA([{"service": "test.script"}, {"event": event}])
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")

    with pytest.raises(exceptions.ServiceNotFound):
        await script_obj.async_run(context=Context())

    assert len(events) == 0
    assert not script_obj.is_running


async def test_propagate_error_invalid_service_data.opp):
    """Test that a script aborts when we send invalid service data."""
    event = "test_event"
    events = async_capture_events.opp, event)
    calls = async_mock_service.opp, "test", "script", vol.Schema({"text": str}))
    sequence = cv.SCRIPT_SCHEMA(
        [{"service": "test.script", "data": {"text": 1}}, {"event": event}]
    )
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")

    with pytest.raises(vol.Invalid):
        await script_obj.async_run(context=Context())

    assert len(events) == 0
    assert len(calls) == 0
    assert not script_obj.is_running


async def test_propagate_error_service_exception.opp):
    """Test that a script aborts when a service throws an exception."""
    event = "test_event"
    events = async_capture_events.opp, event)

    @callback
    def record_call(service):
        """Add recorded event to set."""
        raise ValueError("BROKEN")

   .opp.services.async_register("test", "script", record_call)

    sequence = cv.SCRIPT_SCHEMA([{"service": "test.script"}, {"event": event}])
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")

    with pytest.raises(ValueError):
        await script_obj.async_run(context=Context())

    assert len(events) == 0
    assert not script_obj.is_running


async def test_referenced_entities.opp):
    """Test referenced entities."""
    script_obj = script.Script(
       .opp,
        cv.SCRIPT_SCHEMA(
            [
                {
                    "service": "test.script",
                    "data": {"entity_id": "light.service_not_list"},
                },
                {
                    "service": "test.script",
                    "data": {"entity_id": ["light.service_list"]},
                },
                {
                    "service": "test.script",
                    "data": {"entity_id": "{{ 'light.service_template' }}"},
                },
                {
                    "service": "test.script",
                    "entity_id": "light.direct_entity_referenced",
                },
                {
                    "service": "test.script",
                    "target": {"entity_id": "light.entity_in_target"},
                },
                {
                    "service": "test.script",
                    "data_template": {"entity_id": "light.entity_in_data_template"},
                },
                {
                    "condition": "state",
                    "entity_id": "sensor.condition",
                    "state": "100",
                },
                {"service": "test.script", "data": {"without": "entity_id"}},
                {"scene": "scene.hello"},
                {"event": "test_event"},
                {"delay": "{{ delay_period }}"},
            ]
        ),
        "Test Name",
        "test_domain",
    )
    assert script_obj.referenced_entities == {
        "light.service_not_list",
        "light.service_list",
        "sensor.condition",
        "scene.hello",
        "light.direct_entity_referenced",
        "light.entity_in_target",
        "light.entity_in_data_template",
    }
    # Test we cache results.
    assert script_obj.referenced_entities is script_obj.referenced_entities


async def test_referenced_devices.opp):
    """Test referenced entities."""
    script_obj = script.Script(
       .opp,
        cv.SCRIPT_SCHEMA(
            [
                {"domain": "light", "device_id": "script-dev-id"},
                {
                    "condition": "device",
                    "device_id": "condition-dev-id",
                    "domain": "switch",
                },
                {
                    "service": "test.script",
                    "data": {"device_id": "data-string-id"},
                },
                {
                    "service": "test.script",
                    "data_template": {"device_id": "data-template-string-id"},
                },
                {
                    "service": "test.script",
                    "target": {"device_id": "target-string-id"},
                },
                {
                    "service": "test.script",
                    "target": {"device_id": ["target-list-id-1", "target-list-id-2"]},
                },
            ]
        ),
        "Test Name",
        "test_domain",
    )
    assert script_obj.referenced_devices == {
        "script-dev-id",
        "condition-dev-id",
        "data-string-id",
        "data-template-string-id",
        "target-string-id",
        "target-list-id-1",
        "target-list-id-2",
    }
    # Test we cache results.
    assert script_obj.referenced_devices is script_obj.referenced_devices


@contextmanager
def does_not_raise():
    """Indicate no exception is expected."""
    yield


async def test_script_mode_single.opp, caplog):
    """Test overlapping runs with max_runs = 1."""
    event = "test_event"
    events = async_capture_events.opp, event)
    sequence = cv.SCRIPT_SCHEMA(
        [
            {"event": event, "event_data": {"value": 1}},
            {"wait_template": "{{ states.switch.test.state == 'off' }}"},
            {"event": event, "event_data": {"value": 2}},
        ]
    )
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")
    wait_started_flag = async_watch_for_action(script_obj, "wait")

    try:
       .opp.states.async_set("switch.test", "on")
       .opp.async_create_task(script_obj.async_run(context=Context()))
        await asyncio.wait_for(wait_started_flag.wait(), 1)

        assert script_obj.is_running
        assert len(events) == 1
        assert events[0].data["value"] == 1

        # Start second run of script while first run is suspended in wait_template.

        await script_obj.async_run(context=Context())

        assert "Already running" in caplog.text
        assert script_obj.is_running
    except (AssertionError, asyncio.TimeoutError):
        await script_obj.async_stop()
        raise
    else:
       .opp.states.async_set("switch.test", "off")
        await opp.async_block_till_done()

        assert not script_obj.is_running
        assert len(events) == 2
        assert events[1].data["value"] == 2


@pytest.mark.parametrize("max_exceeded", [None, "WARNING", "INFO", "ERROR", "SILENT"])
@pytest.mark.parametrize(
    "script_mode,max_runs", [("single", 1), ("parallel", 2), ("queued", 2)]
)
async def test_max_exceeded.opp, caplog, max_exceeded, script_mode, max_runs):
    """Test max_exceeded option."""
    sequence = cv.SCRIPT_SCHEMA(
        {"wait_template": "{{ states.switch.test.state == 'off' }}"}
    )
    if max_exceeded is None:
        script_obj = script.Script(
           .opp,
            sequence,
            "Test Name",
            "test_domain",
            script_mode=script_mode,
            max_runs=max_runs,
        )
    else:
        script_obj = script.Script(
           .opp,
            sequence,
            "Test Name",
            "test_domain",
            script_mode=script_mode,
            max_runs=max_runs,
            max_exceeded=max_exceeded,
        )
   .opp.states.async_set("switch.test", "on")
    for _ in range(max_runs + 1):
       .opp.async_create_task(script_obj.async_run(context=Context()))
   .opp.states.async_set("switch.test", "off")
    await opp.async_block_till_done()
    if max_exceeded is None:
        max_exceeded = "WARNING"
    if max_exceeded == "SILENT":
        assert not any(
            any(
                message in rec.message
                for message in ("Already running", "Maximum number of runs exceeded")
            )
            for rec in caplog.records
        )
    else:
        assert any(
            rec.levelname == max_exceeded
            and any(
                message in rec.message
                for message in ("Already running", "Maximum number of runs exceeded")
            )
            for rec in caplog.records
        )


@pytest.mark.parametrize(
    "script_mode,messages,last_events",
    [("restart", ["Restarting"], [2]), ("parallel", [], [2, 2])],
)
async def test_script_mode_2.opp, caplog, script_mode, messages, last_events):
    """Test overlapping runs with max_runs > 1."""
    event = "test_event"
    events = async_capture_events.opp, event)
    sequence = cv.SCRIPT_SCHEMA(
        [
            {"event": event, "event_data": {"value": 1}},
            {"wait_template": "{{ states.switch.test.state == 'off' }}"},
            {"event": event, "event_data": {"value": 2}},
        ]
    )
    logger = logging.getLogger("TEST")
    max_runs = 1 if script_mode == "restart" else 2
    script_obj = script.Script(
       .opp,
        sequence,
        "Test Name",
        "test_domain",
        script_mode=script_mode,
        max_runs=max_runs,
        logger=logger,
    )
    wait_started_flag = async_watch_for_action(script_obj, "wait")

    try:
       .opp.states.async_set("switch.test", "on")
       .opp.async_create_task(script_obj.async_run(context=Context()))
        await asyncio.wait_for(wait_started_flag.wait(), 1)

        assert script_obj.is_running
        assert len(events) == 1
        assert events[0].data["value"] == 1

        # Start second run of script while first run is suspended in wait_template.

        wait_started_flag.clear()
       .opp.async_create_task(script_obj.async_run(context=Context()))
        await asyncio.wait_for(wait_started_flag.wait(), 1)

        assert script_obj.is_running
        assert len(events) == 2
        assert events[1].data["value"] == 1
        assert all(
            any(
                rec.levelname == "INFO"
                and rec.name == "TEST"
                and message in rec.message
                for rec in caplog.records
            )
            for message in messages
        )
    except (AssertionError, asyncio.TimeoutError):
        await script_obj.async_stop()
        raise
    else:
       .opp.states.async_set("switch.test", "off")
        await opp.async_block_till_done()

        assert not script_obj.is_running
        assert len(events) == 2 + len(last_events)
        for idx, value in enumerate(last_events, start=2):
            assert events[idx].data["value"] == value


async def test_script_mode_queued.opp):
    """Test overlapping runs with script_mode = 'queued' & max_runs > 1."""
    event = "test_event"
    events = async_capture_events.opp, event)
    sequence = cv.SCRIPT_SCHEMA(
        [
            {"event": event, "event_data": {"value": 1}},
            {
                "wait_template": "{{ states.switch.test.state == 'off' }}",
                "alias": "wait_1",
            },
            {"event": event, "event_data": {"value": 2}},
            {
                "wait_template": "{{ states.switch.test.state == 'on' }}",
                "alias": "wait_2",
            },
        ]
    )
    logger = logging.getLogger("TEST")
    script_obj = script.Script(
       .opp,
        sequence,
        "Test Name",
        "test_domain",
        script_mode="queued",
        max_runs=2,
        logger=logger,
    )

    watch_messages = []

    @callback
    def check_action():
        for message, flag in watch_messages:
            if script_obj.last_action and message in script_obj.last_action:
                flag.set()

    script_obj.change_listener = check_action
    wait_started_flag_1 = asyncio.Event()
    watch_messages.append(("wait_1", wait_started_flag_1))
    wait_started_flag_2 = asyncio.Event()
    watch_messages.append(("wait_2", wait_started_flag_2))

    try:
        assert not script_obj.is_running
        assert script_obj.runs == 0

       .opp.states.async_set("switch.test", "on")
       .opp.async_create_task(script_obj.async_run(context=Context()))
        await asyncio.wait_for(wait_started_flag_1.wait(), 1)

        assert script_obj.is_running
        assert script_obj.runs == 1
        assert len(events) == 1
        assert events[0].data["value"] == 1

        # Start second run of script while first run is suspended in wait_template.
        # This second run should not start until the first run has finished.

       .opp.async_create_task(script_obj.async_run(context=Context()))
        await asyncio.sleep(0)

        assert script_obj.is_running
        assert script_obj.runs == 2
        assert len(events) == 1

       .opp.states.async_set("switch.test", "off")
        await asyncio.wait_for(wait_started_flag_2.wait(), 1)

        assert script_obj.is_running
        assert script_obj.runs == 2
        assert len(events) == 2
        assert events[1].data["value"] == 2

        wait_started_flag_1.clear()
       .opp.states.async_set("switch.test", "on")
        await asyncio.wait_for(wait_started_flag_1.wait(), 1)

        assert script_obj.is_running
        assert script_obj.runs == 1
        assert len(events) == 3
        assert events[2].data["value"] == 1
    except (AssertionError, asyncio.TimeoutError):
        await script_obj.async_stop()
        raise
    else:
       .opp.states.async_set("switch.test", "off")
        await asyncio.sleep(0)
       .opp.states.async_set("switch.test", "on")
        await opp.async_block_till_done()

        assert not script_obj.is_running
        assert script_obj.runs == 0
        assert len(events) == 4
        assert events[3].data["value"] == 2


async def test_script_mode_queued_cancel.opp):
    """Test canceling with a queued run."""
    script_obj = script.Script(
       .opp,
        cv.SCRIPT_SCHEMA({"wait_template": "{{ false }}"}),
        "Test Name",
        "test_domain",
        script_mode="queued",
        max_runs=2,
    )
    wait_started_flag = async_watch_for_action(script_obj, "wait")

    try:
        assert not script_obj.is_running
        assert script_obj.runs == 0

        task1 = opp.async_create_task(script_obj.async_run(context=Context()))
        await asyncio.wait_for(wait_started_flag.wait(), 1)
        task2 = opp.async_create_task(script_obj.async_run(context=Context()))
        await asyncio.sleep(0)

        assert script_obj.is_running
        assert script_obj.runs == 2

        with pytest.raises(asyncio.CancelledError):
            task2.cancel()
            await task2

        assert script_obj.is_running
        assert script_obj.runs == 1

        with pytest.raises(asyncio.CancelledError):
            task1.cancel()
            await task1

        assert not script_obj.is_running
        assert script_obj.runs == 0
    except (AssertionError, asyncio.TimeoutError):
        await script_obj.async_stop()
        raise


async def test_script_logging.opp, caplog):
    """Test script logging."""
    script_obj = script.Script.opp, [], "Script with % Name", "test_domain")
    script_obj._log("Test message with name %s", 1)

    assert "Script with % Name: Test message with name 1" in caplog.text


async def test_shutdown_at.opp, caplog):
    """Test stopping scripts at shutdown."""
    delay_alias = "delay step"
    sequence = cv.SCRIPT_SCHEMA({"delay": {"seconds": 120}, "alias": delay_alias})
    script_obj = script.Script.opp, sequence, "test script", "test_domain")
    delay_started_flag = async_watch_for_action(script_obj, delay_alias)

    try:
       .opp.async_create_task(script_obj.async_run(context=Context()))
        await asyncio.wait_for(delay_started_flag.wait(), 1)

        assert script_obj.is_running
        assert script_obj.last_action == delay_alias
    except (AssertionError, asyncio.TimeoutError):
        await script_obj.async_stop()
        raise
    else:
       .opp.bus.async_fire("openpeerpowerr_stop")
        await opp.async_block_till_done()

        assert not script_obj.is_running
        assert "Stopping scripts running at shutdown: test script" in caplog.text


async def test_shutdown_after.opp, caplog):
    """Test stopping scripts at shutdown."""
    delay_alias = "delay step"
    sequence = cv.SCRIPT_SCHEMA({"delay": {"seconds": 120}, "alias": delay_alias})
    script_obj = script.Script.opp, sequence, "test script", "test_domain")
    delay_started_flag = async_watch_for_action(script_obj, delay_alias)

   .opp.state = CoreState.stopping
   .opp.bus.async_fire("openpeerpowerr_stop")
    await opp.async_block_till_done()

    try:
       .opp.async_create_task(script_obj.async_run(context=Context()))
        await asyncio.wait_for(delay_started_flag.wait(), 1)

        assert script_obj.is_running
        assert script_obj.last_action == delay_alias
    except (AssertionError, asyncio.TimeoutError):
        await script_obj.async_stop()
        raise
    else:
        async_fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=60))
        await opp.async_block_till_done()

        assert not script_obj.is_running
        assert (
            "Stopping scripts running too long after shutdown: test script"
            in caplog.text
        )


async def test_update_logger.opp, caplog):
    """Test updating logger."""
    sequence = cv.SCRIPT_SCHEMA({"event": "test_event"})
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")

    await script_obj.async_run(context=Context())
    await opp.async_block_till_done()

    assert script.__name__ in caplog.text

    log_name = "testing.123"
    script_obj.update_logger(logging.getLogger(log_name))

    await script_obj.async_run(context=Context())
    await opp.async_block_till_done()

    assert log_name in caplog.text


async def test_started_action.opp, caplog):
    """Test the callback of started_action."""
    event = "test_event"
    log_message = "The script started!"
    logger = logging.getLogger("TEST")

    sequence = cv.SCRIPT_SCHEMA({"event": event})
    script_obj = script.Script.opp, sequence, "Test Name", "test_domain")

    @callback
    def started_action():
        logger.info(log_message)

    await script_obj.async_run(context=Context(), started_action=started_action)
    await opp.async_block_till_done()

    assert log_message in caplog.text


async def test_set_variable.opp, caplog):
    """Test setting variables in scripts."""
    sequence = cv.SCRIPT_SCHEMA(
        [
            {"variables": {"variable": "value"}},
            {"service": "test.script", "data": {"value": "{{ variable }}"}},
        ]
    )
    script_obj = script.Script.opp, sequence, "test script", "test_domain")

    mock_calls = async_mock_service.opp, "test", "script")

    await script_obj.async_run(context=Context())
    await opp.async_block_till_done()

    assert mock_calls[0].data["value"] == "value"


async def test_set_redefines_variable.opp, caplog):
    """Test setting variables based on their current value."""
    sequence = cv.SCRIPT_SCHEMA(
        [
            {"variables": {"variable": "1"}},
            {"service": "test.script", "data": {"value": "{{ variable }}"}},
            {"variables": {"variable": "{{ variable | int + 1 }}"}},
            {"service": "test.script", "data": {"value": "{{ variable }}"}},
        ]
    )
    script_obj = script.Script.opp, sequence, "test script", "test_domain")

    mock_calls = async_mock_service.opp, "test", "script")

    await script_obj.async_run(context=Context())
    await opp.async_block_till_done()

    assert mock_calls[0].data["value"] == 1
    assert mock_calls[1].data["value"] == 2


async def test_validate_action_config.opp):
    """Validate action config."""
    configs = {
        cv.SCRIPT_ACTION_CALL_SERVICE: {"service": "light.turn_on"},
        cv.SCRIPT_ACTION_DELAY: {"delay": 5},
        cv.SCRIPT_ACTION_WAIT_TEMPLATE: {
            "wait_template": "{{ states.light.kitchen.state == 'on' }}"
        },
        cv.SCRIPT_ACTION_FIRE_EVENT: {"event": "my_event"},
        cv.SCRIPT_ACTION_CHECK_CONDITION: {
            "condition": "{{ states.light.kitchen.state == 'on' }}"
        },
        cv.SCRIPT_ACTION_DEVICE_AUTOMATION: {
            "domain": "light",
            "entity_id": "light.kitchen",
            "device_id": "abcd",
            "type": "turn_on",
        },
        cv.SCRIPT_ACTION_ACTIVATE_SCENE: {"scene": "scene.relax"},
        cv.SCRIPT_ACTION_REPEAT: {
            "repeat": {"count": 3, "sequence": [{"event": "repeat_event"}]}
        },
        cv.SCRIPT_ACTION_CHOOSE: {
            "choose": [
                {
                    "condition": "{{ states.light.kitchen.state == 'on' }}",
                    "sequence": [{"event": "choose_event"}],
                }
            ],
            "default": [{"event": "choose_default_event"}],
        },
        cv.SCRIPT_ACTION_WAIT_FOR_TRIGGER: {
            "wait_for_trigger": [
                {"platform": "event", "event_type": "wait_for_trigger_event"}
            ]
        },
        cv.SCRIPT_ACTION_VARIABLES: {"variables": {"hello": "world"}},
    }

    for key in cv.ACTION_TYPE_SCHEMAS:
        assert key in configs, f"No validate config test found for {key}"

    # Verify we raise if we don't know the action type
    with patch(
        "openpeerpowerr.helpers.config_validation.determine_script_action",
        return_value="non-existing",
    ), pytest.raises(ValueError):
        await script.async_validate_action_config.opp, {})

    for action_type, config in configs.items():
        assert cv.determine_script_action(config) == action_type
        try:
            await script.async_validate_action_config.opp, config)
        except vol.Invalid as err:
            assert False, f"{action_type} config invalid: {err}"


async def test_embedded_wait_for_trigger_in_automation.opp):
    """Test an embedded wait for trigger."""
    assert await async_setup_component(
       .opp,
        "automation",
        {
            "automation": {
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {
                    "repeat": {
                        "while": [
                            {
                                "condition": "template",
                                "value_template": '{{ is_state("test.value1", "trigger-while") }}',
                            }
                        ],
                        "sequence": [
                            {"event": "trigger_wait_event"},
                            {
                                "wait_for_trigger": [
                                    {
                                        "platform": "template",
                                        "value_template": '{{ is_state("test.value2", "trigger-wait") }}',
                                    }
                                ]
                            },
                            {"service": "test.script"},
                        ],
                    }
                },
            }
        },
    )

   .opp.states.async_set("test.value1", "trigger-while")
   .opp.states.async_set("test.value2", "not-trigger-wait")
    mock_calls = async_mock_service.opp, "test", "script")

    async def trigger_wait_event(_):
        # give script the time to attach the trigger.
        await asyncio.sleep(0)
       .opp.states.async_set("test.value1", "not-trigger-while")
       .opp.states.async_set("test.value2", "trigger-wait")

   .opp.bus.async_listen("trigger_wait_event", trigger_wait_event)

    # Start automation
   .opp.bus.async_fire("test_event")

    await opp.async_block_till_done()

    assert len(mock_calls) == 1
