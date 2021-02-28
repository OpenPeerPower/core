"""The tests the History component."""
# pylint: disable=protected-access,invalid-name
from copy import copy
from datetime import timedelta
import json
import unittest
from unittest.mock import patch, sentinel

from openpeerpower.components import history, recorder
from openpeerpower.components.recorder.models import process_timestamp
import openpeerpower.core as ha
from openpeerpower.helpers.json import JSONEncoder
from openpeerpower.setup import async_setup_component, setup_component
import openpeerpower.util.dt as dt_util

from tests.common import (
    get_test_open_peer_power,
    init_recorder_component,
    mock_state_change_event,
)
from tests.components.recorder.common import trigger_db_commit, wait_recording_done


class TestComponentHistory(unittest.TestCase):
    """Test History component."""

    def setUp(self):  # pylint: disable=invalid-name
        """Set up things to be run when tests are started."""
        self opp =get_test_open_peer_power()
        self.addCleanup(self.tear_down_cleanup)

    def tear_down_cleanup(self):
        """Stop everything that was started."""
        self.opp.stop()

    def init_recorder(self):
        """Initialize the recorder."""
        init_recorder_component(self.opp)
        self.opp.start()
        wait_recording_done(self.opp)

    def test_setup(self):
        """Test setup method of history."""
        config = history.CONFIG_SCHEMA(
            {
                # op.DOMAIN: {},
                history.DOMAIN: {
                    history.CONF_INCLUDE: {
                        history.CONF_DOMAINS: ["media_player"],
                        history.CONF_ENTITIES: ["thermostat.test"],
                    },
                    history.CONF_EXCLUDE: {
                        history.CONF_DOMAINS: ["thermostat"],
                        history.CONF_ENTITIES: ["media_player.test"],
                    },
                }
            }
        )
        self.init_recorder()
        assert setup_component(self.opp, history.DOMAIN, config)

    def test_get_states(self):
        """Test getting states at a specific point in time."""
        self.test_setup()
        states = []

        now = dt_util.utcnow()
        with patch(
            "openpeerpower.components.recorder.dt_util.utcnow", return_value=now
        ):
            for i in range(5):
                state = op.State(
                    "test.point_in_time_{}".format(i % 5),
                    f"State {i}",
                    {"attribute_test": i},
                )

                mock_state_change_event(self.opp, state)

                states.append(state)

            wait_recording_done(self.opp)

        future = now + timedelta(seconds=1)
        with patch(
            "openpeerpower.components.recorder.dt_util.utcnow", return_value=future
        ):
            for i in range(5):
                state = op.State(
                    "test.point_in_time_{}".format(i % 5),
                    f"State {i}",
                    {"attribute_test": i},
                )

                mock_state_change_event(self.opp, state)

            wait_recording_done(self.opp)

        # Get states returns everything before POINT
        for state1, state2 in zip(
            states,
            sorted(
                history.get_states(self.opp, future), key=lambda state: state.entity_id
            ),
        ):
            assert state1 == state2

        # Test get_state here because we have a DB setup
        assert states[0] == history.get_state(self.opp, future, states[0].entity_id)

        time_before_recorder_ran = now - timedelta(days=1000)
        assert history.get_states(self.opp, time_before_recorder_ran) == []

        assert history.get_state(self.opp, time_before_recorder_ran, "demo.id") is None

    def test_state_changes_during_period(self):
        """Test state change during period."""
        self.test_setup()
        entity_id = "media_player.test"

        def set_state(state):
            """Set the state."""
            self.opp.states.set(entity_id, state)
            wait_recording_done(self.opp)
            return self.opp.states.get(entity_id)

        start = dt_util.utcnow()
        point = start + timedelta(seconds=1)
        end = point + timedelta(seconds=1)

        with patch(
            "openpeerpower.components.recorder.dt_util.utcnow", return_value=start
        ):
            set_state("idle")
            set_state("YouTube")

        with patch(
            "openpeerpower.components.recorder.dt_util.utcnow", return_value=point
        ):
            states = [
                set_state("idle"),
                set_state("Netflix"),
                set_state("Plex"),
                set_state("YouTube"),
            ]

        with patch(
            "openpeerpower.components.recorder.dt_util.utcnow", return_value=end
        ):
            set_state("Netflix")
            set_state("Plex")

        hist = history.state_changes_during_period(self.opp, start, end, entity_id)

        assert states == hist[entity_id]

    def test_get_last_state_changes(self):
        """Test number of state changes."""
        self.test_setup()
        entity_id = "sensor.test"

        def set_state(state):
            """Set the state."""
            self.opp.states.set(entity_id, state)
            wait_recording_done(self.opp)
            return self.opp.states.get(entity_id)

        start = dt_util.utcnow() - timedelta(minutes=2)
        point = start + timedelta(minutes=1)
        point2 = point + timedelta(minutes=1)

        with patch(
            "openpeerpower.components.recorder.dt_util.utcnow", return_value=start
        ):
            set_state("1")

        states = []
        with patch(
            "openpeerpower.components.recorder.dt_util.utcnow", return_value=point
        ):
            states.append(set_state("2"))

        with patch(
            "openpeerpower.components.recorder.dt_util.utcnow", return_value=point2
        ):
            states.append(set_state("3"))

        hist = history.get_last_state_changes(self.opp, 2, entity_id)

        assert states == hist[entity_id]

    def test_ensure_state_can_be_copied(self):
        """Ensure a state can pass though copy().

        The filter integration uses copy() on states
        from history.
        """
        self.test_setup()
        entity_id = "sensor.test"

        def set_state(state):
            """Set the state."""
            self.opp.states.set(entity_id, state)
            wait_recording_done(self.opp)
            return self.opp.states.get(entity_id)

        start = dt_util.utcnow() - timedelta(minutes=2)
        point = start + timedelta(minutes=1)

        with patch(
            "openpeerpower.components.recorder.dt_util.utcnow", return_value=start
        ):
            set_state("1")

        with patch(
            "openpeerpower.components.recorder.dt_util.utcnow", return_value=point
        ):
            set_state("2")

        hist = history.get_last_state_changes(self.opp, 2, entity_id)

        assert copy(hist[entity_id][0]) == hist[entity_id][0]
        assert copy(hist[entity_id][1]) == hist[entity_id][1]

    def test_get_significant_states(self):
        """Test that only significant states are returned.

        We should get back every thermostat change that
        includes an attribute change, but only the state updates for
        media player (attribute changes are not significant and not returned).
        """
        zero, four, states = self.record_states()
        hist = history.get_significant_states(
            self.opp, zero, four, filters=history.Filters()
        )
        assert states == hist

    def test_get_significant_states_minimal_response(self):
        """Test that only significant states are returned.

        When minimal responses is set only the first and
        last states return a complete state.

        We should get back every thermostat change that
        includes an attribute change, but only the state updates for
        media player (attribute changes are not significant and not returned).
        """
        zero, four, states = self.record_states()
        hist = history.get_significant_states(
            self.opp, zero, four, filters=history.Filters(), minimal_response=True
        )

        # The second media_player.test state is reduced
        # down to last_changed and state when minimal_response
        # is set.  We use JSONEncoder to make sure that are
        # pre-encoded last_changed is always the same as what
        # will happen with encoding a native state
        input_state = states["media_player.test"][1]
        orig_last_changed = json.dumps(
            process_timestamp(input_state.last_changed),
            cls=JSONEncoder,
        ).replace('"', "")
        orig_state = input_state.state
        states["media_player.test"][1] = {
            "last_changed": orig_last_changed,
            "state": orig_state,
        }

        assert states == hist

    def test_get_significant_states_with_initial(self):
        """Test that only significant states are returned.

        We should get back every thermostat change that
        includes an attribute change, but only the state updates for
        media player (attribute changes are not significant and not returned).
        """
        zero, four, states = self.record_states()
        one = zero + timedelta(seconds=1)
        one_and_half = zero + timedelta(seconds=1.5)
        for entity_id in states:
            if entity_id == "media_player.test":
                states[entity_id] = states[entity_id][1:]
            for state in states[entity_id]:
                if state.last_changed == one:
                    state.last_changed = one_and_half

        hist = history.get_significant_states(
            self.opp,
            one_and_half,
            four,
            filters=history.Filters(),
            include_start_time_state=True,
        )
        assert states == hist

    def test_get_significant_states_without_initial(self):
        """Test that only significant states are returned.

        We should get back every thermostat change that
        includes an attribute change, but only the state updates for
        media player (attribute changes are not significant and not returned).
        """
        zero, four, states = self.record_states()
        one = zero + timedelta(seconds=1)
        one_and_half = zero + timedelta(seconds=1.5)
        for entity_id in states:
            states[entity_id] = list(
                filter(lambda s: s.last_changed != one, states[entity_id])
            )
        del states["media_player.test2"]

        hist = history.get_significant_states(
            self.opp,
            one_and_half,
            four,
            filters=history.Filters(),
            include_start_time_state=False,
        )
        assert states == hist

    def test_get_significant_states_entity_id(self):
        """Test that only significant states are returned for one entity."""
        zero, four, states = self.record_states()
        del states["media_player.test2"]
        del states["media_player.test3"]
        del states["thermostat.test"]
        del states["thermostat.test2"]
        del states["script.can_cancel_this_one"]

        hist = history.get_significant_states(
            self.opp, zero, four, ["media_player.test"], filters=history.Filters()
        )
        assert states == hist

    def test_get_significant_states_multiple_entity_ids(self):
        """Test that only significant states are returned for one entity."""
        zero, four, states = self.record_states()
        del states["media_player.test2"]
        del states["media_player.test3"]
        del states["thermostat.test2"]
        del states["script.can_cancel_this_one"]

        hist = history.get_significant_states(
            self.opp,
            zero,
            four,
            ["media_player.test", "thermostat.test"],
            filters=history.Filters(),
        )
        assert states == hist

    def test_get_significant_states_exclude_domain(self):
        """Test if significant states are returned when excluding domains.

        We should get back every thermostat change that includes an attribute
        change, but no media player changes.
        """
        zero, four, states = self.record_states()
        del states["media_player.test"]
        del states["media_player.test2"]
        del states["media_player.test3"]

        config = history.CONFIG_SCHEMA(
            {
                op.DOMAIN: {},
                history.DOMAIN: {
                    history.CONF_EXCLUDE: {history.CONF_DOMAINS: ["media_player"]}
                },
            }
        )
        self.check_significant_states(zero, four, states, config)

    def test_get_significant_states_exclude_entity(self):
        """Test if significant states are returned when excluding entities.

        We should get back every thermostat and script changes, but no media
        player changes.
        """
        zero, four, states = self.record_states()
        del states["media_player.test"]

        config = history.CONFIG_SCHEMA(
            {
                op.DOMAIN: {},
                history.DOMAIN: {
                    history.CONF_EXCLUDE: {history.CONF_ENTITIES: ["media_player.test"]}
                },
            }
        )
        self.check_significant_states(zero, four, states, config)

    def test_get_significant_states_exclude(self):
        """Test significant states when excluding entities and domains.

        We should not get back every thermostat and media player test changes.
        """
        zero, four, states = self.record_states()
        del states["media_player.test"]
        del states["thermostat.test"]
        del states["thermostat.test2"]

        config = history.CONFIG_SCHEMA(
            {
                op.DOMAIN: {},
                history.DOMAIN: {
                    history.CONF_EXCLUDE: {
                        history.CONF_DOMAINS: ["thermostat"],
                        history.CONF_ENTITIES: ["media_player.test"],
                    }
                },
            }
        )
        self.check_significant_states(zero, four, states, config)

    def test_get_significant_states_exclude_include_entity(self):
        """Test significant states when excluding domains and include entities.

        We should not get back every thermostat and media player test changes.
        """
        zero, four, states = self.record_states()
        del states["media_player.test2"]
        del states["media_player.test3"]
        del states["thermostat.test"]
        del states["thermostat.test2"]
        del states["script.can_cancel_this_one"]

        config = history.CONFIG_SCHEMA(
            {
                op.DOMAIN: {},
                history.DOMAIN: {
                    history.CONF_INCLUDE: {
                        history.CONF_ENTITIES: ["media_player.test", "thermostat.test"]
                    },
                    history.CONF_EXCLUDE: {history.CONF_DOMAINS: ["thermostat"]},
                },
            }
        )
        self.check_significant_states(zero, four, states, config)

    def test_get_significant_states_include_domain(self):
        """Test if significant states are returned when including domains.

        We should get back every thermostat and script changes, but no media
        player changes.
        """
        zero, four, states = self.record_states()
        del states["media_player.test"]
        del states["media_player.test2"]
        del states["media_player.test3"]

        config = history.CONFIG_SCHEMA(
            {
                op.DOMAIN: {},
                history.DOMAIN: {
                    history.CONF_INCLUDE: {
                        history.CONF_DOMAINS: ["thermostat", "script"]
                    }
                },
            }
        )
        self.check_significant_states(zero, four, states, config)

    def test_get_significant_states_include_entity(self):
        """Test if significant states are returned when including entities.

        We should only get back changes of the media_player.test entity.
        """
        zero, four, states = self.record_states()
        del states["media_player.test2"]
        del states["media_player.test3"]
        del states["thermostat.test"]
        del states["thermostat.test2"]
        del states["script.can_cancel_this_one"]

        config = history.CONFIG_SCHEMA(
            {
                op.DOMAIN: {},
                history.DOMAIN: {
                    history.CONF_INCLUDE: {history.CONF_ENTITIES: ["media_player.test"]}
                },
            }
        )
        self.check_significant_states(zero, four, states, config)

    def test_get_significant_states_include(self):
        """Test significant states when including domains and entities.

        We should only get back changes of the media_player.test entity and the
        thermostat domain.
        """
        zero, four, states = self.record_states()
        del states["media_player.test2"]
        del states["media_player.test3"]
        del states["script.can_cancel_this_one"]

        config = history.CONFIG_SCHEMA(
            {
                op.DOMAIN: {},
                history.DOMAIN: {
                    history.CONF_INCLUDE: {
                        history.CONF_DOMAINS: ["thermostat"],
                        history.CONF_ENTITIES: ["media_player.test"],
                    }
                },
            }
        )
        self.check_significant_states(zero, four, states, config)

    def test_get_significant_states_include_exclude_domain(self):
        """Test if significant states when excluding and including domains.

        We should not get back any changes since we include only the
        media_player domain but also exclude it.
        """
        zero, four, states = self.record_states()
        del states["media_player.test"]
        del states["media_player.test2"]
        del states["media_player.test3"]
        del states["thermostat.test"]
        del states["thermostat.test2"]
        del states["script.can_cancel_this_one"]

        config = history.CONFIG_SCHEMA(
            {
                op.DOMAIN: {},
                history.DOMAIN: {
                    history.CONF_INCLUDE: {history.CONF_DOMAINS: ["media_player"]},
                    history.CONF_EXCLUDE: {history.CONF_DOMAINS: ["media_player"]},
                },
            }
        )
        self.check_significant_states(zero, four, states, config)

    def test_get_significant_states_include_exclude_entity(self):
        """Test if significant states when excluding and including domains.

        We should not get back any changes since we include only
        media_player.test but also exclude it.
        """
        zero, four, states = self.record_states()
        del states["media_player.test"]
        del states["media_player.test2"]
        del states["media_player.test3"]
        del states["thermostat.test"]
        del states["thermostat.test2"]
        del states["script.can_cancel_this_one"]

        config = history.CONFIG_SCHEMA(
            {
                op.DOMAIN: {},
                history.DOMAIN: {
                    history.CONF_INCLUDE: {
                        history.CONF_ENTITIES: ["media_player.test"]
                    },
                    history.CONF_EXCLUDE: {
                        history.CONF_ENTITIES: ["media_player.test"]
                    },
                },
            }
        )
        self.check_significant_states(zero, four, states, config)

    def test_get_significant_states_include_exclude(self):
        """Test if significant states when in/excluding domains and entities.

        We should only get back changes of the media_player.test2 entity.
        """
        zero, four, states = self.record_states()
        del states["media_player.test"]
        del states["thermostat.test"]
        del states["thermostat.test2"]
        del states["script.can_cancel_this_one"]

        config = history.CONFIG_SCHEMA(
            {
                op.DOMAIN: {},
                history.DOMAIN: {
                    history.CONF_INCLUDE: {
                        history.CONF_DOMAINS: ["media_player"],
                        history.CONF_ENTITIES: ["thermostat.test"],
                    },
                    history.CONF_EXCLUDE: {
                        history.CONF_DOMAINS: ["thermostat"],
                        history.CONF_ENTITIES: ["media_player.test"],
                    },
                },
            }
        )
        self.check_significant_states(zero, four, states, config)

    def test_get_significant_states_are_ordered(self):
        """Test order of results from get_significant_states.

        When entity ids are given, the results should be returned with the data
        in the same order.
        """
        zero, four, states = self.record_states()
        entity_ids = ["media_player.test", "media_player.test2"]
        hist = history.get_significant_states(
            self.opp, zero, four, entity_ids, filters=history.Filters()
        )
        assert list(hist.keys()) == entity_ids
        entity_ids = ["media_player.test2", "media_player.test"]
        hist = history.get_significant_states(
            self.opp, zero, four, entity_ids, filters=history.Filters()
        )
        assert list(hist.keys()) == entity_ids

    def test_get_significant_states_only(self):
        """Test significant states when significant_states_only is set."""
        self.test_setup()
        entity_id = "sensor.test"

        def set_state(state, **kwargs):
            """Set the state."""
            self.opp.states.set(entity_id, state, **kwargs)
            wait_recording_done(self.opp)
            return self.opp.states.get(entity_id)

        start = dt_util.utcnow() - timedelta(minutes=4)
        points = []
        for i in range(1, 4):
            points.append(start + timedelta(minutes=i))

        states = []
        with patch(
            "openpeerpower.components.recorder.dt_util.utcnow", return_value=start
        ):
            set_state("123", attributes={"attribute": 10.64})

        with patch(
            "openpeerpower.components.recorder.dt_util.utcnow", return_value=points[0]
        ):
            # Attributes are different, state not
            states.append(set_state("123", attributes={"attribute": 21.42}))

        with patch(
            "openpeerpower.components.recorder.dt_util.utcnow", return_value=points[1]
        ):
            # state is different, attributes not
            states.append(set_state("32", attributes={"attribute": 21.42}))

        with patch(
            "openpeerpower.components.recorder.dt_util.utcnow", return_value=points[2]
        ):
            # everything is different
            states.append(set_state("412", attributes={"attribute": 54.23}))

        hist = history.get_significant_states(
            self.opp, start, significant_changes_only=True
        )

        assert len(hist[entity_id]) == 2
        assert states[0] not in hist[entity_id]
        assert states[1] in hist[entity_id]
        assert states[2] in hist[entity_id]

        hist = history.get_significant_states(
            self.opp, start, significant_changes_only=False
        )

        assert len(hist[entity_id]) == 3
        assert states == hist[entity_id]

    def check_significant_states(self, zero, four, states, config):
        """Check if significant states are retrieved."""
        filters = history.Filters()
        exclude = config[history.DOMAIN].get(history.CONF_EXCLUDE)
        if exclude:
            filters.excluded_entities = exclude.get(history.CONF_ENTITIES, [])
            filters.excluded_domains = exclude.get(history.CONF_DOMAINS, [])
        include = config[history.DOMAIN].get(history.CONF_INCLUDE)
        if include:
            filters.included_entities = include.get(history.CONF_ENTITIES, [])
            filters.included_domains = include.get(history.CONF_DOMAINS, [])

        hist = history.get_significant_states(self.opp, zero, four, filters=filters)
        assert states == hist

    def record_states(self):
        """Record some test states.

        We inject a bunch of state updates from media player, zone and
        thermostat.
        """
        self.test_setup()
        mp = "media_player.test"
        mp2 = "media_player.test2"
        mp3 = "media_player.test3"
        therm = "thermostat.test"
        therm2 = "thermostat.test2"
        zone = "zone.home"
        script_c = "script.can_cancel_this_one"

        def set_state(entity_id, state, **kwargs):
            """Set the state."""
            self.opp.states.set(entity_id, state, **kwargs)
            wait_recording_done(self.opp)
            return self.opp.states.get(entity_id)

        zero = dt_util.utcnow()
        one = zero + timedelta(seconds=1)
        two = one + timedelta(seconds=1)
        three = two + timedelta(seconds=1)
        four = three + timedelta(seconds=1)

        states = {therm: [], therm2: [], mp: [], mp2: [], mp3: [], script_c: []}
        with patch(
            "openpeerpower.components.recorder.dt_util.utcnow", return_value=one
        ):
            states[mp].append(
                set_state(mp, "idle", attributes={"media_title": str(sentinel.mt1)})
            )
            states[mp].append(
                set_state(mp, "YouTube", attributes={"media_title": str(sentinel.mt2)})
            )
            states[mp2].append(
                set_state(mp2, "YouTube", attributes={"media_title": str(sentinel.mt2)})
            )
            states[mp3].append(
                set_state(mp3, "idle", attributes={"media_title": str(sentinel.mt1)})
            )
            states[therm].append(
                set_state(therm, 20, attributes={"current_temperature": 19.5})
            )

        with patch(
            "openpeerpower.components.recorder.dt_util.utcnow", return_value=two
        ):
            # This state will be skipped only different in time
            set_state(mp, "YouTube", attributes={"media_title": str(sentinel.mt3)})
            # This state will be skipped because domain is excluded
            set_state(zone, "zoning")
            states[script_c].append(
                set_state(script_c, "off", attributes={"can_cancel": True})
            )
            states[therm].append(
                set_state(therm, 21, attributes={"current_temperature": 19.8})
            )
            states[therm2].append(
                set_state(therm2, 20, attributes={"current_temperature": 19})
            )

        with patch(
            "openpeerpower.components.recorder.dt_util.utcnow", return_value=three
        ):
            states[mp].append(
                set_state(mp, "Netflix", attributes={"media_title": str(sentinel.mt4)})
            )
            states[mp3].append(
                set_state(mp3, "Netflix", attributes={"media_title": str(sentinel.mt3)})
            )
            # Attributes changed even though state is the same
            states[therm].append(
                set_state(therm, 21, attributes={"current_temperature": 20})
            )

        return zero, four, states


