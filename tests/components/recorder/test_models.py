"""The tests for the Recorder component."""
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from openpeerpower.components.recorder.models import (
    Base,
    Events,
    RecorderRuns,
    States,
    process_timestamp,
    process_timestamp_to_utc_isoformat,
)
from openpeerpower.const import EVENT_STATE_CHANGED
import openpeerpower.core as ha
from openpeerpower.exceptions import InvalidEntityFormatError
from openpeerpower.util import dt
import openpeerpower.util.dt as dt_util


def test_from_event_to_db_event():
    """Test converting event to db event."""
    event = ha.Event("test_event", {"some_data": 15})
    assert event == Events.from_event(event).to_native()


def test_from_event_to_db_state():
    """Test converting event to db state."""
    state = ha.State("sensor.temperature", "18")
    event = ha.Event(
        EVENT_STATE_CHANGED,
        {"entity_id": "sensor.temperature", "old_state": None, "new_state": state},
        context=state.context,
    )
    # We don't restore context unless we need it by joining the
    # events table on the event_id for state_changed events
    state.context = ha.Context(id=None)
    assert state == States.from_event(event).to_native()


def test_from_event_to_delete_state():
    """Test converting deleting state event to db state."""
    event = ha.Event(
        EVENT_STATE_CHANGED,
        {
            "entity_id": "sensor.temperature",
            "old_state": ha.State("sensor.temperature", "18"),
            "new_state": None,
        },
    )
    db_state = States.from_event(event)

    assert db_state.entity_id == "sensor.temperature"
    assert db_state.domain == "sensor"
    assert db_state.state == ""
    assert db_state.last_changed == event.time_fired
    assert db_state.last_updated == event.time_fired


