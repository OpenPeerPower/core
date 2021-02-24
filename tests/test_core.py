"""Test to verify that Open Peer Power core works."""
# pylint: disable=protected-access
import asyncio
from datetime import datetime, timedelta
import functools
import logging
import os
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, Mock, PropertyMock, patch

import pytest
import pytz
import voluptuous as vol

from openpeerpower.const import (
    ATTR_FRIENDLY_NAME,
    ATTR_NOW,
    ATTR_SECONDS,
    CONF_UNIT_SYSTEM,
    EVENT_CALL_SERVICE,
    EVENT_CORE_CONFIG_UPDATE,
    EVENT_OPENPEERPOWER_CLOSE,
    EVENT_OPENPEERPOWER_FINAL_WRITE,
    EVENT_OPENPEERPOWER_START,
    EVENT_OPENPEERPOWER_STARTED,
    EVENT_OPENPEERPOWER_STOP,
    EVENT_SERVICE_REGISTERED,
    EVENT_SERVICE_REMOVED,
    EVENT_STATE_CHANGED,
    EVENT_TIME_CHANGED,
    EVENT_TIMER_OUT_OF_SYNC,
    MATCH_ALL,
    __version__,
)
import openpeerpower.core as ha
from openpeerpower.exceptions import (
    InvalidEntityFormatError,
    InvalidStateError,
    ServiceNotFound,
)
import openpeerpower.util.dt as dt_util
from openpeerpower.util.unit_system import METRIC_SYSTEM

from tests.common import async_capture_events, async_mock_service

PST = pytz.timezone("America/Los_Angeles")


def test_split_entity_id():
    """Test split_entity_id."""
    assert op_split_entity_id("domain.object_id") == ["domain", "object_id"]


def test_async_add_opp_job_schedule_callback():
    """Test that we schedule coroutines and add jobs to the job pool."""
   opp =  MagicMock()
    job = MagicMock()

    op.OpenPeerPower.async_add_opp_job.opp, op.OppJob(op.callback(job)))
    assert len.opp.loop.call_soon.mock_calls) == 1
    assert len.opp.loop.create_task.mock_calls) == 0
    assert len.opp.add_job.mock_calls) == 0


def test_async_add_opp_job_schedule_partial_callback():
    """Test that we schedule partial coros and add jobs to the job pool."""
   opp =  MagicMock()
    job = MagicMock()
    partial = functools.partial(op.callback(job))

    op.OpenPeerPower.async_add_opp_job.opp, op.OppJob(partial))
    assert len.opp.loop.call_soon.mock_calls) == 1
    assert len.opp.loop.create_task.mock_calls) == 0
    assert len.opp.add_job.mock_calls) == 0


def test_async_add_opp_job_schedule_coroutinefunction(loop):
    """Test that we schedule coroutines and add jobs to the job pool."""
   opp =  MagicMock(loop=MagicMock(wraps=loop))

    async def job():
        pass

    op.OpenPeerPower.async_add_opp_job.opp, op.OppJob(job))
    assert len.opp.loop.call_soon.mock_calls) == 0
    assert len.opp.loop.create_task.mock_calls) == 1
    assert len.opp.add_job.mock_calls) == 0


def test_async_add_opp_job_schedule_partial_coroutinefunction(loop):
    """Test that we schedule partial coros and add jobs to the job pool."""
   opp =  MagicMock(loop=MagicMock(wraps=loop))

    async def job():
        pass

    partial = functools.partial(job)

    op.OpenPeerPower.async_add_opp_job.opp, op.OppJob(partial))
    assert len.opp.loop.call_soon.mock_calls) == 0
    assert len.opp.loop.create_task.mock_calls) == 1
    assert len.opp.add_job.mock_calls) == 0


def test_async_add_job_add_opp_threaded_job_to_pool():
    """Test that we schedule coroutines and add jobs to the job pool."""
   opp =  MagicMock()

    def job():
        pass

    op.OpenPeerPower.async_add_opp_job.opp, op.OppJob(job))
    assert len.opp.loop.call_soon.mock_calls) == 0
    assert len.opp.loop.create_task.mock_calls) == 0
    assert len.opp.loop.run_in_executor.mock_calls) == 1


def test_async_create_task_schedule_coroutine(loop):
    """Test that we schedule coroutines and add jobs to the job pool."""
   opp =  MagicMock(loop=MagicMock(wraps=loop))

    async def job():
        pass

    op.OpenPeerPower.async_create_task.opp, job())
    assert len.opp.loop.call_soon.mock_calls) == 0
    assert len.opp.loop.create_task.mock_calls) == 1
    assert len.opp.add_job.mock_calls) == 0


def test_async_run_opp_job_calls_callback():
    """Test that the callback annotation is respected."""
   opp =  MagicMock()
    calls = []

    def job():
        calls.append(1)

    op.OpenPeerPower.async_run_opp_job.opp, op.OppJob(op.callback(job)))
    assert len(calls) == 1
    assert len.opp.async_add_job.mock_calls) == 0


def test_async_run_opp_job_delegates_non_async():
    """Test that the callback annotation is respected."""
   opp =  MagicMock()
    calls = []

    def job():
        calls.append(1)

    op.OpenPeerPower.async_run_opp_job.opp, op.OppJob(job))
    assert len(calls) == 0
    assert len.opp.async_add_opp_job.mock_calls) == 1