async def test_fetch_period_api(opp, opp_client):
    """Test the fetch period view for history."""
    await opp.async_add_executor_job(init_recorder_component, opp)
    await async_setup_component(opp, "history", {})
    await opp.async_add_executor_job.opp.data[recorder.DATA_INSTANCE].block_till_done)
    client = await opp_client()
    response = await client.get(f"/api/history/period/{dt_util.utcnow().isoformat()}")
    assert response.status == 200


async def test_fetch_period_api_with_use_include_order(opp, opp_client):
    """Test the fetch period view for history with include order."""
    await opp.async_add_executor_job(init_recorder_component, opp)
    await async_setup_component(
        opp, "history", {history.DOMAIN: {history.CONF_ORDER: True}}
    )
    await opp.async_add_executor_job.opp.data[recorder.DATA_INSTANCE].block_till_done)
    client = await opp_client()
    response = await client.get(f"/api/history/period/{dt_util.utcnow().isoformat()}")
    assert response.status == 200


async def test_fetch_period_api_with_minimal_response(opp, opp_client):
    """Test the fetch period view for history with minimal_response."""
    await opp.async_add_executor_job(init_recorder_component, opp)
    await async_setup_component(opp, "history", {})
    await opp.async_add_executor_job.opp.data[recorder.DATA_INSTANCE].block_till_done)
    client = await opp_client()
    response = await client.get(
        f"/api/history/period/{dt_util.utcnow().isoformat()}?minimal_response"
    )
    assert response.status == 200


