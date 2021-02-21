"""The test for the History Statistics sensor platform."""
# pylint: disable=protected-access
from datetime import datetime, timedelta
from os import path
import unittest
from unittest.mock import patch

import pytest
import pytz

from openpeerpower import config as.opp_config
from openpeerpower.components.history_stats import DOMAIN
from openpeerpower.components.history_stats.sensor import HistoryStatsSensor
from openpeerpower.const import SERVICE_RELOAD, STATE_UNKNOWN
import openpeerpowerr.core as ha
from openpeerpowerr.helpers.template import Template
from openpeerpowerr.setup import async_setup_component, setup_component
import openpeerpowerr.util.dt as dt_util

from tests.common import get_test_home_assistant, init_recorder_component


class TestHistoryStatsSensor(unittest.TestCase):
    """Test the History Statistics sensor."""

    def setUp(self):
        """Set up things to be run when tests are started."""
        self.opp = get_test_home_assistant()
        self.addCleanup(self.opp.stop)

    def test_setup(self):
        """Test the history statistics sensor setup."""
        self.init_recorder()
        config = {
            "history": {},
            "sensor": {
                "platform": "history_stats",
                "entity_id": "binary_sensor.test_id",
                "state": "on",
                "start": "{{ now().replace(hour=0)"
                ".replace(minute=0).replace(second=0) }}",
                "duration": "02:00",
                "name": "Test",
            },
        }

        assert setup_component(self.opp, "sensor", config)
        self.opp.block_till_done()

        state = self.opp.states.get("sensor.test")
        assert state.state == STATE_UNKNOWN

    def test_setup_multiple_states(self):
        """Test the history statistics sensor setup for multiple states."""
        self.init_recorder()
        config = {
            "history": {},
            "sensor": {
                "platform": "history_stats",
                "entity_id": "binary_sensor.test_id",
                "state": ["on", "true"],
                "start": "{{ now().replace(hour=0)"
                ".replace(minute=0).replace(second=0) }}",
                "duration": "02:00",
                "name": "Test",
            },
        }

        assert setup_component(self.opp, "sensor", config)
        self.opp.block_till_done()

        state = self.opp.states.get("sensor.test")
        assert state.state == STATE_UNKNOWN

    @patch(
        "openpeerpowerr.helpers.template.TemplateEnvironment.is_safe_callable",
        return_value=True,
    )
    def test_period_parsing(self, mock):
        """Test the conversion from templates to period."""
        now = datetime(2019, 1, 1, 23, 30, 0, tzinfo=pytz.utc)
        with patch("openpeerpowerr.util.dt.now", return_value=now):
            today = Template(
                "{{ now().replace(hour=0).replace(minute=0).replace(second=0) }}",
                self.opp,
            )
            duration = timedelta(hours=2, minutes=1)

            sensor1 = HistoryStatsSensor(
                self.opp, "test", "on", today, None, duration, "time", "test"
            )
            sensor2 = HistoryStatsSensor(
                self.opp, "test", "on", None, today, duration, "time", "test"
            )

            sensor1.update_period()
            sensor1_start, sensor1_end = sensor1._period
            sensor2.update_period()
            sensor2_start, sensor2_end = sensor2._period

        # Start = 00:00:00
        assert sensor1_start.hour == 0
        assert sensor1_start.minute == 0
        assert sensor1_start.second == 0

        # End = 02:01:00
        assert sensor1_end.hour == 2
        assert sensor1_end.minute == 1
        assert sensor1_end.second == 0

        # Start = 21:59:00
        assert sensor2_start.hour == 21
        assert sensor2_start.minute == 59
        assert sensor2_start.second == 0

        # End = 00:00:00
        assert sensor2_end.hour == 0
        assert sensor2_end.minute == 0
        assert sensor2_end.second == 0

    def test_measure(self):
        """Test the history statistics sensor measure."""
        t0 = dt_util.utcnow() - timedelta(minutes=40)
        t1 = t0 + timedelta(minutes=20)
        t2 = dt_util.utcnow() - timedelta(minutes=10)

        # Start     t0        t1        t2        End
        # |--20min--|--20min--|--10min--|--10min--|
        # |---off---|---on----|---off---|---on----|

        fake_states = {
            "binary_sensor.test_id": [
                op.State("binary_sensor.test_id", "on", last_changed=t0),
                op.State("binary_sensor.test_id", "off", last_changed=t1),
                op.State("binary_sensor.test_id", "on", last_changed=t2),
            ]
        }

        start = Template("{{ as_timestamp(now()) - 3600 }}", self.opp)
        end = Template("{{ now() }}", self.opp)

        sensor1 = HistoryStatsSensor(
            self.opp, "binary_sensor.test_id", "on", start, end, None, "time", "Test"
        )

        sensor2 = HistoryStatsSensor(
            self.opp, "unknown.id", "on", start, end, None, "time", "Test"
        )

        sensor3 = HistoryStatsSensor(
            self.opp, "binary_sensor.test_id", "on", start, end, None, "count", "test"
        )

        sensor4 = HistoryStatsSensor(
            self.opp, "binary_sensor.test_id", "on", start, end, None, "ratio", "test"
        )

        assert sensor1._type == "time"
        assert sensor3._type == "count"
        assert sensor4._type == "ratio"

        with patch(
            "openpeerpower.components.history.state_changes_during_period",
            return_value=fake_states,
        ):
            with patch("openpeerpower.components.history.get_state", return_value=None):
                sensor1.update()
                sensor2.update()
                sensor3.update()
                sensor4.update()

        assert sensor1.state == 0.5
        assert sensor2.state is None
        assert sensor3.state == 2
        assert sensor4.state == 50

    def test_measure_multiple(self):
        """Test the history statistics sensor measure for multiple states."""
        t0 = dt_util.utcnow() - timedelta(minutes=40)
        t1 = t0 + timedelta(minutes=20)
        t2 = dt_util.utcnow() - timedelta(minutes=10)

        # Start     t0        t1        t2        End
        # |--20min--|--20min--|--10min--|--10min--|
        # |---------|--orange-|-default-|---blue--|

        fake_states = {
            "input_select.test_id": [
                op.State("input_select.test_id", "orange", last_changed=t0),
                op.State("input_select.test_id", "default", last_changed=t1),
                op.State("input_select.test_id", "blue", last_changed=t2),
            ]
        }

        start = Template("{{ as_timestamp(now()) - 3600 }}", self.opp)
        end = Template("{{ now() }}", self.opp)

        sensor1 = HistoryStatsSensor(
            self.opp,
            "input_select.test_id",
            ["orange", "blue"],
            start,
            end,
            None,
            "time",
            "Test",
        )

        sensor2 = HistoryStatsSensor(
            self.opp,
            "unknown.id",
            ["orange", "blue"],
            start,
            end,
            None,
            "time",
            "Test",
        )

        sensor3 = HistoryStatsSensor(
            self.opp,
            "input_select.test_id",
            ["orange", "blue"],
            start,
            end,
            None,
            "count",
            "test",
        )

        sensor4 = HistoryStatsSensor(
            self.opp,
            "input_select.test_id",
            ["orange", "blue"],
            start,
            end,
            None,
            "ratio",
            "test",
        )

        assert sensor1._type == "time"
        assert sensor3._type == "count"
        assert sensor4._type == "ratio"

        with patch(
            "openpeerpower.components.history.state_changes_during_period",
            return_value=fake_states,
        ):
            with patch("openpeerpower.components.history.get_state", return_value=None):
                sensor1.update()
                sensor2.update()
                sensor3.update()
                sensor4.update()

        assert sensor1.state == 0.5
        assert sensor2.state is None
        assert sensor3.state == 2
        assert sensor4.state == 50

    def test_wrong_date(self):
        """Test when start or end value is not a timestamp or a date."""
        good = Template("{{ now() }}", self.opp)
        bad = Template("{{ TEST }}", self.opp)

        sensor1 = HistoryStatsSensor(
            self.opp, "test", "on", good, bad, None, "time", "Test"
        )
        sensor2 = HistoryStatsSensor(
            self.opp, "test", "on", bad, good, None, "time", "Test"
        )

        before_update1 = sensor1._period
        before_update2 = sensor2._period

        sensor1.update_period()
        sensor2.update_period()

        assert before_update1 == sensor1._period
        assert before_update2 == sensor2._period

    def test_wrong_duration(self):
        """Test when duration value is not a timedelta."""
        self.init_recorder()
        config = {
            "history": {},
            "sensor": {
                "platform": "history_stats",
                "entity_id": "binary_sensor.test_id",
                "name": "Test",
                "state": "on",
                "start": "{{ now() }}",
                "duration": "TEST",
            },
        }

        setup_component(self.opp, "sensor", config)
        assert self.opp.states.get("sensor.test") is None
        with pytest.raises(TypeError):
            setup_component(self.opp, "sensor", config)()

    def test_bad_template(self):
        """Test Exception when the template cannot be parsed."""
        bad = Template("{{ x - 12 }}", self.opp)  # x is undefined
        duration = "01:00"

        sensor1 = HistoryStatsSensor(
            self.opp, "test", "on", bad, None, duration, "time", "Test"
        )
        sensor2 = HistoryStatsSensor(
            self.opp, "test", "on", None, bad, duration, "time", "Test"
        )

        before_update1 = sensor1._period
        before_update2 = sensor2._period

        sensor1.update_period()
        sensor2.update_period()

        assert before_update1 == sensor1._period
        assert before_update2 == sensor2._period

    def test_not_enough_arguments(self):
        """Test config when not enough arguments provided."""
        self.init_recorder()
        config = {
            "history": {},
            "sensor": {
                "platform": "history_stats",
                "entity_id": "binary_sensor.test_id",
                "name": "Test",
                "state": "on",
                "start": "{{ now() }}",
            },
        }

        setup_component(self.opp, "sensor", config)
        assert self.opp.states.get("sensor.test") is None
        with pytest.raises(TypeError):
            setup_component(self.opp, "sensor", config)()

    def test_too_many_arguments(self):
        """Test config when too many arguments provided."""
        self.init_recorder()
        config = {
            "history": {},
            "sensor": {
                "platform": "history_stats",
                "entity_id": "binary_sensor.test_id",
                "name": "Test",
                "state": "on",
                "start": "{{ as_timestamp(now()) - 3600 }}",
                "end": "{{ now() }}",
                "duration": "01:00",
            },
        }

        setup_component(self.opp, "sensor", config)
        assert self.opp.states.get("sensor.test") is None
        with pytest.raises(TypeError):
            setup_component(self.opp, "sensor", config)()

    def init_recorder(self):
        """Initialize the recorder."""
        init_recorder_component(self.opp)
        self.opp.start()


async def test_reload.opp):
    """Verify we can reload history_stats sensors."""
    await opp.async_add_executor_job(
        init_recorder_component,.opp
    )  # force in memory db

   .opp.state = op.CoreState.not_running
   .opp.states.async_set("binary_sensor.test_id", "on")

    await async_setup_component(
       .opp,
        "sensor",
        {
            "sensor": {
                "platform": "history_stats",
                "entity_id": "binary_sensor.test_id",
                "name": "test",
                "state": "on",
                "start": "{{ as_timestamp(now()) - 3600 }}",
                "duration": "01:00",
            },
        },
    )
    await opp.async_block_till_done()
    await.opp.async_start()
    await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 2

    assert.opp.states.get("sensor.test")

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "history_stats/configuration.yaml",
    )
    with patch.object.opp_config, "YAML_CONFIG_FILE", yaml_path):
        await.opp.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 2

    assert.opp.states.get("sensor.test") is None
    assert.opp.states.get("sensor.second_test")


def _get_fixtures_base_path():
    return path.dirname(path.dirname(path.dirname(__file__)))
