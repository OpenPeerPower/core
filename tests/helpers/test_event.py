"""Test event helpers."""
# pylint: disable=protected-access
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch

from astral import Astral
import jinja2
import pytest

from openpeerpower.components import sun
from openpeerpower.const import MATCH_ALL
import openpeerpower.core as ha
from openpeerpower.core import callback
from openpeerpower.exceptions import TemplateError
from openpeerpower.helpers.entity_registry import EVENT_ENTITY_REGISTRY_UPDATED
from openpeerpower.helpers.event import (
    TrackStates,
    TrackTemplate,
    TrackTemplateResult,
    async_call_later,
    async_track_point_in_time,
    async_track_point_in_utc_time,
    async_track_same_state,
    async_track_state_added_domain,
    async_track_state_change,
    async_track_state_change_event,
    async_track_state_change_filtered,
    async_track_state_removed_domain,
    async_track_sunrise,
    async_track_sunset,
    async_track_template,
    async_track_template_result,
    async_track_time_change,
    async_track_time_interval,
    async_track_utc_time_change,
    track_point_in_utc_time,
)
from openpeerpower.helpers.template import Template
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util

from tests.common import async_fire_time_changed

DEFAULT_TIME_ZONE = dt_util.DEFAULT_TIME_ZONE


def teardown():
    """Stop everything that was started."""
    dt_util.set_default_time_zone(DEFAULT_TIME_ZONE)


async def test_track_point_in_time.opp):
    """Test track point in time."""
    before_birthday = datetime(1985, 7, 9, 12, 0, 0, tzinfo=dt_util.UTC)
    birthday_paulus = datetime(1986, 7, 9, 12, 0, 0, tzinfo=dt_util.UTC)
    after_birthday = datetime(1987, 7, 9, 12, 0, 0, tzinfo=dt_util.UTC)

    runs = []

    async_track_point_in_utc_time(
       .opp, callback(lambda x: runs.append(x)), birthday_paulus
    )

    async_fire_time_changed.opp, before_birthday)
    await.opp.async_block_till_done()
    assert len(runs) == 0

    async_fire_time_changed.opp, birthday_paulus)
    await.opp.async_block_till_done()
    assert len(runs) == 1

    # A point in time tracker will only fire once, this should do nothing
    async_fire_time_changed.opp, birthday_paulus)
    await.opp.async_block_till_done()
    assert len(runs) == 1

    async_track_point_in_utc_time(
       .opp, callback(lambda x: runs.append(x)), birthday_paulus
    )

    async_fire_time_changed.opp, after_birthday)
    await.opp.async_block_till_done()
    assert len(runs) == 2

    unsub = async_track_point_in_time(
       .opp, callback(lambda x: runs.append(x)), birthday_paulus
    )
    unsub()

    async_fire_time_changed.opp, after_birthday)
    await.opp.async_block_till_done()
    assert len(runs) == 2


async def test_track_point_in_time_drift_rearm.opp):
    """Test tasks with the time rolling backwards."""
    specific_runs = []

    now = dt_util.utcnow()

    time_that_will_not_match_right_away = datetime(
        now.year + 1, 5, 24, 21, 59, 55, tzinfo=dt_util.UTC
    )

    async_track_point_in_utc_time(
       .opp,
        callback(lambda x: specific_runs.append(x)),
        time_that_will_not_match_right_away,
    )

    async_fire_time_changed(
       .opp,
        datetime(now.year + 1, 5, 24, 21, 59, 00, tzinfo=dt_util.UTC),
        fire_all=True,
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 0

    async_fire_time_changed(
       .opp,
        datetime(now.year + 1, 5, 24, 21, 59, 55, tzinfo=dt_util.UTC),
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1


async def test_track_state_change_from_to_state_match.opp):
    """Test track_state_change with from and to state matchers."""
    from_and_to_state_runs = []
    only_from_runs = []
    only_to_runs = []
    match_all_runs = []
    no_to_from_specified_runs = []

    def from_and_to_state_callback(entity_id, old_state, new_state):
        from_and_to_state_runs.append(1)

    def only_from_state_callback(entity_id, old_state, new_state):
        only_from_runs.append(1)

    def only_to_state_callback(entity_id, old_state, new_state):
        only_to_runs.append(1)

    def match_all_callback(entity_id, old_state, new_state):
        match_all_runs.append(1)

    def no_to_from_specified_callback(entity_id, old_state, new_state):
        no_to_from_specified_runs.append(1)

    async_track_state_change(
       .opp, "light.Bowl", from_and_to_state_callback, "on", "off"
    )
    async_track_state_change.opp, "light.Bowl", only_from_state_callback, "on", None)
    async_track_state_change(
       .opp, "light.Bowl", only_to_state_callback, None, ["off", "standby"]
    )
    async_track_state_change(
       .opp, "light.Bowl", match_all_callback, MATCH_ALL, MATCH_ALL
    )
    async_track_state_change.opp, "light.Bowl", no_to_from_specified_callback)

   .opp.states.async_set("light.Bowl", "on")
    await.opp.async_block_till_done()
    assert len(from_and_to_state_runs) == 0
    assert len(only_from_runs) == 0
    assert len(only_to_runs) == 0
    assert len(match_all_runs) == 1
    assert len(no_to_from_specified_runs) == 1

   .opp.states.async_set("light.Bowl", "off")
    await.opp.async_block_till_done()
    assert len(from_and_to_state_runs) == 1
    assert len(only_from_runs) == 1
    assert len(only_to_runs) == 1
    assert len(match_all_runs) == 2
    assert len(no_to_from_specified_runs) == 2

   .opp.states.async_set("light.Bowl", "on")
    await.opp.async_block_till_done()
    assert len(from_and_to_state_runs) == 1
    assert len(only_from_runs) == 1
    assert len(only_to_runs) == 1
    assert len(match_all_runs) == 3
    assert len(no_to_from_specified_runs) == 3

   .opp.states.async_set("light.Bowl", "on")
    await.opp.async_block_till_done()
    assert len(from_and_to_state_runs) == 1
    assert len(only_from_runs) == 1
    assert len(only_to_runs) == 1
    assert len(match_all_runs) == 3
    assert len(no_to_from_specified_runs) == 3

   .opp.states.async_set("light.Bowl", "off")
    await.opp.async_block_till_done()
    assert len(from_and_to_state_runs) == 2
    assert len(only_from_runs) == 2
    assert len(only_to_runs) == 2
    assert len(match_all_runs) == 4
    assert len(no_to_from_specified_runs) == 4

   .opp.states.async_set("light.Bowl", "off")
    await.opp.async_block_till_done()
    assert len(from_and_to_state_runs) == 2
    assert len(only_from_runs) == 2
    assert len(only_to_runs) == 2
    assert len(match_all_runs) == 4
    assert len(no_to_from_specified_runs) == 4


async def test_track_state_change.opp):
    """Test track_state_change."""
    # 2 lists to track how often our callbacks get called
    specific_runs = []
    wildcard_runs = []
    wildercard_runs = []

    def specific_run_callback(entity_id, old_state, new_state):
        specific_runs.append(1)

    # This is the rare use case
    async_track_state_change.opp, "light.Bowl", specific_run_callback, "on", "off")

    @ha.callback
    def wildcard_run_callback(entity_id, old_state, new_state):
        wildcard_runs.append((old_state, new_state))

    # This is the most common use case
    async_track_state_change.opp, "light.Bowl", wildcard_run_callback)

    async def wildercard_run_callback(entity_id, old_state, new_state):
        wildercard_runs.append((old_state, new_state))

    async_track_state_change.opp, MATCH_ALL, wildercard_run_callback)

    # Adding state to state machine
   .opp.states.async_set("light.Bowl", "on")
    await.opp.async_block_till_done()
    assert len(specific_runs) == 0
    assert len(wildcard_runs) == 1
    assert len(wildercard_runs) == 1
    assert wildcard_runs[-1][0] is None
    assert wildcard_runs[-1][1] is not None

    # Set same state should not trigger a state change/listener
   .opp.states.async_set("light.Bowl", "on")
    await.opp.async_block_till_done()
    assert len(specific_runs) == 0
    assert len(wildcard_runs) == 1
    assert len(wildercard_runs) == 1

    # State change off -> on
   .opp.states.async_set("light.Bowl", "off")
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1
    assert len(wildcard_runs) == 2
    assert len(wildercard_runs) == 2

    # State change off -> off
   .opp.states.async_set("light.Bowl", "off", {"some_attr": 1})
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1
    assert len(wildcard_runs) == 3
    assert len(wildercard_runs) == 3

    # State change off -> on
   .opp.states.async_set("light.Bowl", "on")
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1
    assert len(wildcard_runs) == 4
    assert len(wildercard_runs) == 4

   .opp.states.async_remove("light.bowl")
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1
    assert len(wildcard_runs) == 5
    assert len(wildercard_runs) == 5
    assert wildcard_runs[-1][0] is not None
    assert wildcard_runs[-1][1] is None
    assert wildercard_runs[-1][0] is not None
    assert wildercard_runs[-1][1] is None

    # Set state for different entity id
   .opp.states.async_set("switch.kitchen", "on")
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1
    assert len(wildcard_runs) == 5
    assert len(wildercard_runs) == 6


async def test_async_track_state_change_filtered.opp):
    """Test async_track_state_change_filtered."""
    single_entity_id_tracker = []
    multiple_entity_id_tracker = []

    @ha.callback
    def single_run_callback(event):
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        single_entity_id_tracker.append((old_state, new_state))

    @ha.callback
    def multiple_run_callback(event):
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        multiple_entity_id_tracker.append((old_state, new_state))

    @ha.callback
    def callback_that_throws(event):
        raise ValueError

    track_single = async_track_state_change_filtered(
       .opp, TrackStates(False, {"light.bowl"}, None), single_run_callback
    )
    assert track_single.listeners == {
        "all": False,
        "domains": None,
        "entities": {"light.bowl"},
    }

    track_multi = async_track_state_change_filtered(
       .opp, TrackStates(False, {"light.bowl"}, {"switch"}), multiple_run_callback
    )
    assert track_multi.listeners == {
        "all": False,
        "domains": {"switch"},
        "entities": {"light.bowl"},
    }

    track_throws = async_track_state_change_filtered(
       .opp, TrackStates(False, {"light.bowl"}, {"switch"}), callback_that_throws
    )
    assert track_throws.listeners == {
        "all": False,
        "domains": {"switch"},
        "entities": {"light.bowl"},
    }

    # Adding state to state machine
   .opp.states.async_set("light.Bowl", "on")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 1
    assert single_entity_id_tracker[-1][0] is None
    assert single_entity_id_tracker[-1][1] is not None
    assert len(multiple_entity_id_tracker) == 1
    assert multiple_entity_id_tracker[-1][0] is None
    assert multiple_entity_id_tracker[-1][1] is not None

    # Set same state should not trigger a state change/listener
   .opp.states.async_set("light.Bowl", "on")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 1
    assert len(multiple_entity_id_tracker) == 1

    # State change off -> on
   .opp.states.async_set("light.Bowl", "off")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 2
    assert len(multiple_entity_id_tracker) == 2

    # State change off -> off
   .opp.states.async_set("light.Bowl", "off", {"some_attr": 1})
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 3
    assert len(multiple_entity_id_tracker) == 3

    # State change off -> on
   .opp.states.async_set("light.Bowl", "on")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 4
    assert len(multiple_entity_id_tracker) == 4

   .opp.states.async_remove("light.bowl")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 5
    assert single_entity_id_tracker[-1][0] is not None
    assert single_entity_id_tracker[-1][1] is None
    assert len(multiple_entity_id_tracker) == 5
    assert multiple_entity_id_tracker[-1][0] is not None
    assert multiple_entity_id_tracker[-1][1] is None

    # Set state for different entity id
   .opp.states.async_set("switch.kitchen", "on")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 5
    assert len(multiple_entity_id_tracker) == 6

    track_single.async_remove()
    # Ensure unsubing the listener works
   .opp.states.async_set("light.Bowl", "off")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 5
    assert len(multiple_entity_id_tracker) == 7

    assert track_multi.listeners == {
        "all": False,
        "domains": {"switch"},
        "entities": {"light.bowl"},
    }
    track_multi.async_update_listeners(TrackStates(False, {"light.bowl"}, None))
    assert track_multi.listeners == {
        "all": False,
        "domains": None,
        "entities": {"light.bowl"},
    }
   .opp.states.async_set("light.Bowl", "on")
    await.opp.async_block_till_done()
    assert len(multiple_entity_id_tracker) == 8
   .opp.states.async_set("switch.kitchen", "off")
    await.opp.async_block_till_done()
    assert len(multiple_entity_id_tracker) == 8

    track_multi.async_update_listeners(TrackStates(True, None, None))
   .opp.states.async_set("switch.kitchen", "off")
    await.opp.async_block_till_done()
    assert len(multiple_entity_id_tracker) == 8
   .opp.states.async_set("switch.any", "off")
    await.opp.async_block_till_done()
    assert len(multiple_entity_id_tracker) == 9

    track_multi.async_remove()
    track_throws.async_remove()