async def test_fetch_period_api_with_no_timestamp(opp, opp_client):
    """Test the fetch period view for history with no timestamp."""
    await opp.async_add_executor_job(init_recorder_component, opp)
    await async_setup_component(opp, "history", {})
    await opp.async_add_executor_job.opp.data[recorder.DATA_INSTANCE].block_till_done)
    client = await opp_client()
    response = await client.get("/api/history/period")
    assert response.status == 200


async def test_fetch_period_api_with_include_order(opp, opp_client):
    """Test the fetch period view for history."""
    await opp.async_add_executor_job(init_recorder_component, opp)
    await async_setup_component(
        opp,
        "history",
        {
            "history": {
                "use_include_order": True,
                "include": {"entities": ["light.kitchen"]},
            }
        },
    )
    await opp.async_add_executor_job.opp.data[recorder.DATA_INSTANCE].block_till_done)
    client = await opp_client()
    response = await client.get(
        f"/api/history/period/{dt_util.utcnow().isoformat()}",
        params={"filter_entity_id": "non.existing,something.else"},
    )
    assert response.status == 200


async def test_fetch_period_api_with_entity_glob_include(opp, opp_client):
    """Test the fetch period view for history."""
    await opp.async_add_executor_job(init_recorder_component, opp)
    await async_setup_component(
        opp,
        "history",
        {
            "history": {
                "include": {"entity_globs": ["light.k*"]},
            }
        },
    )
    await opp.async_add_executor_job.opp.data[recorder.DATA_INSTANCE].block_till_done)
    opp.states.async_set("light.kitchen", "on")
    opp.states.async_set("light.cow", "on")
    opp.states.async_set("light.nomatch", "on")

    await opp.async_block_till_done()

    await opp.async_add_executor_job(trigger_db_commit, opp)
    await opp.async_block_till_done()
    await opp.async_add_executor_job.opp.data[recorder.DATA_INSTANCE].block_till_done)

    client = await opp_client()
    response = await client.get(
        f"/api/history/period/{dt_util.utcnow().isoformat()}",
    )
    assert response.status == 200
    response_json = await response.json()
    assert response_json[0][0]["entity_id"] == "light.kitchen"


