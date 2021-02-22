"""The test for the Trend sensor platform."""
from datetime import timedelta
from os import path
from unittest.mock import patch

from openpeerpower import config as.opp_config, setup
from openpeerpower.components.trend import DOMAIN
from openpeerpower.const import SERVICE_RELOAD
import openpeerpower.util.dt as dt_util

from tests.common import assert_setup_component, get_test_open_peer_power


class TestTrendBinarySensor:
    """Test the Trend sensor."""

    opp =None

    def setup_method(self, method):
        """Set up things to be run when tests are started."""
        self opp =get_test_open_peer_power()

    def teardown_method(self, method):
        """Stop everything that was started."""
        self.opp.stop()

    def test_up(self):
        """Test up trend."""
        assert setup.setup_component(
            self.opp,
            "binary_sensor",
            {
                "binary_sensor": {
                    "platform": "trend",
                    "sensors": {
                        "test_trend_sensor": {"entity_id": "sensor.test_state"}
                    },
                }
            },
        )
        self.opp.block_till_done()

        self.opp.states.set("sensor.test_state", "1")
        self.opp.block_till_done()
        self.opp.states.set("sensor.test_state", "2")
        self.opp.block_till_done()
        state = self.opp.states.get("binary_sensor.test_trend_sensor")
        assert state.state == "on"

    def test_up_using_trendline(self):
        """Test up trend using multiple samples and trendline calculation."""
        assert setup.setup_component(
            self.opp,
            "binary_sensor",
            {
                "binary_sensor": {
                    "platform": "trend",
                    "sensors": {
                        "test_trend_sensor": {
                            "entity_id": "sensor.test_state",
                            "sample_duration": 10000,
                            "min_gradient": 1,
                            "max_samples": 25,
                        }
                    },
                }
            },
        )
        self.opp.block_till_done()

        now = dt_util.utcnow()
        for val in [10, 0, 20, 30]:
            with patch("openpeerpower.util.dt.utcnow", return_value=now):
                self.opp.states.set("sensor.test_state", val)
            self.opp.block_till_done()
            now += timedelta(seconds=2)

        state = self.opp.states.get("binary_sensor.test_trend_sensor")
        assert state.state == "on"

        # have to change state value, otherwise sample will lost
        for val in [0, 30, 1, 0]:
            with patch("openpeerpower.util.dt.utcnow", return_value=now):
                self.opp.states.set("sensor.test_state", val)
            self.opp.block_till_done()
            now += timedelta(seconds=2)

        state = self.opp.states.get("binary_sensor.test_trend_sensor")
        assert state.state == "off"

    def test_down_using_trendline(self):
        """Test down trend using multiple samples and trendline calculation."""
        assert setup.setup_component(
            self.opp,
            "binary_sensor",
            {
                "binary_sensor": {
                    "platform": "trend",
                    "sensors": {
                        "test_trend_sensor": {
                            "entity_id": "sensor.test_state",
                            "sample_duration": 10000,
                            "min_gradient": 1,
                            "max_samples": 25,
                            "invert": "Yes",
                        }
                    },
                }
            },
        )
        self.opp.block_till_done()

        now = dt_util.utcnow()
        for val in [30, 20, 30, 10]:
            with patch("openpeerpower.util.dt.utcnow", return_value=now):
                self.opp.states.set("sensor.test_state", val)
            self.opp.block_till_done()
            now += timedelta(seconds=2)

        state = self.opp.states.get("binary_sensor.test_trend_sensor")
        assert state.state == "on"

        for val in [30, 0, 45, 50]:
            with patch("openpeerpower.util.dt.utcnow", return_value=now):
                self.opp.states.set("sensor.test_state", val)
            self.opp.block_till_done()
            now += timedelta(seconds=2)

        state = self.opp.states.get("binary_sensor.test_trend_sensor")
        assert state.state == "off"

    def test_down(self):
        """Test down trend."""
        assert setup.setup_component(
            self.opp,
            "binary_sensor",
            {
                "binary_sensor": {
                    "platform": "trend",
                    "sensors": {
                        "test_trend_sensor": {"entity_id": "sensor.test_state"}
                    },
                }
            },
        )
        self.opp.block_till_done()

        self.opp.states.set("sensor.test_state", "2")
        self.opp.block_till_done()
        self.opp.states.set("sensor.test_state", "1")
        self.opp.block_till_done()
        state = self.opp.states.get("binary_sensor.test_trend_sensor")
        assert state.state == "off"

    def test_invert_up(self):
        """Test up trend with custom message."""
        assert setup.setup_component(
            self.opp,
            "binary_sensor",
            {
                "binary_sensor": {
                    "platform": "trend",
                    "sensors": {
                        "test_trend_sensor": {
                            "entity_id": "sensor.test_state",
                            "invert": "Yes",
                        }
                    },
                }
            },
        )
        self.opp.block_till_done()

        self.opp.states.set("sensor.test_state", "1")
        self.opp.block_till_done()
        self.opp.states.set("sensor.test_state", "2")
        self.opp.block_till_done()
        state = self.opp.states.get("binary_sensor.test_trend_sensor")
        assert state.state == "off"

    def test_invert_down(self):
        """Test down trend with custom message."""
        assert setup.setup_component(
            self.opp,
            "binary_sensor",
            {
                "binary_sensor": {
                    "platform": "trend",
                    "sensors": {
                        "test_trend_sensor": {
                            "entity_id": "sensor.test_state",
                            "invert": "Yes",
                        }
                    },
                }
            },
        )
        self.opp.block_till_done()

        self.opp.states.set("sensor.test_state", "2")
        self.opp.block_till_done()
        self.opp.states.set("sensor.test_state", "1")
        self.opp.block_till_done()
        state = self.opp.states.get("binary_sensor.test_trend_sensor")
        assert state.state == "on"

    def test_attribute_up(self):
        """Test attribute up trend."""
        assert setup.setup_component(
            self.opp,
            "binary_sensor",
            {
                "binary_sensor": {
                    "platform": "trend",
                    "sensors": {
                        "test_trend_sensor": {
                            "entity_id": "sensor.test_state",
                            "attribute": "attr",
                        }
                    },
                }
            },
        )
        self.opp.block_till_done()
        self.opp.states.set("sensor.test_state", "State", {"attr": "1"})
        self.opp.block_till_done()
        self.opp.states.set("sensor.test_state", "State", {"attr": "2"})
        self.opp.block_till_done()
        state = self.opp.states.get("binary_sensor.test_trend_sensor")
        assert state.state == "on"

    def test_attribute_down(self):
        """Test attribute down trend."""
        assert setup.setup_component(
            self.opp,
            "binary_sensor",
            {
                "binary_sensor": {
                    "platform": "trend",
                    "sensors": {
                        "test_trend_sensor": {
                            "entity_id": "sensor.test_state",
                            "attribute": "attr",
                        }
                    },
                }
            },
        )
        self.opp.block_till_done()

        self.opp.states.set("sensor.test_state", "State", {"attr": "2"})
        self.opp.block_till_done()
        self.opp.states.set("sensor.test_state", "State", {"attr": "1"})
        self.opp.block_till_done()
        state = self.opp.states.get("binary_sensor.test_trend_sensor")
        assert state.state == "off"

    def test_max_samples(self):
        """Test that sample count is limited correctly."""
        assert setup.setup_component(
            self.opp,
            "binary_sensor",
            {
                "binary_sensor": {
                    "platform": "trend",
                    "sensors": {
                        "test_trend_sensor": {
                            "entity_id": "sensor.test_state",
                            "max_samples": 3,
                            "min_gradient": -1,
                        }
                    },
                }
            },
        )
        self.opp.block_till_done()

        for val in [0, 1, 2, 3, 2, 1]:
            self.opp.states.set("sensor.test_state", val)
            self.opp.block_till_done()

        state = self.opp.states.get("binary_sensor.test_trend_sensor")
        assert state.state == "on"
        assert state.attributes["sample_count"] == 3

    def test_non_numeric(self):
        """Test up trend."""
        assert setup.setup_component(
            self.opp,
            "binary_sensor",
            {
                "binary_sensor": {
                    "platform": "trend",
                    "sensors": {
                        "test_trend_sensor": {"entity_id": "sensor.test_state"}
                    },
                }
            },
        )
        self.opp.block_till_done()

        self.opp.states.set("sensor.test_state", "Non")
        self.opp.block_till_done()
        self.opp.states.set("sensor.test_state", "Numeric")
        self.opp.block_till_done()
        state = self.opp.states.get("binary_sensor.test_trend_sensor")
        assert state.state == "off"

    def test_missing_attribute(self):
        """Test attribute down trend."""
        assert setup.setup_component(
            self.opp,
            "binary_sensor",
            {
                "binary_sensor": {
                    "platform": "trend",
                    "sensors": {
                        "test_trend_sensor": {
                            "entity_id": "sensor.test_state",
                            "attribute": "missing",
                        }
                    },
                }
            },
        )
        self.opp.block_till_done()

        self.opp.states.set("sensor.test_state", "State", {"attr": "2"})
        self.opp.block_till_done()
        self.opp.states.set("sensor.test_state", "State", {"attr": "1"})
        self.opp.block_till_done()
        state = self.opp.states.get("binary_sensor.test_trend_sensor")
        assert state.state == "off"

    def test_invalid_name_does_not_create(self):
        """Test invalid name."""
        with assert_setup_component(0):
            assert setup.setup_component(
                self.opp,
                "binary_sensor",
                {
                    "binary_sensor": {
                        "platform": "template",
                        "sensors": {
                            "test INVALID sensor": {"entity_id": "sensor.test_state"}
                        },
                    }
                },
            )
        assert self.opp.states.all() == []

    def test_invalid_sensor_does_not_create(self):
        """Test invalid sensor."""
        with assert_setup_component(0):
            assert setup.setup_component(
                self.opp,
                "binary_sensor",
                {
                    "binary_sensor": {
                        "platform": "template",
                        "sensors": {
                            "test_trend_sensor": {"not_entity_id": "sensor.test_state"}
                        },
                    }
                },
            )
        assert self.opp.states.all() == []

    def test_no_sensors_does_not_create(self):
        """Test no sensors."""
        with assert_setup_component(0):
            assert setup.setup_component(
                self.opp, "binary_sensor", {"binary_sensor": {"platform": "trend"}}
            )
        assert self.opp.states.all() == []


async def test_reload.opp):
    """Verify we can reload trend sensors."""
   .opp.states.async_set("sensor.test_state", 1234)

    await setup.async_setup_component(
       .opp,
        "binary_sensor",
        {
            "binary_sensor": {
                "platform": "trend",
                "sensors": {"test_trend_sensor": {"entity_id": "sensor.test_state"}},
            }
        },
    )
    await.opp.async_block_till_done()

    assert len.opp.states.async_all()) == 2

    assert.opp.states.get("binary_sensor.test_trend_sensor")

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "trend/configuration.yaml",
    )
    with patch.object.opp_config, "YAML_CONFIG_FILE", yaml_path):
        await.opp.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await.opp.async_block_till_done()

    assert len.opp.states.async_all()) == 2

    assert.opp.states.get("binary_sensor.test_trend_sensor") is None
    assert.opp.states.get("binary_sensor.second_test_trend_sensor")


def _get_fixtures_base_path():
    return path.dirname(path.dirname(path.dirname(__file__)))