async def test_async_track_state_change_event.opp):
    """Test async_track_state_change_event."""
    single_entity_id_tracker = []
    multiple_entity_id_tracker = []

    @ha.callback
    def single_run_callback(event):
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        single_entity_id_tracker.append((old_state, new_state))

    @ha.callback
    def multiple_run_callback(event):
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        multiple_entity_id_tracker.append((old_state, new_state))

    @ha.callback
    def callback_that_throws(event):
        raise ValueError

    unsub_single = async_track_state_change_event(
       .opp, ["light.Bowl"], single_run_callback
    )
    unsub_multi = async_track_state_change_event(
       .opp, ["light.Bowl", "switch.kitchen"], multiple_run_callback
    )
    unsub_throws = async_track_state_change_event(
       .opp, ["light.Bowl", "switch.kitchen"], callback_that_throws
    )

    # Adding state to state machine
   .opp.states.async_set("light.Bowl", "on")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 1
    assert single_entity_id_tracker[-1][0] is None
    assert single_entity_id_tracker[-1][1] is not None
    assert len(multiple_entity_id_tracker) == 1
    assert multiple_entity_id_tracker[-1][0] is None
    assert multiple_entity_id_tracker[-1][1] is not None

    # Set same state should not trigger a state change/listener
   .opp.states.async_set("light.Bowl", "on")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 1
    assert len(multiple_entity_id_tracker) == 1

    # State change off -> on
   .opp.states.async_set("light.Bowl", "off")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 2
    assert len(multiple_entity_id_tracker) == 2

    # State change off -> off
   .opp.states.async_set("light.Bowl", "off", {"some_attr": 1})
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 3
    assert len(multiple_entity_id_tracker) == 3

    # State change off -> on
   .opp.states.async_set("light.Bowl", "on")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 4
    assert len(multiple_entity_id_tracker) == 4

   .opp.states.async_remove("light.bowl")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 5
    assert single_entity_id_tracker[-1][0] is not None
    assert single_entity_id_tracker[-1][1] is None
    assert len(multiple_entity_id_tracker) == 5
    assert multiple_entity_id_tracker[-1][0] is not None
    assert multiple_entity_id_tracker[-1][1] is None

    # Set state for different entity id
   .opp.states.async_set("switch.kitchen", "on")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 5
    assert len(multiple_entity_id_tracker) == 6

    unsub_single()
    # Ensure unsubing the listener works
   .opp.states.async_set("light.Bowl", "off")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 5
    assert len(multiple_entity_id_tracker) == 7

    unsub_multi()
    unsub_throws()


async def test_async_track_state_change_event_with_empty_list.opp):
    """Test async_track_state_change_event passing an empty list of entities."""
    unsub_single = async_track_state_change_event(
       .opp, [], ha.callback(lambda event: None)
    )
    unsub_single2 = async_track_state_change_event(
       .opp, [], ha.callback(lambda event: None)
    )

    unsub_single2()
    unsub_single()


async def test_async_track_state_added_domain.opp):
    """Test async_track_state_added_domain."""
    single_entity_id_tracker = []
    multiple_entity_id_tracker = []

    @ha.callback
    def single_run_callback(event):
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        single_entity_id_tracker.append((old_state, new_state))

    @ha.callback
    def multiple_run_callback(event):
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        multiple_entity_id_tracker.append((old_state, new_state))

    @ha.callback
    def callback_that_throws(event):
        raise ValueError

    unsub_single = async_track_state_added_domain.opp, "light", single_run_callback)
    unsub_multi = async_track_state_added_domain(
       .opp, ["light", "switch"], multiple_run_callback
    )
    unsub_throws = async_track_state_added_domain(
       .opp, ["light", "switch"], callback_that_throws
    )

    # Adding state to state machine
   .opp.states.async_set("light.Bowl", "on")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 1
    assert single_entity_id_tracker[-1][0] is None
    assert single_entity_id_tracker[-1][1] is not None
    assert len(multiple_entity_id_tracker) == 1
    assert multiple_entity_id_tracker[-1][0] is None
    assert multiple_entity_id_tracker[-1][1] is not None

    # Set same state should not trigger a state change/listener
   .opp.states.async_set("light.Bowl", "on")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 1
    assert len(multiple_entity_id_tracker) == 1

    # State change off -> on - nothing added so no trigger
   .opp.states.async_set("light.Bowl", "off")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 1
    assert len(multiple_entity_id_tracker) == 1

    # State change off -> off - nothing added so no trigger
   .opp.states.async_set("light.Bowl", "off", {"some_attr": 1})
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 1
    assert len(multiple_entity_id_tracker) == 1

    # Removing state does not trigger
   .opp.states.async_remove("light.bowl")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 1
    assert len(multiple_entity_id_tracker) == 1

    # Set state for different entity id
   .opp.states.async_set("switch.kitchen", "on")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 1
    assert len(multiple_entity_id_tracker) == 2

    unsub_single()
    # Ensure unsubing the listener works
   .opp.states.async_set("light.new", "off")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 1
    assert len(multiple_entity_id_tracker) == 3

    unsub_multi()
    unsub_throws()


async def test_async_track_state_added_domain_with_empty_list.opp):
    """Test async_track_state_added_domain passing an empty list of domains."""
    unsub_single = async_track_state_added_domain(
       .opp, [], ha.callback(lambda event: None)
    )
    unsub_single2 = async_track_state_added_domain(
       .opp, [], ha.callback(lambda event: None)
    )

    unsub_single2()
    unsub_single()


async def test_async_track_state_removed_domain_with_empty_list.opp):
    """Test async_track_state_removed_domain passing an empty list of domains."""
    unsub_single = async_track_state_removed_domain(
       .opp, [], ha.callback(lambda event: None)
    )
    unsub_single2 = async_track_state_removed_domain(
       .opp, [], ha.callback(lambda event: None)
    )

    unsub_single2()
    unsub_single()


async def test_async_track_state_removed_domain.opp):
    """Test async_track_state_removed_domain."""
    single_entity_id_tracker = []
    multiple_entity_id_tracker = []

    @ha.callback
    def single_run_callback(event):
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        single_entity_id_tracker.append((old_state, new_state))

    @ha.callback
    def multiple_run_callback(event):
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        multiple_entity_id_tracker.append((old_state, new_state))

    @ha.callback
    def callback_that_throws(event):
        raise ValueError

    unsub_single = async_track_state_removed_domain.opp, "light", single_run_callback)
    unsub_multi = async_track_state_removed_domain(
       .opp, ["light", "switch"], multiple_run_callback
    )
    unsub_throws = async_track_state_removed_domain(
       .opp, ["light", "switch"], callback_that_throws
    )

    # Adding state to state machine
   .opp.states.async_set("light.Bowl", "on")
   .opp.states.async_remove("light.Bowl")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 1
    assert single_entity_id_tracker[-1][1] is None
    assert single_entity_id_tracker[-1][0] is not None
    assert len(multiple_entity_id_tracker) == 1
    assert multiple_entity_id_tracker[-1][1] is None
    assert multiple_entity_id_tracker[-1][0] is not None

    # Added and than removed (light)
   .opp.states.async_set("light.Bowl", "on")
   .opp.states.async_remove("light.Bowl")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 2
    assert len(multiple_entity_id_tracker) == 2

    # Added and than removed (light)
   .opp.states.async_set("light.Bowl", "off")
   .opp.states.async_remove("light.Bowl")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 3
    assert len(multiple_entity_id_tracker) == 3

    # Added and than removed (light)
   .opp.states.async_set("light.Bowl", "off", {"some_attr": 1})
   .opp.states.async_remove("light.Bowl")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 4
    assert len(multiple_entity_id_tracker) == 4

    # Added and than removed (switch)
   .opp.states.async_set("switch.kitchen", "on")
   .opp.states.async_remove("switch.kitchen")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 4
    assert len(multiple_entity_id_tracker) == 5

    unsub_single()
    # Ensure unsubing the listener works
   .opp.states.async_set("light.new", "off")
   .opp.states.async_remove("light.new")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 4
    assert len(multiple_entity_id_tracker) == 6

    unsub_multi()
    unsub_throws()


async def test_async_track_state_removed_domain_match_all.opp):
    """Test async_track_state_removed_domain with a match_all."""
    single_entity_id_tracker = []
    match_all_entity_id_tracker = []

    @ha.callback
    def single_run_callback(event):
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        single_entity_id_tracker.append((old_state, new_state))

    @ha.callback
    def match_all_run_callback(event):
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        match_all_entity_id_tracker.append((old_state, new_state))

    unsub_single = async_track_state_removed_domain.opp, "light", single_run_callback)
    unsub_match_all = async_track_state_removed_domain(
       .opp, MATCH_ALL, match_all_run_callback
    )
   .opp.states.async_set("light.new", "off")
   .opp.states.async_remove("light.new")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 1
    assert len(match_all_entity_id_tracker) == 1

   .opp.states.async_set("switch.new", "off")
   .opp.states.async_remove("switch.new")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 1
    assert len(match_all_entity_id_tracker) == 2

    unsub_match_all()
    unsub_single()
   .opp.states.async_set("switch.new", "off")
   .opp.states.async_remove("switch.new")
    await.opp.async_block_till_done()
    assert len(single_entity_id_tracker) == 1
    assert len(match_all_entity_id_tracker) == 2


async def test_track_template.opp):
    """Test tracking template."""
    specific_runs = []
    wildcard_runs = []
    wildercard_runs = []

    template_condition = Template("{{states.switch.test.state == 'on'}}",.opp)
    template_condition_var = Template(
        "{{states.switch.test.state == 'on' and test == 5}}",.opp
    )

   .opp.states.async_set("switch.test", "off")

    def specific_run_callback(entity_id, old_state, new_state):
        specific_runs.append(1)

    async_track_template.opp, template_condition, specific_run_callback)

    @ha.callback
    def wildcard_run_callback(entity_id, old_state, new_state):
        wildcard_runs.append((old_state, new_state))

    async_track_template.opp, template_condition, wildcard_run_callback)

    async def wildercard_run_callback(entity_id, old_state, new_state):
        wildercard_runs.append((old_state, new_state))

    async_track_template(
       .opp, template_condition_var, wildercard_run_callback, {"test": 5}
    )

   .opp.states.async_set("switch.test", "on")
    await.opp.async_block_till_done()

    assert len(specific_runs) == 1
    assert len(wildcard_runs) == 1
    assert len(wildercard_runs) == 1

   .opp.states.async_set("switch.test", "on")
    await.opp.async_block_till_done()

    assert len(specific_runs) == 1
    assert len(wildcard_runs) == 1
    assert len(wildercard_runs) == 1

   .opp.states.async_set("switch.test", "off")
    await.opp.async_block_till_done()

    assert len(specific_runs) == 1
    assert len(wildcard_runs) == 1
    assert len(wildercard_runs) == 1

   .opp.states.async_set("switch.test", "off")
    await.opp.async_block_till_done()

    assert len(specific_runs) == 1
    assert len(wildcard_runs) == 1
    assert len(wildercard_runs) == 1

   .opp.states.async_set("switch.test", "on")
    await.opp.async_block_till_done()

    assert len(specific_runs) == 2
    assert len(wildcard_runs) == 2
    assert len(wildercard_runs) == 2

    template_iterate = Template("{{ (states.switch | length) > 0 }}",.opp)
    iterate_calls = []

    @ha.callback
    def iterate_callback(entity_id, old_state, new_state):
        iterate_calls.append((entity_id, old_state, new_state))

    async_track_template.opp, template_iterate, iterate_callback)
    await.opp.async_block_till_done()

   .opp.states.async_set("switch.new", "on")
    await.opp.async_block_till_done()

    assert len(iterate_calls) == 1
    assert iterate_calls[0][0] == "switch.new"
    assert iterate_calls[0][1] is None
    assert iterate_calls[0][2].state == "on"