async def test_fetch_period_api_with_entity_glob_exclude(opp, opp_client):
    """Test the fetch period view for history."""
    await opp.async_add_executor_job(init_recorder_component, opp)
    await async_setup_component(
        opp,
        "history",
        {
            "history": {
                "exclude": {
                    "entity_globs": ["light.k*"],
                    "domains": "switch",
                    "entities": "media_player.test",
                },
            }
        },
    )
    await opp.async_add_executor_job.opp.data[recorder.DATA_INSTANCE].block_till_done)
    opp.states.async_set("light.kitchen", "on")
    opp.states.async_set("light.cow", "on")
    opp.states.async_set("light.match", "on")
    opp.states.async_set("switch.match", "on")
    opp.states.async_set("media_player.test", "on")

    await opp.async_block_till_done()

    await opp.async_add_executor_job(trigger_db_commit, opp)
    await opp.async_block_till_done()
    await opp.async_add_executor_job.opp.data[recorder.DATA_INSTANCE].block_till_done)

    client = await opp_client()
    response = await client.get(
        f"/api/history/period/{dt_util.utcnow().isoformat()}",
    )
    assert response.status == 200
    response_json = await response.json()
    assert len(response_json) == 2
    assert response_json[0][0]["entity_id"] == "light.cow"
    assert response_json[1][0]["entity_id"] == "light.match"