async def test_stage_shutdown.opp):
    """Simulate a shutdown, test calling stuff."""
    test_stop = async_capture_events.opp, EVENT_OPENPEERPOWER_STOP)
    test_final_write = async_capture_events.opp, EVENT_OPENPEERPOWER_FINAL_WRITE)
    test_close = async_capture_events.opp, EVENT_OPENPEERPOWER_CLOSE)
    test_all = async_capture_events.opp, MATCH_ALL)

    await opp.async_stop()

    assert len(test_stop) == 1
    assert len(test_close) == 1
    assert len(test_final_write) == 1
    assert len(test_all) == 2


async def test_shutdown_calls_block_till_done_after_shutdown_run_callback_threadsafe(
    opp,
):
    """Ensure shutdown_run_callback_threadsafe is called before the final async_block_till_done."""
    stop_calls = []

    async def _record_block_till_done():
        nonlocal stop_calls
        stop_calls.append("async_block_till_done")

    def _record_shutdown_run_callback_threadsafe(loop):
        nonlocal stop_calls
        stop_calls.append(("shutdown_run_callback_threadsafe", loop))

    with patch.object.opp, "async_block_till_done", _record_block_till_done), patch(
        "openpeerpower.core.shutdown_run_callback_threadsafe",
        _record_shutdown_run_callback_threadsafe,
    ):
        await opp.async_stop()

    assert stop_calls[-2] == ("shutdown_run_callback_threadsafe", opp.loop)
    assert stop_calls[-1] == "async_block_till_done"


async def test_pending_sheduler.opp):
    """Add a coro to pending tasks."""
    call_count = []

    async def test_coro():
        """Test Coro."""
        call_count.append("call")

    for _ in range(3):
        opp.async_add_job(test_coro())

    await asyncio.wait.opp._pending_tasks)

    assert len.opp._pending_tasks) == 3
    assert len(call_count) == 3


async def test_async_add_job_pending_tasks_coro.opp):
    """Add a coro to pending tasks."""
    call_count = []

    async def test_coro():
        """Test Coro."""
        call_count.append("call")

    for _ in range(2):
        opp.add_job(test_coro())

    async def wait_finish_callback():
        """Wait until all stuff is scheduled."""
        await asyncio.sleep(0)
        await asyncio.sleep(0)

    await wait_finish_callback()

    assert len.opp._pending_tasks) == 2
    await opp.async_block_till_done()
    assert len(call_count) == 2


async def test_async_add_job_pending_tasks_executor.opp):
    """Run an executor in pending tasks."""
    call_count = []

    def test_executor():
        """Test executor."""
        call_count.append("call")

    async def wait_finish_callback():
        """Wait until all stuff is scheduled."""
        await asyncio.sleep(0)
        await asyncio.sleep(0)

    for _ in range(2):
        opp.async_add_job(test_executor)

    await wait_finish_callback()

    assert len.opp._pending_tasks) == 2
    await opp.async_block_till_done()
    assert len(call_count) == 2


async def test_async_add_job_pending_tasks_callback.opp):
    """Run a callback in pending tasks."""
    call_count = []

    @op.callback
    def test_callback():
        """Test callback."""
        call_count.append("call")

    async def wait_finish_callback():
        """Wait until all stuff is scheduled."""
        await asyncio.sleep(0)
        await asyncio.sleep(0)

    for _ in range(2):
        opp.async_add_job(test_callback)

    await wait_finish_callback()

    await opp.async_block_till_done()

    assert len.opp._pending_tasks) == 0
    assert len(call_count) == 2


async def test_add_job_with_none.opp):
    """Try to add a job with None as function."""
    with pytest.raises(ValueError):
        opp.async_add_job(None, "test_arg")


def test_event_eq():
    """Test events."""
    now = dt_util.utcnow()
    data = {"some": "attr"}
    context = op.Context()
    event1, event2 = [
        op.Event("some_type", data, time_fired=now, context=context) for _ in range(2)
    ]

    assert event1 == event2


def test_event_repr():
    """Test that Event repr method works."""
    assert str(op.Event("TestEvent")) == "<Event TestEvent[L]>"

    assert (
        str(op.Event("TestEvent", {"beer": "nice"}, op.EventOrigin.remote))
        == "<Event TestEvent[R]: beer=nice>"
    )


def test_event_as_dict():
    """Test an Event as dictionary."""
    event_type = "some_type"
    now = dt_util.utcnow()
    data = {"some": "attr"}

    event = op.Event(event_type, data, op.EventOrigin.local, now)
    expected = {
        "event_type": event_type,
        "data": data,
        "origin": "LOCAL",
        "time_fired": now.isoformat(),
        "context": {
            "id": event.context.id,
            "parent_id": None,
            "user_id": event.context.user_id,
        },
    }
    assert event.as_dict() == expected
    # 2nd time to verify cache
    assert event.as_dict() == expected


def test_state_as_dict():
    """Test a State as dictionary."""
    last_time = datetime(1984, 12, 8, 12, 0, 0)
    state = op.State(
        "happy.happy",
        "on",
        {"pig": "dog"},
        last_updated=last_time,
        last_changed=last_time,
    )
    expected = {
        "context": {
            "id": state.context.id,
            "parent_id": None,
            "user_id": state.context.user_id,
        },
        "entity_id": "happy.happy",
        "attributes": {"pig": "dog"},
        "last_changed": last_time.isoformat(),
        "last_updated": last_time.isoformat(),
        "state": "on",
    }
    assert state.as_dict() == expected
    # 2nd time to verify cache
    assert state.as_dict() == expected
    assert state.as_dict() is state.as_dict()


async def test_eventbus_add_remove_listener.opp):
    """Test remove_listener method."""
    old_count = len.opp.bus.async_listeners())

    def listener(_):
        pass

    unsub = opp.bus.async_listen("test", listener)

    assert old_count + 1 == len.opp.bus.async_listeners())

    # Remove listener
    unsub()
    assert old_count == len.opp.bus.async_listeners())

    # Should do nothing now
    unsub()