async def test_track_template_error.opp, caplog):
    """Test tracking template with error."""
    template_error = Template("{{ (states.switch | lunch) > 0 }}",.opp)
    error_calls = []

    @ha.callback
    def error_callback(entity_id, old_state, new_state):
        error_calls.append((entity_id, old_state, new_state))

    async_track_template.opp, template_error, error_callback)
    await.opp.async_block_till_done()

   .opp.states.async_set("switch.new", "on")
    await.opp.async_block_till_done()

    assert not error_calls
    assert "lunch" in caplog.text
    assert "TemplateAssertionError" in caplog.text

    caplog.clear()

    with patch.object(Template, "async_render") as render:
        render.return_value = "ok"

       .opp.states.async_set("switch.not_exist", "off")
        await.opp.async_block_till_done()

    assert "no filter named 'lunch'" not in caplog.text
    assert "TemplateAssertionError" not in caplog.text


async def test_track_template_error_can_recover.opp, caplog):
    """Test tracking template with error."""
   .opp.states.async_set("switch.data_system", "cow", {"opmode": 0})
    template_error = Template(
        "{{ states.sensor.data_system.attributes['opmode'] == '0' }}",.opp
    )
    error_calls = []

    @ha.callback
    def error_callback(entity_id, old_state, new_state):
        error_calls.append((entity_id, old_state, new_state))

    async_track_template.opp, template_error, error_callback)
    await.opp.async_block_till_done()
    assert not error_calls

   .opp.states.async_remove("switch.data_system")

    assert "UndefinedError" in caplog.text

   .opp.states.async_set("switch.data_system", "cow", {"opmode": 0})

    caplog.clear()

    assert "UndefinedError" not in caplog.text


async def test_track_template_time_change.opp, caplog):
    """Test tracking template with time change."""
    template_error = Template("{{ utcnow().minute % 2 == 0 }}",.opp)
    calls = []

    @ha.callback
    def error_callback(entity_id, old_state, new_state):
        calls.append((entity_id, old_state, new_state))

    start_time = dt_util.utcnow() + timedelta(hours=24)
    time_that_will_not_match_right_away = start_time.replace(minute=1, second=0)
    with patch(
        "openpeerpower.util.dt.utcnow", return_value=time_that_will_not_match_right_away
    ):
        async_track_template.opp, template_error, error_callback)
        await.opp.async_block_till_done()
        assert not calls

    first_time = start_time.replace(minute=2, second=0)
    with patch("openpeerpower.util.dt.utcnow", return_value=first_time):
        async_fire_time_changed.opp, first_time)
        await.opp.async_block_till_done()

    assert len(calls) == 1
    assert calls[0] == (None, None, None)


async def test_track_template_result.opp):
    """Test tracking template."""
    specific_runs = []
    wildcard_runs = []
    wildercard_runs = []

    template_condition = Template("{{states.sensor.test.state}}",.opp)
    template_condition_var = Template(
        "{{(states.sensor.test.state|int) + test }}",.opp
    )

    def specific_run_callback(event, updates):
        track_result = updates.pop()
        specific_runs.append(int(track_result.result))

    async_track_template_result(
       .opp, [TrackTemplate(template_condition, None)], specific_run_callback
    )

    @ha.callback
    def wildcard_run_callback(event, updates):
        track_result = updates.pop()
        wildcard_runs.append(
            (int(track_result.last_result or 0), int(track_result.result))
        )

    async_track_template_result(
       .opp, [TrackTemplate(template_condition, None)], wildcard_run_callback
    )

    async def wildercard_run_callback(event, updates):
        track_result = updates.pop()
        wildercard_runs.append(
            (int(track_result.last_result or 0), int(track_result.result))
        )

    async_track_template_result(
       .opp,
        [TrackTemplate(template_condition_var, {"test": 5})],
        wildercard_run_callback,
    )
    await.opp.async_block_till_done()

   .opp.states.async_set("sensor.test", 5)
    await.opp.async_block_till_done()

    assert specific_runs == [5]
    assert wildcard_runs == [(0, 5)]
    assert wildercard_runs == [(0, 10)]

   .opp.states.async_set("sensor.test", 30)
    await.opp.async_block_till_done()

    assert specific_runs == [5, 30]
    assert wildcard_runs == [(0, 5), (5, 30)]
    assert wildercard_runs == [(0, 10), (10, 35)]

   .opp.states.async_set("sensor.test", 30)
    await.opp.async_block_till_done()

    assert len(specific_runs) == 2
    assert len(wildcard_runs) == 2
    assert len(wildercard_runs) == 2

   .opp.states.async_set("sensor.test", 5)
    await.opp.async_block_till_done()

    assert len(specific_runs) == 3
    assert len(wildcard_runs) == 3
    assert len(wildercard_runs) == 3

   .opp.states.async_set("sensor.test", 5)
    await.opp.async_block_till_done()

    assert len(specific_runs) == 3
    assert len(wildcard_runs) == 3
    assert len(wildercard_runs) == 3

   .opp.states.async_set("sensor.test", 20)
    await.opp.async_block_till_done()

    assert len(specific_runs) == 4
    assert len(wildcard_runs) == 4
    assert len(wildercard_runs) == 4


async def test_track_template_result_complex.opp):
    """Test tracking template."""
    specific_runs = []
    template_complex_str = """
{% if states("sensor.domain") == "light" %}
  {{ states.light | map(attribute='entity_id') | list }}
{% elif states("sensor.domain") == "lock" %}
  {{ states.lock | map(attribute='entity_id') | list }}
{% elif states("sensor.domain") == "single_binary_sensor" %}
  {{ states("binary_sensor.single") }}
{% else %}
  {{ states | map(attribute='entity_id') | list }}
{% endif %}

"""
    template_complex = Template(template_complex_str,.opp)

    def specific_run_callback(event, updates):
        specific_runs.append(updates.pop().result)

   .opp.states.async_set("light.one", "on")
   .opp.states.async_set("lock.one", "locked")

    info = async_track_template_result(
       .opp,
        [TrackTemplate(template_complex, None, timedelta(seconds=0))],
        specific_run_callback,
    )
    await.opp.async_block_till_done()

    assert info.listeners == {
        "all": True,
        "domains": set(),
        "entities": set(),
        "time": False,
    }

   .opp.states.async_set("sensor.domain", "light")
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1
    assert specific_runs[0] == ["light.one"]

    assert info.listeners == {
        "all": False,
        "domains": {"light"},
        "entities": {"sensor.domain"},
        "time": False,
    }

   .opp.states.async_set("sensor.domain", "lock")
    await.opp.async_block_till_done()
    assert len(specific_runs) == 2
    assert specific_runs[1] == ["lock.one"]
    assert info.listeners == {
        "all": False,
        "domains": {"lock"},
        "entities": {"sensor.domain"},
        "time": False,
    }

   .opp.states.async_set("sensor.domain", "all")
    await.opp.async_block_till_done()
    assert len(specific_runs) == 3
    assert "light.one" in specific_runs[2]
    assert "lock.one" in specific_runs[2]
    assert "sensor.domain" in specific_runs[2]
    assert info.listeners == {
        "all": True,
        "domains": set(),
        "entities": set(),
        "time": False,
    }

   .opp.states.async_set("sensor.domain", "light")
    await.opp.async_block_till_done()
    assert len(specific_runs) == 4
    assert specific_runs[3] == ["light.one"]
    assert info.listeners == {
        "all": False,
        "domains": {"light"},
        "entities": {"sensor.domain"},
        "time": False,
    }

   .opp.states.async_set("light.two", "on")
    await.opp.async_block_till_done()
    assert len(specific_runs) == 5
    assert "light.one" in specific_runs[4]
    assert "light.two" in specific_runs[4]
    assert "sensor.domain" not in specific_runs[4]
    assert info.listeners == {
        "all": False,
        "domains": {"light"},
        "entities": {"sensor.domain"},
        "time": False,
    }

   .opp.states.async_set("light.three", "on")
    await.opp.async_block_till_done()
    assert len(specific_runs) == 6
    assert "light.one" in specific_runs[5]
    assert "light.two" in specific_runs[5]
    assert "light.three" in specific_runs[5]
    assert "sensor.domain" not in specific_runs[5]
    assert info.listeners == {
        "all": False,
        "domains": {"light"},
        "entities": {"sensor.domain"},
        "time": False,
    }

   .opp.states.async_set("sensor.domain", "lock")
    await.opp.async_block_till_done()
    assert len(specific_runs) == 7
    assert specific_runs[6] == ["lock.one"]
    assert info.listeners == {
        "all": False,
        "domains": {"lock"},
        "entities": {"sensor.domain"},
        "time": False,
    }

   .opp.states.async_set("sensor.domain", "single_binary_sensor")
    await.opp.async_block_till_done()
    assert len(specific_runs) == 8
    assert specific_runs[7] == "unknown"
    assert info.listeners == {
        "all": False,
        "domains": set(),
        "entities": {"binary_sensor.single", "sensor.domain"},
        "time": False,
    }

   .opp.states.async_set("binary_sensor.single", "binary_sensor_on")
    await.opp.async_block_till_done()
    assert len(specific_runs) == 9
    assert specific_runs[8] == "binary_sensor_on"
    assert info.listeners == {
        "all": False,
        "domains": set(),
        "entities": {"binary_sensor.single", "sensor.domain"},
        "time": False,
    }

   .opp.states.async_set("sensor.domain", "lock")
    await.opp.async_block_till_done()
    assert len(specific_runs) == 10
    assert specific_runs[9] == ["lock.one"]
    assert info.listeners == {
        "all": False,
        "domains": {"lock"},
        "entities": {"sensor.domain"},
        "time": False,
    }


async def test_track_template_result_with_wildcard.opp):
    """Test tracking template with a wildcard."""
    specific_runs = []
    template_complex_str = r"""

{% for state in states %}
  {% if state.entity_id | regex_match('.*\.office_') %}
    {{ state.entity_id }}={{ state.state }}
  {% endif %}
{% endfor %}

"""
    template_complex = Template(template_complex_str,.opp)

    def specific_run_callback(event, updates):
        specific_runs.append(updates.pop().result)

   .opp.states.async_set("cover.office_drapes", "closed")
   .opp.states.async_set("cover.office_window", "closed")
   .opp.states.async_set("cover.office_skylight", "open")

    info = async_track_template_result(
       .opp, [TrackTemplate(template_complex, None)], specific_run_callback
    )
    await.opp.async_block_till_done()

   .opp.states.async_set("cover.office_window", "open")
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1
    assert info.listeners == {
        "all": True,
        "domains": set(),
        "entities": set(),
        "time": False,
    }

    assert "cover.office_drapes=closed" in specific_runs[0]
    assert "cover.office_window=open" in specific_runs[0]
    assert "cover.office_skylight=open" in specific_runs[0]