async def test_fetch_period_api_with_entity_glob_include_and_exclude(opp, opp_client):
    """Test the fetch period view for history."""
    await opp.async_add_executor_job(init_recorder_component, opp)
    await async_setup_component(
        opp,
        "history",
        {
            "history": {
                "exclude": {
                    "entity_globs": ["light.many*"],
                },
                "include": {
                    "entity_globs": ["light.m*"],
                    "domains": "switch",
                    "entities": "media_player.test",
                },
            }
        },
    )
    await opp.async_add_executor_job.opp.data[recorder.DATA_INSTANCE].block_till_done)
    opp.states.async_set("light.kitchen", "on")
    opp.states.async_set("light.cow", "on")
    opp.states.async_set("light.match", "on")
    opp.states.async_set("light.many_state_changes", "on")
    opp.states.async_set("switch.match", "on")
    opp.states.async_set("media_player.test", "on")

    await opp.async_block_till_done()

    await opp.async_add_executor_job(trigger_db_commit, opp)
    await opp.async_block_till_done()
    await opp.async_add_executor_job.opp.data[recorder.DATA_INSTANCE].block_till_done)

    client = await opp_client()
    response = await client.get(
        f"/api/history/period/{dt_util.utcnow().isoformat()}",
    )
    assert response.status == 200
    response_json = await response.json()
    assert len(response_json) == 3
    assert response_json[0][0]["entity_id"] == "light.match"
    assert response_json[1][0]["entity_id"] == "media_player.test"
    assert response_json[2][0]["entity_id"] == "switch.match"