async def test_eventbus_filtered_listener.opp):
    """Test we can prefilter events."""
    calls = []

    @op.callback
    def listener(event):
        """Mock listener."""
        calls.append(event)

    @op.callback
    def filter(event):
        """Mock filter."""
        return not event.data["filtered"]

    unsub = opp.bus.async_listen("test", listener, event_filter=filter)

    opp.bus.async_fire("test", {"filtered": True})
    await opp.async_block_till_done()

    assert len(calls) == 0

    opp.bus.async_fire("test", {"filtered": False})
    await opp.async_block_till_done()

    assert len(calls) == 1

    unsub()


async def test_eventbus_unsubscribe_listener.opp):
    """Test unsubscribe listener from returned function."""
    calls = []

    @op.callback
    def listener(event):
        """Mock listener."""
        calls.append(event)

    unsub = opp.bus.async_listen("test", listener)

    opp.bus.async_fire("test")
    await opp.async_block_till_done()

    assert len(calls) == 1

    unsub()

    opp.bus.async_fire("event")
    await opp.async_block_till_done()

    assert len(calls) == 1


async def test_eventbus_listen_once_event_with_callback.opp):
    """Test listen_once_event method."""
    runs = []

    @op.callback
    def event_handler(event):
        runs.append(event)

    opp.bus.async_listen_once("test_event", event_handler)

    opp.bus.async_fire("test_event")
    # Second time it should not increase runs
    opp.bus.async_fire("test_event")

    await opp.async_block_till_done()
    assert len(runs) == 1


async def test_eventbus_listen_once_event_with_coroutine.opp):
    """Test listen_once_event method."""
    runs = []

    async def event_handler(event):
        runs.append(event)

    opp.bus.async_listen_once("test_event", event_handler)

    opp.bus.async_fire("test_event")
    # Second time it should not increase runs
    opp.bus.async_fire("test_event")

    await opp.async_block_till_done()
    assert len(runs) == 1


async def test_eventbus_listen_once_event_with_thread.opp):
    """Test listen_once_event method."""
    runs = []

    def event_handler(event):
        runs.append(event)

    opp.bus.async_listen_once("test_event", event_handler)

    opp.bus.async_fire("test_event")
    # Second time it should not increase runs
    opp.bus.async_fire("test_event")

    await opp.async_block_till_done()
    assert len(runs) == 1


async def test_eventbus_thread_event_listener.opp):
    """Test thread event listener."""
    thread_calls = []

    def thread_listener(event):
        thread_calls.append(event)

    opp.bus.async_listen("test_thread", thread_listener)
    opp.bus.async_fire("test_thread")
    await opp.async_block_till_done()
    assert len(thread_calls) == 1


async def test_eventbus_callback_event_listener.opp):
    """Test callback event listener."""
    callback_calls = []

    @op.callback
    def callback_listener(event):
        callback_calls.append(event)

    opp.bus.async_listen("test_callback", callback_listener)
    opp.bus.async_fire("test_callback")
    await opp.async_block_till_done()
    assert len(callback_calls) == 1


async def test_eventbus_coroutine_event_listener.opp):
    """Test coroutine event listener."""
    coroutine_calls = []

    async def coroutine_listener(event):
        coroutine_calls.append(event)

    opp.bus.async_listen("test_coroutine", coroutine_listener)
    opp.bus.async_fire("test_coroutine")
    await opp.async_block_till_done()
    assert len(coroutine_calls) == 1


def test_state_init():
    """Test state.init."""
    with pytest.raises(InvalidEntityFormatError):
        op.State("invalid_entity_format", "test_state")

    with pytest.raises(InvalidStateError):
        op.State("domain.long_state", "t" * 256)


def test_state_domain():
    """Test domain."""
    state = op.State("some_domain.hello", "world")
    assert state.domain == "some_domain"


def test_state_object_id():
    """Test object ID."""
    state = op.State("domain.hello", "world")
    assert state.object_id == "hello"


def test_state_name_if_no_friendly_name_attr():
    """Test if there is no friendly name."""
    state = op.State("domain.hello_world", "world")
    assert state.name == "hello world"


def test_state_name_if_friendly_name_attr():
    """Test if there is a friendly name."""
    name = "Some Unique Name"
    state = op.State("domain.hello_world", "world", {ATTR_FRIENDLY_NAME: name})
    assert state.name == name


def test_state_dict_conversion():
    """Test conversion of dict."""
    state = op.State("domain.hello", "world", {"some": "attr"})
    assert state == op.State.from_dict(state.as_dict())


def test_state_dict_conversion_with_wrong_data():
    """Test conversion with wrong data."""
    assert op.State.from_dict(None) is None
    assert op.State.from_dict({"state": "yes"}) is None
    assert op.State.from_dict({"entity_id": "yes"}) is None
    # Make sure invalid context data doesn't crash
    wrong_context = op.State.from_dict(
        {
            "entity_id": "light.kitchen",
            "state": "on",
            "context": {"id": "123", "non-existing": "crash"},
        }
    )
    assert wrong_context is not None
    assert wrong_context.context.id == "123"


def test_state_repr():
    """Test state.repr."""
    assert (
        str(op.State("happy.happy", "on", last_changed=datetime(1984, 12, 8, 12, 0, 0)))
        == "<state happy.happy=on @ 1984-12-08T12:00:00+00:00>"
    )

    assert (
        str(
            op.State(
                "happy.happy",
                "on",
                {"brightness": 144},
                datetime(1984, 12, 8, 12, 0, 0),
            )
        )
        == "<state happy.happy=on; brightness=144 @ "
        "1984-12-08T12:00:00+00:00>"
    )