async def test_track_template_result_with_group.opp):
    """Test tracking template with a group."""
   .opp.states.async_set("sensor.power_1", 0)
   .opp.states.async_set("sensor.power_2", 200.2)
   .opp.states.async_set("sensor.power_3", 400.4)
   .opp.states.async_set("sensor.power_4", 800.8)

    assert await async_setup_component(
       .opp,
        "group",
        {"group": {"power_sensors": "sensor.power_1,sensor.power_2,sensor.power_3"}},
    )
    await.opp.async_block_till_done()

    assert.opp.states.get("group.power_sensors")
    assert.opp.states.get("group.power_sensors").state

    specific_runs = []
    template_complex_str = r"""

{{ states.group.power_sensors.attributes.entity_id | expand | map(attribute='state')|map('float')|sum  }}

"""
    template_complex = Template(template_complex_str,.opp)

    def specific_run_callback(event, updates):
        specific_runs.append(updates.pop().result)

    info = async_track_template_result(
       .opp, [TrackTemplate(template_complex, None)], specific_run_callback
    )
    await.opp.async_block_till_done()

    assert info.listeners == {
        "all": False,
        "domains": set(),
        "entities": {
            "group.power_sensors",
            "sensor.power_1",
            "sensor.power_2",
            "sensor.power_3",
        },
        "time": False,
    }

   .opp.states.async_set("sensor.power_1", 100.1)
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1

    assert specific_runs[0] == 100.1 + 200.2 + 400.4

   .opp.states.async_set("sensor.power_3", 0)
    await.opp.async_block_till_done()
    assert len(specific_runs) == 2

    assert specific_runs[1] == 100.1 + 200.2 + 0

    with patch(
        "openpeerpower.config.load_yaml_config_file",
        return_value={
            "group": {
                "power_sensors": "sensor.power_1,sensor.power_2,sensor.power_3,sensor.power_4",
            }
        },
    ):
        await.opp.services.async_call("group", "reload")
        await.opp.async_block_till_done()

    info.async_refresh()
    await.opp.async_block_till_done()
    assert specific_runs[-1] == 100.1 + 200.2 + 0 + 800.8


async def test_track_template_result_and_conditional.opp):
    """Test tracking template with an and conditional."""
    specific_runs = []
   .opp.states.async_set("light.a", "off")
   .opp.states.async_set("light.b", "off")
    template_str = '{% if states.light.a.state == "on" and states.light.b.state == "on" %}on{% else %}off{% endif %}'

    template = Template(template_str,.opp)

    def specific_run_callback(event, updates):
        specific_runs.append(updates.pop().result)

    info = async_track_template_result(
       .opp, [TrackTemplate(template, None)], specific_run_callback
    )
    await.opp.async_block_till_done()
    assert info.listeners == {
        "all": False,
        "domains": set(),
        "entities": {"light.a"},
        "time": False,
    }

   .opp.states.async_set("light.b", "on")
    await.opp.async_block_till_done()
    assert len(specific_runs) == 0

   .opp.states.async_set("light.a", "on")
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1
    assert specific_runs[0] == "on"
    assert info.listeners == {
        "all": False,
        "domains": set(),
        "entities": {"light.a", "light.b"},
        "time": False,
    }

   .opp.states.async_set("light.b", "off")
    await.opp.async_block_till_done()
    assert len(specific_runs) == 2
    assert specific_runs[1] == "off"
    assert info.listeners == {
        "all": False,
        "domains": set(),
        "entities": {"light.a", "light.b"},
        "time": False,
    }

   .opp.states.async_set("light.a", "off")
    await.opp.async_block_till_done()
    assert len(specific_runs) == 2

   .opp.states.async_set("light.b", "on")
    await.opp.async_block_till_done()
    assert len(specific_runs) == 2

   .opp.states.async_set("light.a", "on")
    await.opp.async_block_till_done()
    assert len(specific_runs) == 3
    assert specific_runs[2] == "on"


async def test_track_template_result_iterator.opp):
    """Test tracking template."""
    iterator_runs = []

    @ha.callback
    def iterator_callback(event, updates):
        iterator_runs.append(updates.pop().result)

    async_track_template_result(
       .opp,
        [
            TrackTemplate(
                Template(
                    """
            {% for state in states.sensor %}
                {% if state.state == 'on' %}
                    {{ state.entity_id }},
                {% endif %}
            {% endfor %}
            """,
                   .opp,
                ),
                None,
                timedelta(seconds=0),
            )
        ],
        iterator_callback,
    )
    await.opp.async_block_till_done()

   .opp.states.async_set("sensor.test", 5)
    await.opp.async_block_till_done()

    assert iterator_runs == [""]

    filter_runs = []

    @ha.callback
    def filter_callback(event, updates):
        filter_runs.append(updates.pop().result)

    info = async_track_template_result(
       .opp,
        [
            TrackTemplate(
                Template(
                    """{{ states.sensor|selectattr("state","equalto","on")
                |join(",", attribute="entity_id") }}""",
                   .opp,
                ),
                None,
                timedelta(seconds=0),
            )
        ],
        filter_callback,
    )
    await.opp.async_block_till_done()
    assert info.listeners == {
        "all": False,
        "domains": {"sensor"},
        "entities": set(),
        "time": False,
    }

   .opp.states.async_set("sensor.test", 6)
    await.opp.async_block_till_done()

    assert filter_runs == [""]
    assert iterator_runs == [""]

   .opp.states.async_set("sensor.new", "on")
    await.opp.async_block_till_done()
    assert iterator_runs == ["", "sensor.new,"]
    assert filter_runs == ["", "sensor.new"]


async def test_track_template_result_errors.opp, caplog):
    """Test tracking template with errors in the template."""
    template_syntax_error = Template("{{states.switch",.opp)

    template_not_exist = Template("{{states.switch.not_exist.state }}",.opp)

    syntax_error_runs = []
    not_exist_runs = []

    @ha.callback
    def syntax_error_listener(event, updates):
        track_result = updates.pop()
        syntax_error_runs.append(
            (
                event,
                track_result.template,
                track_result.last_result,
                track_result.result,
            )
        )

    async_track_template_result(
       .opp, [TrackTemplate(template_syntax_error, None)], syntax_error_listener
    )
    await.opp.async_block_till_done()

    assert len(syntax_error_runs) == 0
    assert "TemplateSyntaxError" in caplog.text

    @ha.callback
    def not_exist_runs_error_listener(event, updates):
        template_track = updates.pop()
        not_exist_runs.append(
            (
                event,
                template_track.template,
                template_track.last_result,
                template_track.result,
            )
        )

    async_track_template_result(
       .opp,
        [TrackTemplate(template_not_exist, None)],
        not_exist_runs_error_listener,
    )
    await.opp.async_block_till_done()

    assert len(syntax_error_runs) == 0
    assert len(not_exist_runs) == 0

   .opp.states.async_set("switch.not_exist", "off")
    await.opp.async_block_till_done()

    assert len(not_exist_runs) == 1
    assert not_exist_runs[0][0].data.get("entity_id") == "switch.not_exist"
    assert not_exist_runs[0][1] == template_not_exist
    assert not_exist_runs[0][2] is None
    assert not_exist_runs[0][3] == "off"

   .opp.states.async_set("switch.not_exist", "on")
    await.opp.async_block_till_done()

    assert len(syntax_error_runs) == 1
    assert len(not_exist_runs) == 2
    assert not_exist_runs[1][0].data.get("entity_id") == "switch.not_exist"
    assert not_exist_runs[1][1] == template_not_exist
    assert not_exist_runs[1][2] == "off"
    assert not_exist_runs[1][3] == "on"

    with patch.object(Template, "async_render") as render:
        render.side_effect = TemplateError(jinja2.TemplateError())

       .opp.states.async_set("switch.not_exist", "off")
        await.opp.async_block_till_done()

        assert len(not_exist_runs) == 3
        assert not_exist_runs[2][0].data.get("entity_id") == "switch.not_exist"
        assert not_exist_runs[2][1] == template_not_exist
        assert not_exist_runs[2][2] == "on"
        assert isinstance(not_exist_runs[2][3], TemplateError)


async def test_static_string.opp):
    """Test a static string."""
    template_refresh = Template("{{ 'static' }}",.opp)

    refresh_runs = []

    @ha.callback
    def refresh_listener(event, updates):
        refresh_runs.append(updates.pop().result)

    info = async_track_template_result(
       .opp, [TrackTemplate(template_refresh, None)], refresh_listener
    )
    await.opp.async_block_till_done()
    info.async_refresh()
    await.opp.async_block_till_done()

    assert refresh_runs == ["static"]


async def test_track_template_rate_limit.opp):
    """Test template rate limit."""
    template_refresh = Template("{{ states | count }}",.opp)

    refresh_runs = []

    @ha.callback
    def refresh_listener(event, updates):
        refresh_runs.append(updates.pop().result)

    info = async_track_template_result(
       .opp,
        [TrackTemplate(template_refresh, None, timedelta(seconds=0.1))],
        refresh_listener,
    )
    await.opp.async_block_till_done()
    info.async_refresh()
    await.opp.async_block_till_done()

    assert refresh_runs == [0]
   .opp.states.async_set("sensor.one", "any")
    await.opp.async_block_till_done()
    assert refresh_runs == [0]
    info.async_refresh()
    assert refresh_runs == [0, 1]
   .opp.states.async_set("sensor.two", "any")
    await.opp.async_block_till_done()
    assert refresh_runs == [0, 1]
    next_time = dt_util.utcnow() + timedelta(seconds=0.125)
    with patch(
        "openpeerpower.helpers.ratelimit.dt_util.utcnow", return_value=next_time
    ):
        async_fire_time_changed.opp, next_time)
        await.opp.async_block_till_done()
    assert refresh_runs == [0, 1, 2]
   .opp.states.async_set("sensor.three", "any")
    await.opp.async_block_till_done()
    assert refresh_runs == [0, 1, 2]
   .opp.states.async_set("sensor.four", "any")
    await.opp.async_block_till_done()
    assert refresh_runs == [0, 1, 2]
    next_time = dt_util.utcnow() + timedelta(seconds=0.125 * 2)
    with patch(
        "openpeerpower.helpers.ratelimit.dt_util.utcnow", return_value=next_time
    ):
        async_fire_time_changed.opp, next_time)
        await.opp.async_block_till_done()
    assert refresh_runs == [0, 1, 2, 4]
   .opp.states.async_set("sensor.five", "any")
    await.opp.async_block_till_done()
    assert refresh_runs == [0, 1, 2, 4]


async def test_track_template_rate_limit_suppress_listener.opp):
    """Test template rate limit will suppress the listener during the rate limit."""
    template_refresh = Template("{{ states | count }}",.opp)

    refresh_runs = []

    @ha.callback
    def refresh_listener(event, updates):
        refresh_runs.append(updates.pop().result)

    info = async_track_template_result(
       .opp,
        [TrackTemplate(template_refresh, None, timedelta(seconds=0.1))],
        refresh_listener,
    )
    await.opp.async_block_till_done()
    info.async_refresh()

    assert info.listeners == {
        "all": True,
        "domains": set(),
        "entities": set(),
        "time": False,
    }
    await.opp.async_block_till_done()

    assert refresh_runs == [0]
   .opp.states.async_set("sensor.one", "any")
    await.opp.async_block_till_done()
    assert refresh_runs == [0]
    info.async_refresh()
    assert refresh_runs == [0, 1]
   .opp.states.async_set("sensor.two", "any")
    await.opp.async_block_till_done()
    # Should be suppressed during the rate limit
    assert info.listeners == {
        "all": False,
        "domains": set(),
        "entities": set(),
        "time": False,
    }
    assert refresh_runs == [0, 1]
    next_time = dt_util.utcnow() + timedelta(seconds=0.125)
    with patch(
        "openpeerpower.helpers.ratelimit.dt_util.utcnow", return_value=next_time
    ):
        async_fire_time_changed.opp, next_time)
        await.opp.async_block_till_done()
    # Rate limit released and the all listener returns
    assert info.listeners == {
        "all": True,
        "domains": set(),
        "entities": set(),
        "time": False,
    }
    assert refresh_runs == [0, 1, 2]
   .opp.states.async_set("sensor.three", "any")
    await.opp.async_block_till_done()
    assert refresh_runs == [0, 1, 2]
   .opp.states.async_set("sensor.four", "any")
    await.opp.async_block_till_done()
    assert refresh_runs == [0, 1, 2]
    # Rate limit hit and the all listener is shut off
    assert info.listeners == {
        "all": False,
        "domains": set(),
        "entities": set(),
        "time": False,
    }
    next_time = dt_util.utcnow() + timedelta(seconds=0.125 * 2)
    with patch(
        "openpeerpower.helpers.ratelimit.dt_util.utcnow", return_value=next_time
    ):
        async_fire_time_changed.opp, next_time)
        await.opp.async_block_till_done()
    # Rate limit released and the all listener returns
    assert info.listeners == {
        "all": True,
        "domains": set(),
        "entities": set(),
        "time": False,
    }
    assert refresh_runs == [0, 1, 2, 4]
   .opp.states.async_set("sensor.five", "any")
    await.opp.async_block_till_done()
    # Rate limit hit and the all listener is shut off
    assert info.listeners == {
        "all": False,
        "domains": set(),
        "entities": set(),
        "time": False,
    }
    assert refresh_runs == [0, 1, 2, 4]