def test_entity_ids():
    """Test if entity ids helper method works."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    session = scoped_session(session_factory)
    session.query(Events).delete()
    session.query(States).delete()
    session.query(RecorderRuns).delete()

    run = RecorderRuns(
        start=datetime(2016, 7, 9, 11, 0, 0, tzinfo=dt.UTC),
        end=datetime(2016, 7, 9, 23, 0, 0, tzinfo=dt.UTC),
        closed_incorrect=False,
        created=datetime(2016, 7, 9, 11, 0, 0, tzinfo=dt.UTC),
    )

    session.add(run)
    session.commit()

    before_run = datetime(2016, 7, 9, 8, 0, 0, tzinfo=dt.UTC)
    in_run = datetime(2016, 7, 9, 13, 0, 0, tzinfo=dt.UTC)
    in_run2 = datetime(2016, 7, 9, 15, 0, 0, tzinfo=dt.UTC)
    in_run3 = datetime(2016, 7, 9, 18, 0, 0, tzinfo=dt.UTC)
    after_run = datetime(2016, 7, 9, 23, 30, 0, tzinfo=dt.UTC)

    assert run.to_native() == run
    assert run.entity_ids() == []

    session.add(
        States(
            entity_id="sensor.temperature",
            state="20",
            last_changed=before_run,
            last_updated=before_run,
        )
    )
    session.add(
        States(
            entity_id="sensor.sound",
            state="10",
            last_changed=after_run,
            last_updated=after_run,
        )
    )

    session.add(
        States(
            entity_id="sensor.humidity",
            state="76",
            last_changed=in_run,
            last_updated=in_run,
        )
    )
    session.add(
        States(
            entity_id="sensor.lux",
            state="5",
            last_changed=in_run3,
            last_updated=in_run3,
        )
    )

    assert sorted(run.entity_ids()) == ["sensor.humidity", "sensor.lux"]
    assert run.entity_ids(in_run2) == ["sensor.humidity"]


def test_states_from_native_invalid_entity_id():
    """Test loading a state from an invalid entity ID."""
    state = States()
    state.entity_id = "test.invalid__id"
    state.attributes = "{}"
    with pytest.raises(InvalidEntityFormatError):
        state = state.to_native()

    state = state.to_native(validate_entity_id=False)
    assert state.entity_id == "test.invalid__id"


async def test_process_timestamp():
    """Test processing time stamp to UTC."""
    datetime_with_tzinfo = datetime(2016, 7, 9, 11, 0, 0, tzinfo=dt.UTC)
    datetime_without_tzinfo = datetime(2016, 7, 9, 11, 0, 0)
    est = dt_util.get_time_zone("US/Eastern")
    datetime_est_timezone = datetime(2016, 7, 9, 11, 0, 0, tzinfo=est)
    nst = dt_util.get_time_zone("Canada/Newfoundland")
    datetime_nst_timezone = datetime(2016, 7, 9, 11, 0, 0, tzinfo=nst)
    hst = dt_util.get_time_zone("US/Hawaii")
    datetime_hst_timezone = datetime(2016, 7, 9, 11, 0, 0, tzinfo=hst)

    assert process_timestamp(datetime_with_tzinfo) == datetime(
        2016, 7, 9, 11, 0, 0, tzinfo=dt.UTC
    )
    assert process_timestamp(datetime_without_tzinfo) == datetime(
        2016, 7, 9, 11, 0, 0, tzinfo=dt.UTC
    )
    assert process_timestamp(datetime_est_timezone) == datetime(
        2016, 7, 9, 15, 0, tzinfo=dt.UTC
    )
    assert process_timestamp(datetime_nst_timezone) == datetime(
        2016, 7, 9, 13, 30, tzinfo=dt.UTC
    )
    assert process_timestamp(datetime_hst_timezone) == datetime(
        2016, 7, 9, 21, 0, tzinfo=dt.UTC
    )
    assert process_timestamp(None) is None


async def test_process_timestamp_to_utc_isoformat():
    """Test processing time stamp to UTC isoformat."""
    datetime_with_tzinfo = datetime(2016, 7, 9, 11, 0, 0, tzinfo=dt.UTC)
    datetime_without_tzinfo = datetime(2016, 7, 9, 11, 0, 0)
    est = dt_util.get_time_zone("US/Eastern")
    datetime_est_timezone = datetime(2016, 7, 9, 11, 0, 0, tzinfo=est)
    est = dt_util.get_time_zone("US/Eastern")
    datetime_est_timezone = datetime(2016, 7, 9, 11, 0, 0, tzinfo=est)
    nst = dt_util.get_time_zone("Canada/Newfoundland")
    datetime_nst_timezone = datetime(2016, 7, 9, 11, 0, 0, tzinfo=nst)
    hst = dt_util.get_time_zone("US/Hawaii")
    datetime_hst_timezone = datetime(2016, 7, 9, 11, 0, 0, tzinfo=hst)

    assert (
        process_timestamp_to_utc_isoformat(datetime_with_tzinfo)
        == "2016-07-09T11:00:00+00:00"
    )
    assert (
        process_timestamp_to_utc_isoformat(datetime_without_tzinfo)
        == "2016-07-09T11:00:00+00:00"
    )
    assert (
        process_timestamp_to_utc_isoformat(datetime_est_timezone)
        == "2016-07-09T15:00:00+00:00"
    )
    assert (
        process_timestamp_to_utc_isoformat(datetime_nst_timezone)
        == "2016-07-09T13:30:00+00:00"
    )
    assert (
        process_timestamp_to_utc_isoformat(datetime_hst_timezone)
        == "2016-07-09T21:00:00+00:00"
    )
    assert process_timestamp_to_utc_isoformat(None) is None


async def test_event_to_db_model():
    """Test we can round trip Event conversion."""
    event = ha.Event(
        "state_changed", {"some": "attr"}, ha.EventOrigin.local, dt_util.utcnow()
    )
    native = Events.from_event(event).to_native()
    assert native == event

    native = Events.from_event(event, event_data="{}").to_native()
    event.data = {}
    assert native == event