async def test_statemachine_is_state.opp):
    """Test is_state method."""
    opp.states.async_set("light.bowl", "on", {})
    assert.opp.states.is_state("light.Bowl", "on")
    assert not.opp.states.is_state("light.Bowl", "off")
    assert not.opp.states.is_state("light.Non_existing", "on")


async def test_statemachine_entity_ids.opp):
    """Test get_entity_ids method."""
    opp.states.async_set("light.bowl", "on", {})
    opp.states.async_set("SWITCH.AC", "off", {})
    ent_ids = opp.states.async_entity_ids()
    assert len(ent_ids) == 2
    assert "light.bowl" in ent_ids
    assert "switch.ac" in ent_ids

    ent_ids = opp.states.async_entity_ids("light")
    assert len(ent_ids) == 1
    assert "light.bowl" in ent_ids

    states = sorted(state.entity_id for state in.opp.states.async_all())
    assert states == ["light.bowl", "switch.ac"]


async def test_statemachine_remove.opp):
    """Test remove method."""
    opp.states.async_set("light.bowl", "on", {})
    events = async_capture_events.opp, EVENT_STATE_CHANGED)

    assert "light.bowl" in.opp.states.async_entity_ids()
    assert.opp.states.async_remove("light.bowl")
    await opp.async_block_till_done()

    assert "light.bowl" not in.opp.states.async_entity_ids()
    assert len(events) == 1
    assert events[0].data.get("entity_id") == "light.bowl"
    assert events[0].data.get("old_state") is not None
    assert events[0].data["old_state"].entity_id == "light.bowl"
    assert events[0].data.get("new_state") is None

    # If it does not exist, we should get False
    assert not.opp.states.async_remove("light.Bowl")
    await opp.async_block_till_done()
    assert len(events) == 1


async def test_statemachine_case_insensitivty.opp):
    """Test insensitivty."""
    events = async_capture_events.opp, EVENT_STATE_CHANGED)

    opp.states.async_set("light.BOWL", "off")
    await opp.async_block_till_done()

    assert.opp.states.is_state("light.bowl", "off")
    assert len(events) == 1


async def test_statemachine_last_changed_not_updated_on_same_state.opp):
    """Test to not update the existing, same state."""
    opp.states.async_set("light.bowl", "on", {})
    state = opp.states.get("light.Bowl")

    future = dt_util.utcnow() + timedelta(hours=10)

    with patch("openpeerpower.util.dt.utcnow", return_value=future):
        opp.states.async_set("light.Bowl", "on", {"attr": "triggers_change"})
        await opp.async_block_till_done()

    state2 = opp.states.get("light.Bowl")
    assert state2 is not None
    assert state.last_changed == state2.last_changed


async def test_statemachine_force_update.opp):
    """Test force update option."""
    opp.states.async_set("light.bowl", "on", {})
    events = async_capture_events.opp, EVENT_STATE_CHANGED)

    opp.states.async_set("light.bowl", "on")
    await opp.async_block_till_done()
    assert len(events) == 0

    opp.states.async_set("light.bowl", "on", None, True)
    await opp.async_block_till_done()
    assert len(events) == 1


def test_service_call_repr():
    """Test ServiceCall repr."""
    call = op.ServiceCall("openpeerpower", "start")
    assert str(call) == f"<ServiceCall openpeerpower.start (c:{call.context.id})>"

    call2 = op.ServiceCall("openpeerpower", "start", {"fast": "yes"})
    assert (
        str(call2)
        == f"<ServiceCall openpeerpower.start (c:{call2.context.id}): fast=yes>"
    )


async def test_serviceregistry_op._service.opp):
    """Test has_service method."""
    opp.services.async_register("test_domain", "test_service", lambda call: None)
    assert len.opp.services.async_services()) == 1
    assert.opp.services.has_service("tesT_domaiN", "tesT_servicE")
    assert not.opp.services.has_service("test_domain", "non_existing")
    assert not.opp.services.has_service("non_existing", "test_service")


async def test_serviceregistry_call_with_blocking_done_in_time.opp):
    """Test call with blocking."""
    registered_events = async_capture_events.opp, EVENT_SERVICE_REGISTERED)
    calls = async_mock_service.opp, "test_domain", "register_calls")
    await opp.async_block_till_done()

    assert len(registered_events) == 1
    assert registered_events[0].data["domain"] == "test_domain"
    assert registered_events[0].data["service"] == "register_calls"

    assert await opp.services.async_call(
        "test_domain", "REGISTER_CALLS", blocking=True
    )
    assert len(calls) == 1


async def test_serviceregistry_call_non_existing_with_blocking.opp):
    """Test non-existing with blocking."""
    with pytest.raises(op.ServiceNotFound):
        await opp.services.async_call("test_domain", "i_do_not_exist", blocking=True)


async def test_serviceregistry_async_service.opp):
    """Test registering and calling an async service."""
    calls = []

    async def service_handler(call):
        """Service handler coroutine."""
        calls.append(call)

    opp.services.async_register("test_domain", "register_calls", service_handler)

    assert await opp.services.async_call(
        "test_domain", "REGISTER_CALLS", blocking=True
    )
    assert len(calls) == 1


async def test_serviceregistry_async_service_partial.opp):
    """Test registering and calling an wrapped async service."""
    calls = []

    async def service_handler(call):
        """Service handler coroutine."""
        calls.append(call)

    opp.services.async_register(
        "test_domain", "register_calls", functools.partial(service_handler)
    )
    await opp.async_block_till_done()

    assert await opp.services.async_call(
        "test_domain", "REGISTER_CALLS", blocking=True
    )
    assert len(calls) == 1