async def test_track_template_rate_limit_five.opp):
    """Test template rate limit of 5 seconds."""
    template_refresh = Template("{{ states | count }}",.opp)

    refresh_runs = []

    @ha.callback
    def refresh_listener(event, updates):
        refresh_runs.append(updates.pop().result)

    info = async_track_template_result(
       .opp,
        [TrackTemplate(template_refresh, None, timedelta(seconds=5))],
        refresh_listener,
    )
    await.opp.async_block_till_done()
    info.async_refresh()
    await.opp.async_block_till_done()

    assert refresh_runs == [0]
   .opp.states.async_set("sensor.one", "any")
    await.opp.async_block_till_done()
    assert refresh_runs == [0]
    info.async_refresh()
    assert refresh_runs == [0, 1]
   .opp.states.async_set("sensor.two", "any")
    await.opp.async_block_till_done()
    assert refresh_runs == [0, 1]
   .opp.states.async_set("sensor.three", "any")
    await.opp.async_block_till_done()
    assert refresh_runs == [0, 1]


async def test_track_template_has_default_rate_limit.opp):
    """Test template has a rate limit by default."""
   .opp.states.async_set("sensor.zero", "any")
    template_refresh = Template("{{ states | list | count }}",.opp)

    refresh_runs = []

    @ha.callback
    def refresh_listener(event, updates):
        refresh_runs.append(updates.pop().result)

    info = async_track_template_result(
       .opp,
        [TrackTemplate(template_refresh, None)],
        refresh_listener,
    )
    await.opp.async_block_till_done()
    info.async_refresh()
    await.opp.async_block_till_done()

    assert refresh_runs == [1]
   .opp.states.async_set("sensor.one", "any")
    await.opp.async_block_till_done()
    assert refresh_runs == [1]
    info.async_refresh()
    assert refresh_runs == [1, 2]
   .opp.states.async_set("sensor.two", "any")
    await.opp.async_block_till_done()
    assert refresh_runs == [1, 2]
   .opp.states.async_set("sensor.three", "any")
    await.opp.async_block_till_done()
    assert refresh_runs == [1, 2]


async def test_track_template_unavailable_sates_has_default_rate_limit.opp):
    """Test template watching for unavailable states has a rate limit by default."""
   .opp.states.async_set("sensor.zero", "unknown")
    template_refresh = Template(
        "{{ states | selectattr('state', 'in', ['unavailable', 'unknown', 'none']) | list | count }}",
       .opp,
    )

    refresh_runs = []

    @ha.callback
    def refresh_listener(event, updates):
        refresh_runs.append(updates.pop().result)

    info = async_track_template_result(
       .opp,
        [TrackTemplate(template_refresh, None)],
        refresh_listener,
    )
    await.opp.async_block_till_done()
    info.async_refresh()
    await.opp.async_block_till_done()

    assert refresh_runs == [1]
   .opp.states.async_set("sensor.one", "unknown")
    await.opp.async_block_till_done()
    assert refresh_runs == [1]
    info.async_refresh()
    assert refresh_runs == [1, 2]
   .opp.states.async_set("sensor.two", "any")
    await.opp.async_block_till_done()
    assert refresh_runs == [1, 2]
   .opp.states.async_set("sensor.three", "unknown")
    await.opp.async_block_till_done()
    assert refresh_runs == [1, 2]
    info.async_refresh()
    await.opp.async_block_till_done()
    assert refresh_runs == [1, 2, 3]
    info.async_remove()


async def test_specifically_referenced_entity_is_not_rate_limited.opp):
    """Test template rate limit of 5 seconds."""
   .opp.states.async_set("sensor.one", "none")

    template_refresh = Template('{{ states | count }}_{{ states("sensor.one") }}',.opp)

    refresh_runs = []

    @ha.callback
    def refresh_listener(event, updates):
        refresh_runs.append(updates.pop().result)

    info = async_track_template_result(
       .opp,
        [TrackTemplate(template_refresh, None, timedelta(seconds=5))],
        refresh_listener,
    )
    await.opp.async_block_till_done()
    info.async_refresh()
    await.opp.async_block_till_done()

    assert refresh_runs == ["1_none"]
   .opp.states.async_set("sensor.one", "any")
    await.opp.async_block_till_done()
    assert refresh_runs == ["1_none", "1_any"]
    info.async_refresh()
    assert refresh_runs == ["1_none", "1_any"]
   .opp.states.async_set("sensor.two", "any")
    await.opp.async_block_till_done()
    assert refresh_runs == ["1_none", "1_any"]
   .opp.states.async_set("sensor.three", "any")
    await.opp.async_block_till_done()
    assert refresh_runs == ["1_none", "1_any"]
   .opp.states.async_set("sensor.one", "none")
    await.opp.async_block_till_done()
    assert refresh_runs == ["1_none", "1_any", "3_none"]
    info.async_remove()


async def test_track_two_templates_with_different_rate_limits.opp):
    """Test two templates with different rate limits."""
    template_one = Template("{{ (states | count) + 0 }}",.opp)
    template_five = Template("{{ states | count }}",.opp)

    refresh_runs = {
        template_one: [],
        template_five: [],
    }

    @ha.callback
    def refresh_listener(event, updates):
        for update in updates:
            refresh_runs[update.template].append(update.result)

    info = async_track_template_result(
       .opp,
        [
            TrackTemplate(template_one, None, timedelta(seconds=0.1)),
            TrackTemplate(template_five, None, timedelta(seconds=5)),
        ],
        refresh_listener,
    )

    await.opp.async_block_till_done()
    info.async_refresh()
    await.opp.async_block_till_done()

    assert refresh_runs[template_one] == [0]
    assert refresh_runs[template_five] == [0]
   .opp.states.async_set("sensor.one", "any")
    await.opp.async_block_till_done()
    assert refresh_runs[template_one] == [0]
    assert refresh_runs[template_five] == [0]
    info.async_refresh()
    assert refresh_runs[template_one] == [0, 1]
    assert refresh_runs[template_five] == [0, 1]
   .opp.states.async_set("sensor.two", "any")
    await.opp.async_block_till_done()
    assert refresh_runs[template_one] == [0, 1]
    assert refresh_runs[template_five] == [0, 1]
    next_time = dt_util.utcnow() + timedelta(seconds=0.125 * 1)
    with patch(
        "openpeerpower.helpers.ratelimit.dt_util.utcnow", return_value=next_time
    ):
        async_fire_time_changed.opp, next_time)
        await.opp.async_block_till_done()
    await.opp.async_block_till_done()
    assert refresh_runs[template_one] == [0, 1, 2]
    assert refresh_runs[template_five] == [0, 1]
   .opp.states.async_set("sensor.three", "any")
    await.opp.async_block_till_done()
    assert refresh_runs[template_one] == [0, 1, 2]
    assert refresh_runs[template_five] == [0, 1]
   .opp.states.async_set("sensor.four", "any")
    await.opp.async_block_till_done()
    assert refresh_runs[template_one] == [0, 1, 2]
    assert refresh_runs[template_five] == [0, 1]
   .opp.states.async_set("sensor.five", "any")
    await.opp.async_block_till_done()
    assert refresh_runs[template_one] == [0, 1, 2]
    assert refresh_runs[template_five] == [0, 1]
    info.async_remove()


async def test_string.opp):
    """Test a string."""
    template_refresh = Template("no_template",.opp)

    refresh_runs = []

    @ha.callback
    def refresh_listener(event, updates):
        refresh_runs.append(updates.pop().result)

    info = async_track_template_result(
       .opp, [TrackTemplate(template_refresh, None)], refresh_listener
    )
    await.opp.async_block_till_done()
    info.async_refresh()
    await.opp.async_block_till_done()

    assert refresh_runs == ["no_template"]


async def test_track_template_result_refresh_cancel.opp):
    """Test cancelling and refreshing result."""
    template_refresh = Template("{{states.switch.test.state == 'on' and now() }}",.opp)

    refresh_runs = []

    @ha.callback
    def refresh_listener(event, updates):
        refresh_runs.append(updates.pop().result)

    info = async_track_template_result(
       .opp, [TrackTemplate(template_refresh, None)], refresh_listener
    )
    await.opp.async_block_till_done()

   .opp.states.async_set("switch.test", "off")
    await.opp.async_block_till_done()

    assert refresh_runs == [False]

    assert len(refresh_runs) == 1

    info.async_refresh()
   .opp.states.async_set("switch.test", "on")
    await.opp.async_block_till_done()

    assert len(refresh_runs) == 2
    assert refresh_runs[0] != refresh_runs[1]

    info.async_remove()
   .opp.states.async_set("switch.test", "off")
    await.opp.async_block_till_done()

    assert len(refresh_runs) == 2

    template_refresh = Template("{{ value }}",.opp)
    refresh_runs = []

    info = async_track_template_result(
       .opp,
        [TrackTemplate(template_refresh, {"value": "duck"})],
        refresh_listener,
    )
    await.opp.async_block_till_done()
    info.async_refresh()
    await.opp.async_block_till_done()

    assert refresh_runs == ["duck"]

    info.async_refresh()
    await.opp.async_block_till_done()
    assert refresh_runs == ["duck"]


async def test_async_track_template_result_multiple_templates.opp):
    """Test tracking multiple templates."""

    template_1 = Template("{{ states.switch.test.state == 'on' }}")
    template_2 = Template("{{ states.switch.test.state == 'on' }}")
    template_3 = Template("{{ states.switch.test.state == 'off' }}")
    template_4 = Template(
        "{{ states.binary_sensor | map(attribute='entity_id') | list }}"
    )

    refresh_runs = []

    @ha.callback
    def refresh_listener(event, updates):
        refresh_runs.append(updates)

    async_track_template_result(
       .opp,
        [
            TrackTemplate(template_1, None),
            TrackTemplate(template_2, None),
            TrackTemplate(template_3, None),
            TrackTemplate(template_4, None),
        ],
        refresh_listener,
    )

   .opp.states.async_set("switch.test", "on")
    await.opp.async_block_till_done()

    assert refresh_runs == [
        [
            TrackTemplateResult(template_1, None, True),
            TrackTemplateResult(template_2, None, True),
            TrackTemplateResult(template_3, None, False),
        ]
    ]

    refresh_runs = []
   .opp.states.async_set("switch.test", "off")
    await.opp.async_block_till_done()

    assert refresh_runs == [
        [
            TrackTemplateResult(template_1, True, False),
            TrackTemplateResult(template_2, True, False),
            TrackTemplateResult(template_3, False, True),
        ]
    ]

    refresh_runs = []
   .opp.states.async_set("binary_sensor.test", "off")
    await.opp.async_block_till_done()

    assert refresh_runs == [
        [TrackTemplateResult(template_4, None, ["binary_sensor.test"])]
    ]


