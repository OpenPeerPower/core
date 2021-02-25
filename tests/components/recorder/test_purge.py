"""Test data purging."""
from datetime import datetime, timedelta
import json
from unittest.mock import patch

from openpeerpower.components import recorder
from openpeerpower.components.recorder.const import DATA_INSTANCE
from openpeerpower.components.recorder.models import Events, RecorderRuns, States
from openpeerpower.components.recorder.purge import purge_old_data
from openpeerpower.components.recorder.util import session_scope
from openpeerpower.util import dt as dt_util

from .common import wait_recording_done


def test_purge_old_states(opp, opp_recorder):
    """Test deleting old states."""
   opp =  opp_recorder()
    _add_test_states.opp)

    # make sure we start with 6 states
    with session_scope.opp.opp) as session:
        states = session.query(States)
        assert states.count() == 6

        # run purge_old_data()
        finished = purge_old_data.opp.data[DATA_INSTANCE], 4, repack=False)
        assert not finished
        assert states.count() == 4

        finished = purge_old_data.opp.data[DATA_INSTANCE], 4, repack=False)
        assert not finished
        assert states.count() == 2

        finished = purge_old_data.opp.data[DATA_INSTANCE], 4, repack=False)
        assert finished
        assert states.count() == 2


def test_purge_old_events(opp, opp_recorder):
    """Test deleting old events."""
   opp =  opp_recorder()
    _add_test_events.opp)

    with session_scope.opp.opp) as session:
        events = session.query(Events).filter(Events.event_type.like("EVENT_TEST%"))
        assert events.count() == 6

        # run purge_old_data()
        finished = purge_old_data.opp.data[DATA_INSTANCE], 4, repack=False)
        assert not finished
        assert events.count() == 4

        finished = purge_old_data.opp.data[DATA_INSTANCE], 4, repack=False)
        assert not finished
        assert events.count() == 2

        # we should only have 2 events left
        finished = purge_old_data.opp.data[DATA_INSTANCE], 4, repack=False)
        assert finished
        assert events.count() == 2


def test_purge_old_recorder_runs(opp, opp_recorder):
    """Test deleting old recorder runs keeps current run."""
   opp =  opp_recorder()
    _add_test_recorder_runs.opp)

    # make sure we start with 7 recorder runs
    with session_scope.opp.opp) as session:
        recorder_runs = session.query(RecorderRuns)
        assert recorder_runs.count() == 7

        # run purge_old_data()
        finished = purge_old_data.opp.data[DATA_INSTANCE], 0, repack=False)
        assert finished
        assert recorder_runs.count() == 1


def test_purge_method(opp, opp_recorder):
    """Test purge method."""
   opp =  opp_recorder()
    service_data = {"keep_days": 4}
    _add_test_events.opp)
    _add_test_states.opp)
    _add_test_recorder_runs.opp)

    # make sure we start with 6 states
    with session_scope.opp.opp) as session:
        states = session.query(States)
        assert states.count() == 6

        events = session.query(Events).filter(Events.event_type.like("EVENT_TEST%"))
        assert events.count() == 6

        recorder_runs = session.query(RecorderRuns)
        assert recorder_runs.count() == 7

        opp.data[DATA_INSTANCE].block_till_done()
        wait_recording_done.opp)

        # run purge method - no service data, use defaults
        opp.services.call("recorder", "purge")
        opp.block_till_done()

        # Small wait for recorder thread
        opp.data[DATA_INSTANCE].block_till_done()
        wait_recording_done.opp)

        # only purged old events
        assert states.count() == 4
        assert events.count() == 4

        # run purge method - correct service data
        opp.services.call("recorder", "purge", service_data=service_data)
        opp.block_till_done()

        # Small wait for recorder thread
        opp.data[DATA_INSTANCE].block_till_done()
        wait_recording_done.opp)

        # we should only have 2 states left after purging
        assert states.count() == 2

        # now we should only have 2 events left
        assert events.count() == 2

        # now we should only have 3 recorder runs left
        assert recorder_runs.count() == 3

        assert not ("EVENT_TEST_PURGE" in (event.event_type for event in events.all()))

        # run purge method - correct service data, with repack
        with patch("openpeerpower.components.recorder.purge._LOGGER") as mock_logger:
            service_data["repack"] = True
            opp.services.call("recorder", "purge", service_data=service_data)
            opp.block_till_done()
            opp.data[DATA_INSTANCE].block_till_done()
            wait_recording_done.opp)
            assert (
                mock_logger.debug.mock_calls[5][1][0]
                == "Vacuuming SQL DB to free space"
            )


def _add_test_states.opp):
    """Add multiple states to the db for testing."""
    now = datetime.now()
    five_days_ago = now - timedelta(days=5)
    eleven_days_ago = now - timedelta(days=11)
    attributes = {"test_attr": 5, "test_attr_10": "nice"}

    opp.block_till_done()
    opp.data[DATA_INSTANCE].block_till_done()
    wait_recording_done.opp)

    with recorder.session_scope.opp.opp) as session:
        for event_id in range(6):
            if event_id < 2:
                timestamp = eleven_days_ago
                state = "autopurgeme"
            elif event_id < 4:
                timestamp = five_days_ago
                state = "purgeme"
            else:
                timestamp = now
                state = "dontpurgeme"

            session.add(
                States(
                    entity_id="test.recorder2",
                    domain="sensor",
                    state=state,
                    attributes=json.dumps(attributes),
                    last_changed=timestamp,
                    last_updated=timestamp,
                    created=timestamp,
                    event_id=event_id + 1000,
                )
            )


def _add_test_events.opp):
    """Add a few events for testing."""
    now = datetime.now()
    five_days_ago = now - timedelta(days=5)
    eleven_days_ago = now - timedelta(days=11)
    event_data = {"test_attr": 5, "test_attr_10": "nice"}

    opp.block_till_done()
    opp.data[DATA_INSTANCE].block_till_done()
    wait_recording_done.opp)

    with recorder.session_scope.opp.opp) as session:
        for event_id in range(6):
            if event_id < 2:
                timestamp = eleven_days_ago
                event_type = "EVENT_TEST_AUTOPURGE"
            elif event_id < 4:
                timestamp = five_days_ago
                event_type = "EVENT_TEST_PURGE"
            else:
                timestamp = now
                event_type = "EVENT_TEST"

            session.add(
                Events(
                    event_type=event_type,
                    event_data=json.dumps(event_data),
                    origin="LOCAL",
                    created=timestamp,
                    time_fired=timestamp,
                )
            )


def _add_test_recorder_runs.opp):
    """Add a few recorder_runs for testing."""
    now = datetime.now()
    five_days_ago = now - timedelta(days=5)
    eleven_days_ago = now - timedelta(days=11)

    opp.block_till_done()
    opp.data[DATA_INSTANCE].block_till_done()
    wait_recording_done.opp)

    with recorder.session_scope.opp.opp) as session:
        for rec_id in range(6):
            if rec_id < 2:
                timestamp = eleven_days_ago
            elif rec_id < 4:
                timestamp = five_days_ago
            else:
                timestamp = now

            session.add(
                RecorderRuns(
                    start=timestamp,
                    created=dt_util.utcnow(),
                    end=timestamp + timedelta(days=1),
                )
            )