async def test_serviceregistry_callback_service.opp):
    """Test registering and calling an async service."""
    calls = []

    @op.callback
    def service_handler(call):
        """Service handler coroutine."""
        calls.append(call)

    opp.services.async_register("test_domain", "register_calls", service_handler)

    assert await opp.services.async_call(
        "test_domain", "REGISTER_CALLS", blocking=True
    )
    assert len(calls) == 1


async def test_serviceregistry_remove_service.opp):
    """Test remove service."""
    calls_remove = async_capture_events.opp, EVENT_SERVICE_REMOVED)

    opp.services.async_register("test_domain", "test_service", lambda call: None)
    assert.opp.services.has_service("test_Domain", "test_Service")

    opp.services.async_remove("test_Domain", "test_Service")
    await opp.async_block_till_done()

    assert not.opp.services.has_service("test_Domain", "test_Service")
    assert len(calls_remove) == 1
    assert calls_remove[-1].data["domain"] == "test_domain"
    assert calls_remove[-1].data["service"] == "test_service"


async def test_serviceregistry_service_that_not_exists(opp):
    """Test remove service that not exists."""
    calls_remove = async_capture_events.opp, EVENT_SERVICE_REMOVED)
    assert not.opp.services.has_service("test_xxx", "test_yyy")
    opp.services.async_remove("test_xxx", "test_yyy")
    await opp.async_block_till_done()
    assert len(calls_remove) == 0

    with pytest.raises(ServiceNotFound):
        await opp.services.async_call("test_do_not", "exist", {})


async def test_serviceregistry_async_service_raise_exception.opp):
    """Test registering and calling an async service raise exception."""

    async def service_handler(_):
        """Service handler coroutine."""
        raise ValueError

    opp.services.async_register("test_domain", "register_calls", service_handler)

    with pytest.raises(ValueError):
        assert await opp.services.async_call(
            "test_domain", "REGISTER_CALLS", blocking=True
        )

    # Non-blocking service call never throw exception
    await opp.services.async_call("test_domain", "REGISTER_CALLS", blocking=False)
    await opp.async_block_till_done()


async def test_serviceregistry_callback_service_raise_exception.opp):
    """Test registering and calling an callback service raise exception."""

    @op.callback
    def service_handler(_):
        """Service handler coroutine."""
        raise ValueError

    opp.services.async_register("test_domain", "register_calls", service_handler)

    with pytest.raises(ValueError):
        assert await opp.services.async_call(
            "test_domain", "REGISTER_CALLS", blocking=True
        )

    # Non-blocking service call never throw exception
    await opp.services.async_call("test_domain", "REGISTER_CALLS", blocking=False)
    await opp.async_block_till_done()