async def test_async_track_template_result_multiple_templates_mixing_domain.opp):
    """Test tracking multiple templates when tracking entities and an entire domain."""

    template_1 = Template("{{ states.switch.test.state == 'on' }}")
    template_2 = Template("{{ states.switch.test.state == 'on' }}")
    template_3 = Template("{{ states.switch.test.state == 'off' }}")
    template_4 = Template("{{ states.switch | map(attribute='entity_id') | list }}")

    refresh_runs = []

    @ha.callback
    def refresh_listener(event, updates):
        refresh_runs.append(updates)

    async_track_template_result(
       .opp,
        [
            TrackTemplate(template_1, None),
            TrackTemplate(template_2, None),
            TrackTemplate(template_3, None),
            TrackTemplate(template_4, None, timedelta(seconds=0)),
        ],
        refresh_listener,
    )

   .opp.states.async_set("switch.test", "on")
    await.opp.async_block_till_done()

    assert refresh_runs == [
        [
            TrackTemplateResult(template_1, None, True),
            TrackTemplateResult(template_2, None, True),
            TrackTemplateResult(template_3, None, False),
            TrackTemplateResult(template_4, None, ["switch.test"]),
        ]
    ]

    refresh_runs = []
   .opp.states.async_set("switch.test", "off")
    await.opp.async_block_till_done()

    assert refresh_runs == [
        [
            TrackTemplateResult(template_1, True, False),
            TrackTemplateResult(template_2, True, False),
            TrackTemplateResult(template_3, False, True),
        ]
    ]

    refresh_runs = []
   .opp.states.async_set("binary_sensor.test", "off")
    await.opp.async_block_till_done()

    assert refresh_runs == []

    refresh_runs = []
   .opp.states.async_set("switch.new", "off")
    await.opp.async_block_till_done()

    assert refresh_runs == [
        [
            TrackTemplateResult(
                template_4, ["switch.test"], ["switch.new", "switch.test"]
            )
        ]
    ]


async def test_async_track_template_result_raise_on_template_error.opp):
    """Test that we raise as soon as we encounter a failed template."""

    with pytest.raises(TemplateError):
        async_track_template_result(
           .opp,
            [
                TrackTemplate(
                    Template(
                        "{{ states.switch | function_that_does_not_exist | list }}"
                    ),
                    None,
                ),
            ],
            ha.callback(lambda event, updates: None),
            raise_on_template_error=True,
        )


async def test_track_template_with_time.opp):
    """Test tracking template with time."""

   .opp.states.async_set("switch.test", "on")
    specific_runs = []
    template_complex = Template("{{ states.switch.test.state and now() }}",.opp)

    def specific_run_callback(event, updates):
        specific_runs.append(updates.pop().result)

    info = async_track_template_result(
       .opp, [TrackTemplate(template_complex, None)], specific_run_callback
    )
    await.opp.async_block_till_done()

    assert info.listeners == {
        "all": False,
        "domains": set(),
        "entities": {"switch.test"},
        "time": True,
    }

    await.opp.async_block_till_done()
    now = dt_util.utcnow()
    async_fire_time_changed.opp, now + timedelta(seconds=61))
    async_fire_time_changed.opp, now + timedelta(seconds=61 * 2))
    await.opp.async_block_till_done()
    assert specific_runs[-1] != specific_runs[0]
    info.async_remove()


async def test_track_template_with_time_default.opp):
    """Test tracking template with time."""

    specific_runs = []
    template_complex = Template("{{ now() }}",.opp)

    def specific_run_callback(event, updates):
        specific_runs.append(updates.pop().result)

    info = async_track_template_result(
       .opp, [TrackTemplate(template_complex, None)], specific_run_callback
    )
    await.opp.async_block_till_done()

    assert info.listeners == {
        "all": False,
        "domains": set(),
        "entities": set(),
        "time": True,
    }

    await.opp.async_block_till_done()
    now = dt_util.utcnow()
    async_fire_time_changed.opp, now + timedelta(seconds=2))
    async_fire_time_changed.opp, now + timedelta(seconds=4))
    await.opp.async_block_till_done()
    assert len(specific_runs) < 2
    async_fire_time_changed.opp, now + timedelta(minutes=2))
    await.opp.async_block_till_done()
    async_fire_time_changed.opp, now + timedelta(minutes=4))
    await.opp.async_block_till_done()
    assert len(specific_runs) >= 2
    assert specific_runs[-1] != specific_runs[0]
    info.async_remove()


async def test_track_template_with_time_that_leaves_scope.opp):
    """Test tracking template with time."""
    now = dt_util.utcnow()
    test_time = datetime(now.year + 1, 5, 24, 11, 59, 1, 500000, tzinfo=dt_util.UTC)

    with patch("openpeerpower.util.dt.utcnow", return_value=test_time):
       .opp.states.async_set("binary_sensor.washing_machine", "on")
        specific_runs = []
        template_complex = Template(
            """
            {% if states.binary_sensor.washing_machine.state == "on" %}
                {{ now() }}
            {% else %}
                {{ states.binary_sensor.washing_machine.last_updated }}
            {% endif %}
        """,
           .opp,
        )

        def specific_run_callback(event, updates):
            specific_runs.append(updates.pop().result)

        info = async_track_template_result(
           .opp, [TrackTemplate(template_complex, None)], specific_run_callback
        )
        await.opp.async_block_till_done()

        assert info.listeners == {
            "all": False,
            "domains": set(),
            "entities": {"binary_sensor.washing_machine"},
            "time": True,
        }

       .opp.states.async_set("binary_sensor.washing_machine", "off")
        await.opp.async_block_till_done()

        assert info.listeners == {
            "all": False,
            "domains": set(),
            "entities": {"binary_sensor.washing_machine"},
            "time": False,
        }

       .opp.states.async_set("binary_sensor.washing_machine", "on")
        await.opp.async_block_till_done()

        assert info.listeners == {
            "all": False,
            "domains": set(),
            "entities": {"binary_sensor.washing_machine"},
            "time": True,
        }

        # Verify we do not update before the minute rolls over
        callback_count_before_time_change = len(specific_runs)
        async_fire_time_changed.opp, test_time)
        await.opp.async_block_till_done()
        assert len(specific_runs) == callback_count_before_time_change

        async_fire_time_changed.opp, test_time + timedelta(seconds=58))
        await.opp.async_block_till_done()
        assert len(specific_runs) == callback_count_before_time_change

        # Verify we do update on the next change of minute
        async_fire_time_changed.opp, test_time + timedelta(seconds=59))

        await.opp.async_block_till_done()
        assert len(specific_runs) == callback_count_before_time_change + 1

    info.async_remove()


async def test_async_track_template_result_multiple_templates_mixing_listeners.opp):
    """Test tracking multiple templates with mixing listener types."""

    template_1 = Template("{{ states.switch.test.state == 'on' }}")
    template_2 = Template("{{ now() and True }}")

    refresh_runs = []

    @ha.callback
    def refresh_listener(event, updates):
        refresh_runs.append(updates)

    now = dt_util.utcnow()

    time_that_will_not_match_right_away = datetime(
        now.year + 1, 5, 24, 11, 59, 55, tzinfo=dt_util.UTC
    )

    with patch(
        "openpeerpower.util.dt.utcnow", return_value=time_that_will_not_match_right_away
    ):
        info = async_track_template_result(
           .opp,
            [
                TrackTemplate(template_1, None),
                TrackTemplate(template_2, None),
            ],
            refresh_listener,
        )

    assert info.listeners == {
        "all": False,
        "domains": set(),
        "entities": {"switch.test"},
        "time": True,
    }
   .opp.states.async_set("switch.test", "on")
    await.opp.async_block_till_done()

    assert refresh_runs == [
        [
            TrackTemplateResult(template_1, None, True),
        ]
    ]

    refresh_runs = []
   .opp.states.async_set("switch.test", "off")
    await.opp.async_block_till_done()

    assert refresh_runs == [
        [
            TrackTemplateResult(template_1, True, False),
        ]
    ]

    refresh_runs = []
    next_time = time_that_will_not_match_right_away + timedelta(hours=25)
    with patch("openpeerpower.util.dt.utcnow", return_value=next_time):
        async_fire_time_changed.opp, next_time)
        await.opp.async_block_till_done()

    assert refresh_runs == [
        [
            TrackTemplateResult(template_2, None, True),
        ]
    ]


async def test_track_same_state_simple_no_trigger.opp):
    """Test track_same_change with no trigger."""
    callback_runs = []
    period = timedelta(minutes=1)

    @ha.callback
    def callback_run_callback():
        callback_runs.append(1)

    async_track_same_state(
       .opp,
        period,
        callback_run_callback,
        callback(lambda _, _2, to_s: to_s.state == "on"),
        entity_ids="light.Bowl",
    )

    # Adding state to state machine
   .opp.states.async_set("light.Bowl", "on")
    await.opp.async_block_till_done()
    assert len(callback_runs) == 0

    # Change state on state machine
   .opp.states.async_set("light.Bowl", "off")
    await.opp.async_block_till_done()
    assert len(callback_runs) == 0

    # change time to track and see if they trigger
    future = dt_util.utcnow() + period
    async_fire_time_changed.opp, future)
    await.opp.async_block_till_done()
    assert len(callback_runs) == 0


async def test_track_same_state_simple_trigger_check_funct.opp):
    """Test track_same_change with trigger and check funct."""
    callback_runs = []
    check_func = []
    period = timedelta(minutes=1)

    @ha.callback
    def callback_run_callback():
        callback_runs.append(1)

    @ha.callback
    def async_check_func(entity, from_s, to_s):
        check_func.append((entity, from_s, to_s))
        return True

    async_track_same_state(
       .opp,
        period,
        callback_run_callback,
        entity_ids="light.Bowl",
        async_check_same_func=async_check_func,
    )

    # Adding state to state machine
   .opp.states.async_set("light.Bowl", "on")
    await.opp.async_block_till_done()
    await.opp.async_block_till_done()
    assert len(callback_runs) == 0
    assert check_func[-1][2].state == "on"
    assert check_func[-1][0] == "light.bowl"

    # change time to track and see if they trigger
    future = dt_util.utcnow() + period
    async_fire_time_changed.opp, future)
    await.opp.async_block_till_done()
    assert len(callback_runs) == 1


async def test_track_time_interval.opp):
    """Test tracking time interval."""
    specific_runs = []

    utc_now = dt_util.utcnow()
    unsub = async_track_time_interval(
       .opp, callback(lambda x: specific_runs.append(x)), timedelta(seconds=10)
    )

    async_fire_time_changed.opp, utc_now + timedelta(seconds=5))
    await.opp.async_block_till_done()
    assert len(specific_runs) == 0

    async_fire_time_changed.opp, utc_now + timedelta(seconds=13))
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1

    async_fire_time_changed.opp, utc_now + timedelta(minutes=20))
    await.opp.async_block_till_done()
    assert len(specific_runs) == 2

    unsub()

    async_fire_time_changed.opp, utc_now + timedelta(seconds=30))
    await.opp.async_block_till_done()
    assert len(specific_runs) == 2


async def test_track_sunrise.opp, legacy_patchable_time):
    """Test track the sunrise."""
    latitude = 32.87336
    longitude = 117.22743

    # Setup sun component
   .opp.config.latitude = latitude
   .opp.config.longitude = longitude
    assert await async_setup_component(
       .opp, sun.DOMAIN, {sun.DOMAIN: {sun.CONF_ELEVATION: 0}}
    )

    # Get next sunrise/sunset
    astral = Astral()
    utc_now = datetime(2014, 5, 24, 12, 0, 0, tzinfo=dt_util.UTC)
    utc_today = utc_now.date()

    mod = -1
    while True:
        next_rising = astral.sunrise_utc(
            utc_today + timedelta(days=mod), latitude, longitude
        )
        if next_rising > utc_now:
            break
        mod += 1

    # Track sunrise
    runs = []
    with patch("openpeerpower.util.dt.utcnow", return_value=utc_now):
        unsub = async_track_sunrise.opp, callback(lambda: runs.append(1)))

    offset_runs = []
    offset = timedelta(minutes=30)
    with patch("openpeerpower.util.dt.utcnow", return_value=utc_now):
        unsub2 = async_track_sunrise(
           .opp, callback(lambda: offset_runs.append(1)), offset
        )

    # run tests
    async_fire_time_changed.opp, next_rising - offset)
    await.opp.async_block_till_done()
    assert len(runs) == 0
    assert len(offset_runs) == 0

    async_fire_time_changed.opp, next_rising)
    await.opp.async_block_till_done()
    assert len(runs) == 1
    assert len(offset_runs) == 0

    async_fire_time_changed.opp, next_rising + offset)
    await.opp.async_block_till_done()
    assert len(runs) == 1
    assert len(offset_runs) == 1

    unsub()
    unsub2()

    async_fire_time_changed.opp, next_rising + offset)
    await.opp.async_block_till_done()
    assert len(runs) == 1
    assert len(offset_runs) == 1


