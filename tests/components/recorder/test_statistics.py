"""The tests for sensor recorder platform."""
# pylint: disable=protected-access,invalid-name
from datetime import timedelta
from unittest.mock import patch, sentinel

from pytest import approx

from openpeerpower.components.recorder import history
from openpeerpower.components.recorder.const import DATA_INSTANCE
from openpeerpower.components.recorder.models import process_timestamp_to_utc_isoformat
from openpeerpower.components.recorder.statistics import statistics_during_period
from openpeerpower.setup import setup_component
import openpeerpower.util.dt as dt_util

from tests.components.recorder.common import wait_recording_done


def test_compile_hourly_statistics(opp_recorder):
    """Test compiling hourly statistics."""
    opp = opp_recorder()
    recorder = opp.data[DATA_INSTANCE]
    setup_component(opp, "sensor", {})
    zero, four, states = record_states(opp)
    hist = history.get_significant_states(opp, zero, four)
    assert dict(states) == dict(hist)

    recorder.do_adhoc_statistics(period="hourly", start=zero)
    wait_recording_done(opp)
    stats = statistics_during_period(opp, zero)
    assert stats == {
        "sensor.test1": [
            {
                "statistic_id": "sensor.test1",
                "start": process_timestamp_to_utc_isoformat(zero),
                "mean": approx(14.915254237288135),
                "min": approx(10.0),
                "max": approx(20.0),
                "last_reset": None,
                "state": None,
                "sum": None,
            }
        ]
    }


def record_states(opp):
    """Record some test states.

    We inject a bunch of state updates temperature sensors.
    """
    mp = "media_player.test"
    sns1 = "sensor.test1"
    sns2 = "sensor.test2"
    sns3 = "sensor.test3"
    sns1_attr = {"device_class": "temperature", "state_class": "measurement"}
    sns2_attr = {"device_class": "temperature"}
    sns3_attr = {}

    def set_state(entity_id, state, **kwargs):
        """Set the state."""
        opp.states.set(entity_id, state, **kwargs)
        wait_recording_done(opp)
        return opp.states.get(entity_id)

    zero = dt_util.utcnow()
    one = zero + timedelta(minutes=1)
    two = one + timedelta(minutes=15)
    three = two + timedelta(minutes=30)
    four = three + timedelta(minutes=15)

    states = {mp: [], sns1: [], sns2: [], sns3: []}
    with patch("openpeerpower.components.recorder.dt_util.utcnow", return_value=one):
        states[mp].append(
            set_state(mp, "idle", attributes={"media_title": str(sentinel.mt1)})
        )
        states[mp].append(
            set_state(mp, "YouTube", attributes={"media_title": str(sentinel.mt2)})
        )
        states[sns1].append(set_state(sns1, "10", attributes=sns1_attr))
        states[sns2].append(set_state(sns2, "10", attributes=sns2_attr))
        states[sns3].append(set_state(sns3, "10", attributes=sns3_attr))

    with patch("openpeerpower.components.recorder.dt_util.utcnow", return_value=two):
        states[sns1].append(set_state(sns1, "15", attributes=sns1_attr))
        states[sns2].append(set_state(sns2, "15", attributes=sns2_attr))
        states[sns3].append(set_state(sns3, "15", attributes=sns3_attr))

    with patch("openpeerpower.components.recorder.dt_util.utcnow", return_value=three):
        states[sns1].append(set_state(sns1, "20", attributes=sns1_attr))
        states[sns2].append(set_state(sns2, "20", attributes=sns2_attr))
        states[sns3].append(set_state(sns3, "20", attributes=sns3_attr))

    return zero, four, states