def test_config_defaults():
    """Test config defaults."""
   opp =  Mock()
    config = op.config(opp)
    assert config(opp is.opp
    assert config.latitude == 0
    assert config.longitude == 0
    assert config.elevation == 0
    assert config.location_name == "Home"
    assert config.time_zone == dt_util.UTC
    assert config.internal_url is None
    assert config.external_url is None
    assert config.config_source == "default"
    assert config.skip_pip is False
    assert config.components == set()
    assert config.api is None
    assert config.config_dir is None
    assert config.allowlist_external_dirs == set()
    assert config.allowlist_external_urls == set()
    assert config.media_dirs == {}
    assert config.safe_mode is False
    assert config.legacy_templates is False


def test_config_path_with_file():
    """Test get_config_path method."""
    config = op.Config(None)
    config.config_dir = "/test/ha-config"
    assert config.path("test.conf") == "/test/ha-config/test.conf"


def test_config_path_with_dir_and_file():
    """Test get_config_path method."""
    config = op.Config(None)
    config.config_dir = "/test/ha-config"
    assert config.path("dir", "test.conf") == "/test/ha-config/dir/test.conf"


def test_config_as_dict():
    """Test as dict."""
    config = op.Config(None)
    config.config_dir = "/test/ha-config"
    config opp =MagicMock()
    type(config(opp.state).value = PropertyMock(return_value="RUNNING")
    expected = {
        "latitude": 0,
        "longitude": 0,
        "elevation": 0,
        CONF_UNIT_SYSTEM: METRIC_SYSTEM.as_dict(),
        "location_name": "Home",
        "time_zone": "UTC",
        "components": set(),
        "config_dir": "/test/ha-config",
        "whitelist_external_dirs": set(),
        "allowlist_external_dirs": set(),
        "allowlist_external_urls": set(),
        "version": __version__,
        "config_source": "default",
        "safe_mode": False,
        "state": "RUNNING",
        "external_url": None,
        "internal_url": None,
    }

    assert expected == config.as_dict()


def test_config_is_allowed_path():
    """Test is_allowed_path method."""
    config = op.Config(None)
    with TemporaryDirectory() as tmp_dir:
        # The created dir is in /tmp. This is a symlink on OS X
        # causing this test to fail unless we resolve path first.
        config.allowlist_external_dirs = {os.path.realpath(tmp_dir)}

        test_file = os.path.join(tmp_dir, "test.jpg")
        with open(test_file, "w") as tmp_file:
            tmp_file.write("test")

        valid = [test_file, tmp_dir, os.path.join(tmp_dir, "notfound321")]
        for path in valid:
            assert config.is_allowed_path(path)

        config.allowlist_external_dirs = {"/home", "/var"}

        invalid = [
            ".opp/config/secure",
            "/etc/passwd",
            "/root/secure_file",
            "/var/../etc/passwd",
            test_file,
        ]
        for path in invalid:
            assert not config.is_allowed_path(path)

        with pytest.raises(AssertionError):
            config.is_allowed_path(None)


def test_config_is_allowed_external_url():
    """Test is_allowed_external_url method."""
    config = op.Config(None)
    config.allowlist_external_urls = [
        "http://x.com/",
        "https://y.com/bla/",
        "https://z.com/images/1.jpg/",
    ]

    valid = [
        "http://x.com/1.jpg",
        "http://x.com",
        "https://y.com/bla/",
        "https://y.com/bla/2.png",
        "https://z.com/images/1.jpg",
    ]
    for url in valid:
        assert config.is_allowed_external_url(url)

    invalid = [
        "https://a.co",
        "https://y.com/bla_wrong",
        "https://y.com/bla/../image.jpg",
        "https://z.com/images",
    ]
    for url in invalid:
        assert not config.is_allowed_external_url(url)


async def test_event_on_update.opp):
    """Test that event is fired on update."""
    events = []

    @op.callback
    def callback(event):
        events.append(event)

    opp.bus.async_listen(EVENT_CORE_CONFIG_UPDATE, callback)

    assert.opp.config.latitude != 12

    await opp.config.async_update(latitude=12)
    await opp.async_block_till_done()

    assert.opp.config.latitude == 12
    assert len(events) == 1
    assert events[0].data == {"latitude": 12}


async def test_bad_timezone_raises_value_error(opp):
    """Test bad timezone raises ValueError."""
    with pytest.raises(ValueError):
        await opp.config.async_update(time_zone="not_a_timezone")


@patch("openpeerpower.core.monotonic")
def test_create_timer(mock_monotonic, loop):
    """Test create timer."""
   opp =  MagicMock()
    funcs = []
    orig_callback = op.callback

    def mock_callback(func):
        funcs.append(func)
        return orig_callback(func)

    mock_monotonic.side_effect = 10.2, 10.8, 11.3

    with patch.object(ha, "callback", mock_callback), patch(
        "openpeerpower.core.dt_util.utcnow",
        return_value=datetime(2018, 12, 31, 3, 4, 5, 333333),
    ):
        op._async_create_timer.opp)

    assert len(funcs) == 2
    fire_time_event, stop_timer = funcs

    assert len.opp.loop.call_later.mock_calls) == 1
    delay, callback, target = opp.loop.call_later.mock_calls[0][1]
    assert abs(delay - 0.666667) < 0.001
    assert callback is fire_time_event
    assert abs(target - 10.866667) < 0.001

    with patch(
        "openpeerpower.core.dt_util.utcnow",
        return_value=datetime(2018, 12, 31, 3, 4, 6, 100000),
    ):
        callback(target)

    assert len.opp.bus.async_listen_once.mock_calls) == 1
    assert len.opp.bus.async_fire.mock_calls) == 1
    assert len.opp.loop.call_later.mock_calls) == 2

    event_type, callback = opp.bus.async_listen_once.mock_calls[0][1]
    assert event_type == EVENT_OPENPEERPOWER_STOP
    assert callback is stop_timer

    delay, callback, target = opp.loop.call_later.mock_calls[1][1]
    assert abs(delay - 0.9) < 0.001
    assert callback is fire_time_event
    assert abs(target - 12.2) < 0.001

    event_type, event_data = opp.bus.async_fire.mock_calls[0][1]
    assert event_type == EVENT_TIME_CHANGED
    assert event_data[ATTR_NOW] == datetime(2018, 12, 31, 3, 4, 6, 100000)


@patch("openpeerpower.core.monotonic")
def test_timer_out_of_sync(mock_monotonic, loop):
    """Test create timer."""
   opp =  MagicMock()
    funcs = []
    orig_callback = op.callback

    def mock_callback(func):
        funcs.append(func)
        return orig_callback(func)

    mock_monotonic.side_effect = 10.2, 13.3, 13.4

    with patch.object(ha, "callback", mock_callback), patch(
        "openpeerpower.core.dt_util.utcnow",
        return_value=datetime(2018, 12, 31, 3, 4, 5, 333333),
    ):
        op._async_create_timer.opp)

    delay, callback, target = opp.loop.call_later.mock_calls[0][1]

    with patch(
        "openpeerpower.core.dt_util.utcnow",
        return_value=datetime(2018, 12, 31, 3, 4, 8, 200000),
    ):
        callback(target)

        _, event_0_args, event_0_kwargs = opp.bus.async_fire.mock_calls[0]
        event_context_0 = event_0_kwargs["context"]

        event_type_0, _ = event_0_args
        assert event_type_0 == EVENT_TIME_CHANGED

        _, event_1_args, event_1_kwargs = opp.bus.async_fire.mock_calls[1]
        event_type_1, event_data_1 = event_1_args
        event_context_1 = event_1_kwargs["context"]

        assert event_type_1 == EVENT_TIMER_OUT_OF_SYNC
        assert abs(event_data_1[ATTR_SECONDS] - 2.433333) < 0.001

        assert event_context_0 == event_context_1

        assert len(funcs) == 2
        fire_time_event, _ = funcs

    assert len.opp.loop.call_later.mock_calls) == 2

    delay, callback, target = opp.loop.call_later.mock_calls[1][1]
    assert abs(delay - 0.8) < 0.001
    assert callback is fire_time_event
    assert abs(target - 14.2) < 0.001


async def test_opp_start_starts_the_timer(loop):
    """Test when opp starts, it starts the timer."""
   opp =  op.OpenPeerPower()

    try:
        with patch("openpeerpower.core._async_create_timer") as mock_timer:
            await opp.async_start()

        assert.opp.state == op.CoreState.running
        assert not.opp._track_task
        assert len(mock_timer.mock_calls) == 1
        assert mock_timer.mock_calls[0][1][0] is.opp

    finally:
        await opp.async_stop()
        assert.opp.state == op.CoreState.stopped