async def test_track_sunrise_update_location.opp, legacy_patchable_time):
    """Test track the sunrise."""
    # Setup sun component
   .opp.config.latitude = 32.87336
   .opp.config.longitude = 117.22743
    assert await async_setup_component(
       .opp, sun.DOMAIN, {sun.DOMAIN: {sun.CONF_ELEVATION: 0}}
    )

    # Get next sunrise
    astral = Astral()
    utc_now = datetime(2014, 5, 24, 12, 0, 0, tzinfo=dt_util.UTC)
    utc_today = utc_now.date()

    mod = -1
    while True:
        next_rising = astral.sunrise_utc(
            utc_today + timedelta(days=mod),.opp.config.latitude,.opp.config.longitude
        )
        if next_rising > utc_now:
            break
        mod += 1

    # Track sunrise
    runs = []
    with patch("openpeerpower.util.dt.utcnow", return_value=utc_now):
        async_track_sunrise.opp, callback(lambda: runs.append(1)))

    # Mimic sunrise
    async_fire_time_changed.opp, next_rising)
    await.opp.async_block_till_done()
    assert len(runs) == 1

    # Move!
    with patch("openpeerpower.util.dt.utcnow", return_value=utc_now):
        await.opp.config.async_update(latitude=40.755931, longitude=-73.984606)
        await.opp.async_block_till_done()

    # Mimic sunrise
    async_fire_time_changed.opp, next_rising)
    await.opp.async_block_till_done()
    # Did not increase
    assert len(runs) == 1

    # Get next sunrise
    mod = -1
    while True:
        next_rising = astral.sunrise_utc(
            utc_today + timedelta(days=mod),.opp.config.latitude,.opp.config.longitude
        )
        if next_rising > utc_now:
            break
        mod += 1

    # Mimic sunrise at new location
    async_fire_time_changed.opp, next_rising)
    await.opp.async_block_till_done()
    assert len(runs) == 2


async def test_track_sunset.opp, legacy_patchable_time):
    """Test track the sunset."""
    latitude = 32.87336
    longitude = 117.22743

    # Setup sun component
   .opp.config.latitude = latitude
   .opp.config.longitude = longitude
    assert await async_setup_component(
       .opp, sun.DOMAIN, {sun.DOMAIN: {sun.CONF_ELEVATION: 0}}
    )

    # Get next sunrise/sunset
    astral = Astral()
    utc_now = datetime(2014, 5, 24, 12, 0, 0, tzinfo=dt_util.UTC)
    utc_today = utc_now.date()

    mod = -1
    while True:
        next_setting = astral.sunset_utc(
            utc_today + timedelta(days=mod), latitude, longitude
        )
        if next_setting > utc_now:
            break
        mod += 1

    # Track sunset
    runs = []
    with patch("openpeerpower.util.dt.utcnow", return_value=utc_now):
        unsub = async_track_sunset.opp, callback(lambda: runs.append(1)))

    offset_runs = []
    offset = timedelta(minutes=30)
    with patch("openpeerpower.util.dt.utcnow", return_value=utc_now):
        unsub2 = async_track_sunset(
           .opp, callback(lambda: offset_runs.append(1)), offset
        )

    # Run tests
    async_fire_time_changed.opp, next_setting - offset)
    await.opp.async_block_till_done()
    assert len(runs) == 0
    assert len(offset_runs) == 0

    async_fire_time_changed.opp, next_setting)
    await.opp.async_block_till_done()
    assert len(runs) == 1
    assert len(offset_runs) == 0

    async_fire_time_changed.opp, next_setting + offset)
    await.opp.async_block_till_done()
    assert len(runs) == 1
    assert len(offset_runs) == 1

    unsub()
    unsub2()

    async_fire_time_changed.opp, next_setting + offset)
    await.opp.async_block_till_done()
    assert len(runs) == 1
    assert len(offset_runs) == 1