async def test_entity_ids_limit_via_api(opp, opp_client):
    """Test limiting history to entity_ids."""
    await opp.async_add_executor_job(init_recorder_component, opp)
    await async_setup_component(
        opp,
        "history",
        {"history": {}},
    )
    await opp.async_add_executor_job.opp.data[recorder.DATA_INSTANCE].block_till_done)
    opp.states.async_set("light.kitchen", "on")
    opp.states.async_set("light.cow", "on")
    opp.states.async_set("light.nomatch", "on")

    await opp.async_block_till_done()

    await opp.async_add_executor_job(trigger_db_commit, opp)
    await opp.async_block_till_done()
    await opp.async_add_executor_job.opp.data[recorder.DATA_INSTANCE].block_till_done)

    client = await opp_client()
    response = await client.get(
        f"/api/history/period/{dt_util.utcnow().isoformat()}?filter_entity_id=light.kitchen,light.cow",
    )
    assert response.status == 200
    response_json = await response.json()
    assert len(response_json) == 2
    assert response_json[0][0]["entity_id"] == "light.kitchen"
    assert response_json[1][0]["entity_id"] == "light.cow"


async def test_entity_ids_limit_via_api_with_skip_initial_state(opp, opp_client):
    """Test limiting history to entity_ids with skip_initial_state."""
    await opp.async_add_executor_job(init_recorder_component, opp)
    await async_setup_component(
        opp,
        "history",
        {"history": {}},
    )
    await opp.async_add_executor_job.opp.data[recorder.DATA_INSTANCE].block_till_done)
    opp.states.async_set("light.kitchen", "on")
    opp.states.async_set("light.cow", "on")
    opp.states.async_set("light.nomatch", "on")

    await opp.async_block_till_done()

    await opp.async_add_executor_job(trigger_db_commit, opp)
    await opp.async_block_till_done()
    await opp.async_add_executor_job.opp.data[recorder.DATA_INSTANCE].block_till_done)

    client = await opp_client()
    response = await client.get(
        f"/api/history/period/{dt_util.utcnow().isoformat()}?filter_entity_id=light.kitchen,light.cow&skip_initial_state",
    )
    assert response.status == 200
    response_json = await response.json()
    assert len(response_json) == 0

    when = dt_util.utcnow() - timedelta(minutes=1)
    response = await client.get(
        f"/api/history/period/{when.isoformat()}?filter_entity_id=light.kitchen,light.cow&skip_initial_state",
    )
    assert response.status == 200
    response_json = await response.json()
    assert len(response_json) == 2
    assert response_json[0][0]["entity_id"] == "light.kitchen"
    assert response_json[1][0]["entity_id"] == "light.cow"