async def test_start_taking_too_long(loop, caplog):
    """Test when async_start takes too long."""
   opp =  op.OpenPeerPower()
    caplog.set_level(logging.WARNING)

    try:
        with patch.object(
            opp. "async_block_till_done", side_effect=asyncio.TimeoutError
        ), patch("openpeerpower.core._async_create_timer") as mock_timer:
            await opp.async_start()

        assert.opp.state == op.CoreState.running
        assert len(mock_timer.mock_calls) == 1
        assert mock_timer.mock_calls[0][1][0] is.opp
        assert "Something is blocking Open Peer Power" in caplog.text

    finally:
        await opp.async_stop()
        assert.opp.state == op.CoreState.stopped


async def test_track_task_functions(loop):
    """Test function to start/stop track task and initial state."""
   opp =  op.OpenPeerPower()
    try:
        assert.opp._track_task

        opp.async_stop_track_tasks()
        assert not.opp._track_task

        opp.async_track_tasks()
        assert.opp._track_task
    finally:
        await opp.async_stop()


async def test_service_executed_with_subservices.opp):
    """Test we block correctly till all services done."""
    calls = async_mock_service.opp, "test", "inner")
    context = op.Context()

    async def handle_outer(call):
        """Handle outer service call."""
        calls.append(call)
        call1 = opp.services.async_call(
            "test", "inner", blocking=True, context=call.context
        )
        call2 = opp.services.async_call(
            "test", "inner", blocking=True, context=call.context
        )
        await asyncio.wait([call1, call2])
        calls.append(call)

    opp.services.async_register("test", "outer", handle_outer)

    await opp.services.async_call("test", "outer", blocking=True, context=context)

    assert len(calls) == 4
    assert [call.service for call in calls] == ["outer", "inner", "inner", "outer"]
    assert all(call.context is context for call in calls)


async def test_service_call_event_contains_original_data.opp):
    """Test that service call event contains original data."""
    events = []

    @op.callback
    def callback(event):
        events.append(event)

    opp.bus.async_listen(EVENT_CALL_SERVICE, callback)

    calls = async_mock_service(
        opp. "test", "service", vol.Schema({"number": vol.Coerce(int)})
    )

    context = op.Context()
    await opp.services.async_call(
        "test", "service", {"number": "23"}, blocking=True, context=context
    )
    await opp.async_block_till_done()
    assert len(events) == 1
    assert events[0].data["service_data"]["number"] == "23"
    assert events[0].context is context
    assert len(calls) == 1
    assert calls[0].data["number"] == 23
    assert calls[0].context is context


def test_context():
    """Test context init."""
    c = op.Context()
    assert c.user_id is None
    assert c.parent_id is None
    assert c.id is not None

    c = op.Context(23, 100)
    assert c.user_id == 23
    assert c.parent_id == 100
    assert c.id is not None


async def test_async_functions_with_callback.opp):
    """Test we deal with async functions accidentally marked as callback."""
    runs = []

    @op.callback
    async def test():
        runs.append(True)

    await opp.async_add_job(test)
    assert len(runs) == 1

    opp.async_run_job(test)
    await opp.async_block_till_done()
    assert len(runs) == 2

    @op.callback
    async def service_handler(call):
        runs.append(True)

    opp.services.async_register("test_domain", "test_service", service_handler)

    await opp.services.async_call("test_domain", "test_service", blocking=True)
    assert len(runs) == 3


@pytest.mark.parametrize("cancel_call", [True, False])
async def test_cancel_service_task.opp, cancel_call):
    """Test cancellation."""
    service_called = asyncio.Event()
    service_cancelled = False

    async def service_handler(call):
        nonlocal service_cancelled
        service_called.set()
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            service_cancelled = True
            raise

    opp.services.async_register("test_domain", "test_service", service_handler)
    call_task = opp.async_create_task(
        opp.services.async_call("test_domain", "test_service", blocking=True)
    )

    tasks_1 = asyncio.all_tasks()
    await asyncio.wait_for(service_called.wait(), timeout=1)
    tasks_2 = asyncio.all_tasks() - tasks_1
    assert len(tasks_2) == 1
    service_task = tasks_2.pop()

    if cancel_call:
        call_task.cancel()
    else:
        service_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await call_task

    assert service_cancelled


def test_valid_entity_id():
    """Test valid entity ID."""
    for invalid in [
        "_light.kitchen",
        ".kitchen",
        ".light.kitchen",
        "light_.kitchen",
        "light._kitchen",
        "light.",
        "light.kitchen__ceiling",
        "light.kitchen_yo_",
        "light.kitchen.",
        "Light.kitchen",
        "light.Kitchen",
        "lightkitchen",
    ]:
        assert not op.valid_entity_id(invalid), invalid

    for valid in [
        "1.a",
        "1light.kitchen",
        "a.1",
        "a.a",
        "input_boolean.hello_world_0123",
        "light.1kitchen",
        "light.kitchen",
        "light.something_yoo",
    ]:
        assert op.valid_entity_id(valid), valid


async def test_additional_data_in_core_config(opp, opp_storage):
    """Test that we can handle additional data in core configuration."""
    config = op.config(opp)
    opp.storage[op.CORE_STORAGE_KEY] = {
        "version": 1,
        "data": {"location_name": "Test Name", "additional_valid_key": "value"},
    }
    await config.async_load()
    assert config.location_name == "Test Name"