async def test_async_track_time_change.opp):
    """Test tracking time change."""
    wildcard_runs = []
    specific_runs = []

    now = dt_util.utcnow()

    time_that_will_not_match_right_away = datetime(
        now.year + 1, 5, 24, 11, 59, 55, tzinfo=dt_util.UTC
    )

    with patch(
        "openpeerpower.util.dt.utcnow", return_value=time_that_will_not_match_right_away
    ):
        unsub = async_track_time_change(
           .opp, callback(lambda x: wildcard_runs.append(x))
        )
        unsub_utc = async_track_utc_time_change(
           .opp, callback(lambda x: specific_runs.append(x)), second=[0, 30]
        )

    async_fire_time_changed(
       .opp, datetime(now.year + 1, 5, 24, 12, 0, 0, 999999, tzinfo=dt_util.UTC)
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1
    assert len(wildcard_runs) == 1

    async_fire_time_changed(
       .opp, datetime(now.year + 1, 5, 24, 12, 0, 15, 999999, tzinfo=dt_util.UTC)
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1
    assert len(wildcard_runs) == 2

    async_fire_time_changed(
       .opp, datetime(now.year + 1, 5, 24, 12, 0, 30, 999999, tzinfo=dt_util.UTC)
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 2
    assert len(wildcard_runs) == 3

    unsub()
    unsub_utc()

    async_fire_time_changed(
       .opp, datetime(now.year + 1, 5, 24, 12, 0, 30, 999999, tzinfo=dt_util.UTC)
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 2
    assert len(wildcard_runs) == 3


async def test_periodic_task_minute.opp):
    """Test periodic tasks per minute."""
    specific_runs = []

    now = dt_util.utcnow()

    time_that_will_not_match_right_away = datetime(
        now.year + 1, 5, 24, 11, 59, 55, tzinfo=dt_util.UTC
    )

    with patch(
        "openpeerpower.util.dt.utcnow", return_value=time_that_will_not_match_right_away
    ):
        unsub = async_track_utc_time_change(
           .opp, callback(lambda x: specific_runs.append(x)), minute="/5", second=0
        )

    async_fire_time_changed(
       .opp, datetime(now.year + 1, 5, 24, 12, 0, 0, 999999, tzinfo=dt_util.UTC)
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1

    async_fire_time_changed(
       .opp, datetime(now.year + 1, 5, 24, 12, 3, 0, 999999, tzinfo=dt_util.UTC)
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1

    async_fire_time_changed(
       .opp, datetime(now.year + 1, 5, 24, 12, 5, 0, 999999, tzinfo=dt_util.UTC)
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 2

    unsub()

    async_fire_time_changed(
       .opp, datetime(now.year + 1, 5, 24, 12, 5, 0, 999999, tzinfo=dt_util.UTC)
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 2


async def test_periodic_task_hour.opp):
    """Test periodic tasks per hour."""
    specific_runs = []

    now = dt_util.utcnow()

    time_that_will_not_match_right_away = datetime(
        now.year + 1, 5, 24, 21, 59, 55, tzinfo=dt_util.UTC
    )

    with patch(
        "openpeerpower.util.dt.utcnow", return_value=time_that_will_not_match_right_away
    ):
        unsub = async_track_utc_time_change(
           .opp,
            callback(lambda x: specific_runs.append(x)),
            hour="/2",
            minute=0,
            second=0,
        )

    async_fire_time_changed(
       .opp, datetime(now.year + 1, 5, 24, 22, 0, 0, 999999, tzinfo=dt_util.UTC)
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1

    async_fire_time_changed(
       .opp, datetime(now.year + 1, 5, 24, 23, 0, 0, 999999, tzinfo=dt_util.UTC)
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1

    async_fire_time_changed(
       .opp, datetime(now.year + 1, 5, 25, 0, 0, 0, 999999, tzinfo=dt_util.UTC)
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 2

    async_fire_time_changed(
       .opp, datetime(now.year + 1, 5, 25, 1, 0, 0, 999999, tzinfo=dt_util.UTC)
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 2

    async_fire_time_changed(
       .opp, datetime(now.year + 1, 5, 25, 2, 0, 0, 999999, tzinfo=dt_util.UTC)
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 3

    unsub()

    async_fire_time_changed(
       .opp, datetime(now.year + 1, 5, 25, 2, 0, 0, tzinfo=dt_util.UTC)
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 3


async def test_periodic_task_wrong_input.opp):
    """Test periodic tasks with wrong input."""
    specific_runs = []

    now = dt_util.utcnow()

    with pytest.raises(ValueError):
        async_track_utc_time_change(
           .opp, callback(lambda x: specific_runs.append(x)), hour="/two"
        )

    async_fire_time_changed(
       .opp, datetime(now.year + 1, 5, 2, 0, 0, 0, 999999, tzinfo=dt_util.UTC)
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 0


async def test_periodic_task_clock_rollback.opp):
    """Test periodic tasks with the time rolling backwards."""
    specific_runs = []

    now = dt_util.utcnow()

    time_that_will_not_match_right_away = datetime(
        now.year + 1, 5, 24, 21, 59, 55, tzinfo=dt_util.UTC
    )

    with patch(
        "openpeerpower.util.dt.utcnow", return_value=time_that_will_not_match_right_away
    ):
        unsub = async_track_utc_time_change(
           .opp,
            callback(lambda x: specific_runs.append(x)),
            hour="/2",
            minute=0,
            second=0,
        )

    async_fire_time_changed(
       .opp, datetime(now.year + 1, 5, 24, 22, 0, 0, 999999, tzinfo=dt_util.UTC)
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1

    async_fire_time_changed(
       .opp, datetime(now.year + 1, 5, 24, 23, 0, 0, 999999, tzinfo=dt_util.UTC)
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1

    async_fire_time_changed(
       .opp,
        datetime(now.year + 1, 5, 24, 22, 0, 0, 999999, tzinfo=dt_util.UTC),
        fire_all=True,
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1

    async_fire_time_changed(
       .opp,
        datetime(now.year + 1, 5, 24, 0, 0, 0, 999999, tzinfo=dt_util.UTC),
        fire_all=True,
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1

    async_fire_time_changed(
       .opp, datetime(now.year + 1, 5, 25, 2, 0, 0, 999999, tzinfo=dt_util.UTC)
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 2

    unsub()

    async_fire_time_changed(
       .opp, datetime(now.year + 1, 5, 25, 2, 0, 0, 999999, tzinfo=dt_util.UTC)
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 2


async def test_periodic_task_duplicate_time.opp):
    """Test periodic tasks not triggering on duplicate time."""
    specific_runs = []

    now = dt_util.utcnow()

    time_that_will_not_match_right_away = datetime(
        now.year + 1, 5, 24, 21, 59, 55, tzinfo=dt_util.UTC
    )

    with patch(
        "openpeerpower.util.dt.utcnow", return_value=time_that_will_not_match_right_away
    ):
        unsub = async_track_utc_time_change(
           .opp,
            callback(lambda x: specific_runs.append(x)),
            hour="/2",
            minute=0,
            second=0,
        )

    async_fire_time_changed(
       .opp, datetime(now.year + 1, 5, 24, 22, 0, 0, 999999, tzinfo=dt_util.UTC)
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1

    async_fire_time_changed(
       .opp, datetime(now.year + 1, 5, 24, 22, 0, 0, 999999, tzinfo=dt_util.UTC)
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1

    async_fire_time_changed(
       .opp, datetime(now.year + 1, 5, 25, 0, 0, 0, 999999, tzinfo=dt_util.UTC)
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 2

    unsub()


async def test_periodic_task_entering_dst.opp):
    """Test periodic task behavior when entering dst."""
    timezone = dt_util.get_time_zone("Europe/Vienna")
    dt_util.set_default_time_zone(timezone)
    specific_runs = []

    now = dt_util.utcnow()
    time_that_will_not_match_right_away = timezone.localize(
        datetime(now.year + 1, 3, 25, 2, 31, 0)
    )

    with patch(
        "openpeerpower.util.dt.utcnow", return_value=time_that_will_not_match_right_away
    ):
        unsub = async_track_time_change(
           .opp,
            callback(lambda x: specific_runs.append(x)),
            hour=2,
            minute=30,
            second=0,
        )

    async_fire_time_changed(
       .opp, timezone.localize(datetime(now.year + 1, 3, 25, 1, 50, 0, 999999))
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 0

    async_fire_time_changed(
       .opp, timezone.localize(datetime(now.year + 1, 3, 25, 3, 50, 0, 999999))
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 0

    async_fire_time_changed(
       .opp, timezone.localize(datetime(now.year + 1, 3, 26, 1, 50, 0, 999999))
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 0

    async_fire_time_changed(
       .opp, timezone.localize(datetime(now.year + 1, 3, 26, 2, 50, 0, 999999))
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1

    unsub()


async def test_periodic_task_leaving_dst.opp):
    """Test periodic task behavior when leaving dst."""
    timezone = dt_util.get_time_zone("Europe/Vienna")
    dt_util.set_default_time_zone(timezone)
    specific_runs = []

    now = dt_util.utcnow()

    time_that_will_not_match_right_away = timezone.localize(
        datetime(now.year + 1, 10, 28, 2, 28, 0), is_dst=True
    )

    with patch(
        "openpeerpower.util.dt.utcnow", return_value=time_that_will_not_match_right_away
    ):
        unsub = async_track_time_change(
           .opp,
            callback(lambda x: specific_runs.append(x)),
            hour=2,
            minute=30,
            second=0,
        )

    async_fire_time_changed(
       .opp,
        timezone.localize(
            datetime(now.year + 1, 10, 28, 2, 5, 0, 999999), is_dst=False
        ),
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 0

    async_fire_time_changed(
       .opp,
        timezone.localize(
            datetime(now.year + 1, 10, 28, 2, 55, 0, 999999), is_dst=False
        ),
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 1

    async_fire_time_changed(
       .opp,
        timezone.localize(
            datetime(now.year + 2, 10, 28, 2, 45, 0, 999999), is_dst=True
        ),
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 2

    async_fire_time_changed(
       .opp,
        timezone.localize(
            datetime(now.year + 2, 10, 28, 2, 55, 0, 999999), is_dst=True
        ),
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 2

    async_fire_time_changed(
       .opp,
        timezone.localize(
            datetime(now.year + 2, 10, 28, 2, 55, 0, 999999), is_dst=True
        ),
    )
    await.opp.async_block_till_done()
    assert len(specific_runs) == 2

    unsub()


async def test_call_later.opp):
    """Test calling an action later."""

    def action():
        pass

    now = datetime(2017, 12, 19, 15, 40, 0, tzinfo=dt_util.UTC)

    with patch(
        "openpeerpower.helpers.event.async_track_point_in_utc_time"
    ) as mock, patch("openpeerpower.util.dt.utcnow", return_value=now):
        async_call_later.opp, 3, action)

    assert len(mock.mock_calls) == 1
    p.opp, p_action, p_point = mock.mock_calls[0][1]
    assert p.opp is.opp
    assert p_action is action
    assert p_point == now + timedelta(seconds=3)


async def test_async_call_later.opp):
    """Test calling an action later."""

    def action():
        pass

    now = datetime(2017, 12, 19, 15, 40, 0, tzinfo=dt_util.UTC)

    with patch(
        "openpeerpower.helpers.event.async_track_point_in_utc_time"
    ) as mock, patch("openpeerpower.util.dt.utcnow", return_value=now):
        remove = async_call_later.opp, 3, action)

    assert len(mock.mock_calls) == 1
    p.opp, p_action, p_point = mock.mock_calls[0][1]
    assert p.opp is.opp
    assert p_action is action
    assert p_point == now + timedelta(seconds=3)
    assert remove is mock()


async def test_track_state_change_event_chain_multple_entity.opp):
    """Test that adding a new state tracker inside a tracker does not fire right away."""
    tracker_called = []
    chained_tracker_called = []

    chained_tracker_unsub = []
    tracker_unsub = []

    @ha.callback
    def chained_single_run_callback(event):
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        chained_tracker_called.append((old_state, new_state))

    @ha.callback
    def single_run_callback(event):
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        tracker_called.append((old_state, new_state))

        chained_tracker_unsub.append(
            async_track_state_change_event(
               .opp, ["light.bowl", "light.top"], chained_single_run_callback
            )
        )

    tracker_unsub.append(
        async_track_state_change_event(
           .opp, ["light.bowl", "light.top"], single_run_callback
        )
    )

   .opp.states.async_set("light.bowl", "on")
   .opp.states.async_set("light.top", "on")
    await.opp.async_block_till_done()

    assert len(tracker_called) == 2
    assert len(chained_tracker_called) == 1
    assert len(tracker_unsub) == 1
    assert len(chained_tracker_unsub) == 2

   .opp.states.async_set("light.bowl", "off")
    await.opp.async_block_till_done()

    assert len(tracker_called) == 3
    assert len(chained_tracker_called) == 3
    assert len(tracker_unsub) == 1
    assert len(chained_tracker_unsub) == 3


async def test_track_state_change_event_chain_single_entity.opp):
    """Test that adding a new state tracker inside a tracker does not fire right away."""
    tracker_called = []
    chained_tracker_called = []

    chained_tracker_unsub = []
    tracker_unsub = []

    @ha.callback
    def chained_single_run_callback(event):
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        chained_tracker_called.append((old_state, new_state))

    @ha.callback
    def single_run_callback(event):
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        tracker_called.append((old_state, new_state))

        chained_tracker_unsub.append(
            async_track_state_change_event(
               .opp, "light.bowl", chained_single_run_callback
            )
        )

    tracker_unsub.append(
        async_track_state_change_event.opp, "light.bowl", single_run_callback)
    )

   .opp.states.async_set("light.bowl", "on")
    await.opp.async_block_till_done()

    assert len(tracker_called) == 1
    assert len(chained_tracker_called) == 0
    assert len(tracker_unsub) == 1
    assert len(chained_tracker_unsub) == 1

   .opp.states.async_set("light.bowl", "off")
    await.opp.async_block_till_done()

    assert len(tracker_called) == 2
    assert len(chained_tracker_called) == 1
    assert len(tracker_unsub) == 1
    assert len(chained_tracker_unsub) == 2


async def test_track_point_in_utc_time_cancel.opp):
    """Test cancel of async track point in time."""

    times = []

    @ha.callback
    def run_callback(utc_time):
        nonlocal times
        times.append(utc_time)

    def _setup_listeners():
        """Ensure we test the non-async version."""
        utc_now = dt_util.utcnow()

        with pytest.raises(TypeError):
            track_point_in_utc_time("no.opp", run_callback, utc_now)

        unsub1 =.opp.helpers.event.track_point_in_utc_time(
            run_callback, utc_now + timedelta(seconds=0.1)
        )
       .opp.helpers.event.track_point_in_utc_time(
            run_callback, utc_now + timedelta(seconds=0.1)
        )

        unsub1()

    await.opp.async_add_executor_job(_setup_listeners)

    await asyncio.sleep(0.2)

    assert len(times) == 1
    assert times[0].tzinfo == dt_util.UTC


async def test_async_track_point_in_time_cancel.opp):
    """Test cancel of async track point in time."""

    times = []
    hst_tz = dt_util.get_time_zone("US/Hawaii")
    dt_util.set_default_time_zone(hst_tz)

    @ha.callback
    def run_callback(local_time):
        nonlocal times
        times.append(local_time)

    utc_now = dt_util.utcnow()
    hst_now = utc_now.astimezone(hst_tz)

    unsub1 =.opp.helpers.event.async_track_point_in_time(
        run_callback, hst_now + timedelta(seconds=0.1)
    )
   .opp.helpers.event.async_track_point_in_time(
        run_callback, hst_now + timedelta(seconds=0.1)
    )

    unsub1()

    await asyncio.sleep(0.2)

    assert len(times) == 1
    assert times[0].tzinfo.zone == "US/Hawaii"


async def test_async_track_entity_registry_updated_event.opp):
    """Test tracking entity registry updates for an entity_id."""

    entity_id = "switch.puppy_feeder"
    new_entity_id = "switch.dog_feeder"
    untracked_entity_id = "switch.kitty_feeder"

   .opp.states.async_set(entity_id, "on")
    await.opp.async_block_till_done()
    event_data = []

    @ha.callback
    def run_callback(event):
        event_data.append(event.data)

    unsub1 =.opp.helpers.event.async_track_entity_registry_updated_event(
        entity_id, run_callback
    )
    unsub2 =.opp.helpers.event.async_track_entity_registry_updated_event(
        new_entity_id, run_callback
    )
   .opp.bus.async_fire(
        EVENT_ENTITY_REGISTRY_UPDATED, {"action": "create", "entity_id": entity_id}
    )
   .opp.bus.async_fire(
        EVENT_ENTITY_REGISTRY_UPDATED,
        {"action": "create", "entity_id": untracked_entity_id},
    )
    await.opp.async_block_till_done()

   .opp.bus.async_fire(
        EVENT_ENTITY_REGISTRY_UPDATED,
        {
            "action": "update",
            "entity_id": new_entity_id,
            "old_entity_id": entity_id,
            "changes": {},
        },
    )
    await.opp.async_block_till_done()

   .opp.bus.async_fire(
        EVENT_ENTITY_REGISTRY_UPDATED, {"action": "remove", "entity_id": new_entity_id}
    )
    await.opp.async_block_till_done()

    unsub1()
    unsub2()
   .opp.bus.async_fire(
        EVENT_ENTITY_REGISTRY_UPDATED, {"action": "create", "entity_id": entity_id}
    )
   .opp.bus.async_fire(
        EVENT_ENTITY_REGISTRY_UPDATED, {"action": "create", "entity_id": new_entity_id}
    )
    await.opp.async_block_till_done()

    assert event_data[0] == {"action": "create", "entity_id": "switch.puppy_feeder"}
    assert event_data[1] == {
        "action": "update",
        "changes": {},
        "entity_id": "switch.dog_feeder",
        "old_entity_id": "switch.puppy_feeder",
    }
    assert event_data[2] == {"action": "remove", "entity_id": "switch.dog_feeder"}


async def test_async_track_entity_registry_updated_event_with_a_callback_that_throws(
   .opp,
):
    """Test tracking entity registry updates for an entity_id when one callback throws."""

    entity_id = "switch.puppy_feeder"

   .opp.states.async_set(entity_id, "on")
    await.opp.async_block_till_done()
    event_data = []

    @ha.callback
    def run_callback(event):
        event_data.append(event.data)

    @ha.callback
    def failing_callback(event):
        raise ValueError

    unsub1 =.opp.helpers.event.async_track_entity_registry_updated_event(
        entity_id, failing_callback
    )
    unsub2 =.opp.helpers.event.async_track_entity_registry_updated_event(
        entity_id, run_callback
    )
   .opp.bus.async_fire(
        EVENT_ENTITY_REGISTRY_UPDATED, {"action": "create", "entity_id": entity_id}
    )
    await.opp.async_block_till_done()
    unsub1()
    unsub2()

    assert event_data[0] == {"action": "create", "entity_id": "switch.puppy_feeder"}


async def test_async_track_entity_registry_updated_event_with_empty_list.opp):
    """Test async_track_entity_registry_updated_event passing an empty list of entities."""
    unsub_single =.opp.helpers.event.async_track_entity_registry_updated_event(
        [], ha.callback(lambda event: None)
    )
    unsub_single2 =.opp.helpers.event.async_track_entity_registry_updated_event(
        [], ha.callback(lambda event: None)
    )

    unsub_single2()
    unsub_single()