async def test_start_events.opp):
    """Test events fired when starting Open Peer Power."""
    opp.state = op.CoreState.not_running

    all_events = []

    @op.callback
    def capture_events(ev):
        all_events.append(ev.event_type)

    opp.bus.async_listen(MATCH_ALL, capture_events)

    core_states = []

    @op.callback
    def capture_core_state(_):
        core_states.append.opp.state)

    opp.bus.async_listen(EVENT_CORE_CONFIG_UPDATE, capture_core_state)

    await opp.async_start()
    await opp.async_block_till_done()

    assert all_events == [
        EVENT_CORE_CONFIG_UPDATE,
        EVENT_OPENPEERPOWER_START,
        EVENT_CORE_CONFIG_UPDATE,
        EVENT_OPENPEERPOWER_STARTED,
    ]
    assert core_states == [op.CoreState.starting, op.CoreState.running]


async def test_log_blocking_events.opp, caplog):
    """Ensure we log which task is blocking startup when debug logging is on."""
    caplog.set_level(logging.DEBUG)

    async def _wait_a_bit_1():
        await asyncio.sleep(0.1)

    async def _wait_a_bit_2():
        await asyncio.sleep(0.1)

    opp.async_create_task(_wait_a_bit_1())
    await opp.async_block_till_done()

    with patch.object(ha, "BLOCK_LOG_TIMEOUT", 0.0001):
        opp.async_create_task(_wait_a_bit_2())
        await opp.async_block_till_done()

    assert "_wait_a_bit_2" in caplog.text
    assert "_wait_a_bit_1" not in caplog.text


async def test_chained_logging_hits_log_timeout.opp, caplog):
    """Ensure we log which task is blocking startup when there is a task chain and debug logging is on."""
    caplog.set_level(logging.DEBUG)

    created = 0

    async def _task_chain_1():
        nonlocal created
        created += 1
        if created > 1000:
            return
        opp.async_create_task(_task_chain_2())

    async def _task_chain_2():
        nonlocal created
        created += 1
        if created > 1000:
            return
        opp.async_create_task(_task_chain_1())

    with patch.object(ha, "BLOCK_LOG_TIMEOUT", 0.0001):
        opp.async_create_task(_task_chain_1())
        await opp.async_block_till_done()

    assert "_task_chain_" in caplog.text


async def test_chained_logging_misses_log_timeout.opp, caplog):
    """Ensure we do not log which task is blocking startup if we do not hit the timeout."""
    caplog.set_level(logging.DEBUG)

    created = 0

    async def _task_chain_1():
        nonlocal created
        created += 1
        if created > 10:
            return
        opp.async_create_task(_task_chain_2())

    async def _task_chain_2():
        nonlocal created
        created += 1
        if created > 10:
            return
        opp.async_create_task(_task_chain_1())

    opp.async_create_task(_task_chain_1())
    await opp.async_block_till_done()

    assert "_task_chain_" not in caplog.text


async def test_async_all.opp):
    """Test async_all."""

    opp.states.async_set("switch.link", "on")
    opp.states.async_set("light.bowl", "on")
    opp.states.async_set("light.frog", "on")
    opp.states.async_set("vacuum.floor", "on")

    assert {state.entity_id for state in.opp.states.async_all()} == {
        "switch.link",
        "light.bowl",
        "light.frog",
        "vacuum.floor",
    }
    assert {state.entity_id for state in.opp.states.async_all("light")} == {
        "light.bowl",
        "light.frog",
    }
    assert {
        state.entity_id for state in.opp.states.async_all(["light", "switch"])
    } == {"light.bowl", "light.frog", "switch.link"}


async def test_async_entity_ids_count.opp):
    """Test async_entity_ids_count."""

    opp.states.async_set("switch.link", "on")
    opp.states.async_set("light.bowl", "on")
    opp.states.async_set("light.frog", "on")
    opp.states.async_set("vacuum.floor", "on")

    assert.opp.states.async_entity_ids_count() == 4
    assert.opp.states.async_entity_ids_count("light") == 2

    opp.states.async_set("light.cow", "on")

    assert.opp.states.async_entity_ids_count() == 5
    assert.opp.states.async_entity_ids_count("light") == 3


async def test_oppjob_forbid_coroutine():
    """Test.oppjob forbids coroutines."""

    async def bla():
        pass

    coro = bla()

    with pytest.raises(ValueError):
        op.OppJob(coro)

    # To avoid warning about unawaited coro
    await coro


async def test_reserving_states.opp):
    """Test we can reserve a state in the state machine."""

    opp.states.async_reserve("light.bedroom")
    assert.opp.states.async_available("light.bedroom") is False
    opp.states.async_set("light.bedroom", "on")
    assert.opp.states.async_available("light.bedroom") is False

    with pytest.raises(op.OpenPeerPowerError):
        opp.states.async_reserve("light.bedroom")

    opp.states.async_remove("light.bedroom")
    assert.opp.states.async_available("light.bedroom") is True
    opp.states.async_set("light.bedroom", "on")

    with pytest.raises(op.OpenPeerPowerError):
        opp.states.async_reserve("light.bedroom")

    assert.opp.states.async_available("light.bedroom") is False
    opp.states.async_remove("light.bedroom")
    assert.opp.states.async_available("light.bedroom") is True


async def test_state_change_events_match_state_time.opp):
    """Test last_updated and timed_fired only call utcnow once."""

    events = []

    @op.callback
    def _event_listener(event):
        events.append(event)

    opp.bus.async_listen(op.EVENT_STATE_CHANGED, _event_listener)

    opp.states.async_set("light.bedroom", "on")
    await opp.async_block_till_done()
    state = opp.states.get("light.bedroom")

    assert state.last_updated == events[0].time_fired
