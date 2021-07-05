"""Test the condition helper."""
from datetime import datetime
from unittest.mock import patch

import pytest

from openpeerpower.components import sun
import openpeerpower.components.automation as automation
from openpeerpower.const import SUN_EVENT_SUNRISE, SUN_EVENT_SUNSET
from openpeerpower.exceptions import ConditionError, OpenPeerPowerError
from openpeerpower.helpers import condition, trace
from openpeerpower.helpers.template import Template
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util

from tests.common import async_mock_service

ORIG_TIME_ZONE = dt_util.DEFAULT_TIME_ZONE


@pytest.fixture
def calls(opp):
    """Track calls to a mock service."""
    return async_mock_service(opp, "test", "automation")


@pytest.fixture(autouse=True)
def setup_comp(opp):
    """Initialize components."""
    opp.config.set_time_zone(opp.config.time_zone)
    opp.loop.run_until_complete(
        async_setup_component(opp, sun.DOMAIN, {sun.DOMAIN: {sun.CONF_ELEVATION: 0}})
    )


def teardown():
    """Restore."""
    dt_util.set_default_time_zone(ORIG_TIME_ZONE)


def assert_element(trace_element, expected_element, path):
    """Assert a trace element is as expected.

    Note: Unused variable 'path' is passed to get helpful errors from pytest.
    """
    expected_result = expected_element.get("result", {})
    # Check that every item in expected_element is present and equal in trace_element
    # The redundant set operation gives helpful errors from pytest
    assert not set(expected_result) - set(trace_element._result or {})
    for result_key, result in expected_result.items():
        assert trace_element._result[result_key] == result

    # Check for unexpected items in trace_element
    assert not set(trace_element._result or {}) - set(expected_result)

    if "error_type" in expected_element:
        assert isinstance(trace_element._error, expected_element["error_type"])
    else:
        assert trace_element._error is None


@pytest.fixture(autouse=True)
def prepare_condition_trace():
    """Clear previous trace."""
    trace.trace_clear()


def assert_condition_trace(expected):
    """Assert a trace condition sequence is as expected."""
    condition_trace = trace.trace_get(clear=False)
    trace.trace_clear()
    expected_trace_keys = list(expected.keys())
    assert list(condition_trace.keys()) == expected_trace_keys
    for trace_key_index, key in enumerate(expected_trace_keys):
        assert len(condition_trace[key]) == len(expected[key])
        for index, element in enumerate(expected[key]):
            path = f"[{trace_key_index}][{index}]"
            assert_element(condition_trace[key][index], element, path)


async def test_invalid_condition(opp):
    """Test if invalid condition raises."""
    with pytest.raises(OpenPeerPowerError):
        await condition.async_from_config(
            opp,
            {
                "condition": "invalid",
                "conditions": [
                    {
                        "condition": "state",
                        "entity_id": "sensor.temperature",
                        "state": "100",
                    },
                ],
            },
        )


async def test_and_condition(opp):
    """Test the 'and' condition."""
    test = await condition.async_from_config(
        opp,
        {
            "alias": "And Condition",
            "condition": "and",
            "conditions": [
                {
                    "condition": "state",
                    "entity_id": "sensor.temperature",
                    "state": "100",
                },
                {
                    "condition": "numeric_state",
                    "entity_id": "sensor.temperature",
                    "below": 110,
                },
            ],
        },
    )

    with pytest.raises(ConditionError):
        test(opp)
    assert_condition_trace(
        {
            "": [{"error_type": ConditionError}],
            "conditions/0": [{"error_type": ConditionError}],
            "conditions/0/entity_id/0": [{"error_type": ConditionError}],
            "conditions/1": [{"error_type": ConditionError}],
            "conditions/1/entity_id/0": [{"error_type": ConditionError}],
        }
    )

    opp.states.async_set("sensor.temperature", 120)
    assert not test(opp)
    assert_condition_trace(
        {
            "": [{"result": {"result": False}}],
            "conditions/0": [{"result": {"result": False}}],
            "conditions/0/entity_id/0": [
                {"result": {"result": False, "state": "120", "wanted_state": "100"}}
            ],
        }
    )

    opp.states.async_set("sensor.temperature", 105)
    assert not test(opp)
    assert_condition_trace(
        {
            "": [{"result": {"result": False}}],
            "conditions/0": [{"result": {"result": False}}],
            "conditions/0/entity_id/0": [
                {"result": {"result": False, "state": "105", "wanted_state": "100"}}
            ],
        }
    )

    opp.states.async_set("sensor.temperature", 100)
    assert test(opp)
    assert_condition_trace(
        {
            "": [{"result": {"result": True}}],
            "conditions/0": [{"result": {"result": True}}],
            "conditions/0/entity_id/0": [
                {"result": {"result": True, "state": "100", "wanted_state": "100"}}
            ],
            "conditions/1": [{"result": {"result": True}}],
            "conditions/1/entity_id/0": [{"result": {"result": True, "state": 100.0}}],
        }
    )


async def test_and_condition_raises(opp):
    """Test the 'and' condition."""
    test = await condition.async_from_config(
        opp,
        {
            "alias": "And Condition",
            "condition": "and",
            "conditions": [
                {
                    "condition": "state",
                    "entity_id": "sensor.temperature",
                    "state": "100",
                },
                {
                    "condition": "numeric_state",
                    "entity_id": "sensor.temperature2",
                    "above": 110,
                },
            ],
        },
    )

    # All subconditions raise, the AND-condition should raise
    with pytest.raises(ConditionError):
        test(opp)
    assert_condition_trace(
        {
            "": [{"error_type": ConditionError}],
            "conditions/0": [{"error_type": ConditionError}],
            "conditions/0/entity_id/0": [{"error_type": ConditionError}],
            "conditions/1": [{"error_type": ConditionError}],
            "conditions/1/entity_id/0": [{"error_type": ConditionError}],
        }
    )

    # The first subconditions raises, the second returns True, the AND-condition
    # should raise
    opp.states.async_set("sensor.temperature2", 120)
    with pytest.raises(ConditionError):
        test(opp)
    assert_condition_trace(
        {
            "": [{"error_type": ConditionError}],
            "conditions/0": [{"error_type": ConditionError}],
            "conditions/0/entity_id/0": [{"error_type": ConditionError}],
            "conditions/1": [{"result": {"result": True}}],
            "conditions/1/entity_id/0": [{"result": {"result": True, "state": 120.0}}],
        }
    )

    # The first subconditions raises, the second returns False, the AND-condition
    # should return False
    opp.states.async_set("sensor.temperature2", 90)
    assert not test(opp)
    assert_condition_trace(
        {
            "": [{"result": {"result": False}}],
            "conditions/0": [{"error_type": ConditionError}],
            "conditions/0/entity_id/0": [{"error_type": ConditionError}],
            "conditions/1": [{"result": {"result": False}}],
            "conditions/1/entity_id/0": [
                {
                    "result": {
                        "result": False,
                        "state": 90.0,
                        "wanted_state_above": 110.0,
                    }
                }
            ],
        }
    )


async def test_and_condition_with_template(opp):
    """Test the 'and' condition."""
    test = await condition.async_from_config(
        opp,
        {
            "condition": "and",
            "conditions": [
                {
                    "alias": "Template Condition",
                    "condition": "template",
                    "value_template": '{{ states.sensor.temperature.state == "100" }}',
                },
                {
                    "condition": "numeric_state",
                    "entity_id": "sensor.temperature",
                    "below": 110,
                },
            ],
        },
    )

    opp.states.async_set("sensor.temperature", 120)
    assert not test(opp)
    assert_condition_trace(
        {
            "": [{"result": {"result": False}}],
            "conditions/0": [
                {"result": {"entities": ["sensor.temperature"], "result": False}}
            ],
        }
    )

    opp.states.async_set("sensor.temperature", 105)
    assert not test(opp)

    opp.states.async_set("sensor.temperature", 100)
    assert test(opp)


async def test_or_condition(opp):
    """Test the 'or' condition."""
    test = await condition.async_from_config(
        opp,
        {
            "alias": "Or Condition",
            "condition": "or",
            "conditions": [
                {
                    "condition": "state",
                    "entity_id": "sensor.temperature",
                    "state": "100",
                },
                {
                    "condition": "numeric_state",
                    "entity_id": "sensor.temperature",
                    "below": 110,
                },
            ],
        },
    )

    with pytest.raises(ConditionError):
        test(opp)
    assert_condition_trace(
        {
            "": [{"error_type": ConditionError}],
            "conditions/0": [{"error_type": ConditionError}],
            "conditions/0/entity_id/0": [{"error_type": ConditionError}],
            "conditions/1": [{"error_type": ConditionError}],
            "conditions/1/entity_id/0": [{"error_type": ConditionError}],
        }
    )

    opp.states.async_set("sensor.temperature", 120)
    assert not test(opp)
    assert_condition_trace(
        {
            "": [{"result": {"result": False}}],
            "conditions/0": [{"result": {"result": False}}],
            "conditions/0/entity_id/0": [
                {"result": {"result": False, "state": "120", "wanted_state": "100"}}
            ],
            "conditions/1": [{"result": {"result": False}}],
            "conditions/1/entity_id/0": [
                {
                    "result": {
                        "result": False,
                        "state": 120.0,
                        "wanted_state_below": 110.0,
                    }
                }
            ],
        }
    )

    opp.states.async_set("sensor.temperature", 105)
    assert test(opp)
    assert_condition_trace(
        {
            "": [{"result": {"result": True}}],
            "conditions/0": [{"result": {"result": False}}],
            "conditions/0/entity_id/0": [
                {"result": {"result": False, "state": "105", "wanted_state": "100"}}
            ],
            "conditions/1": [{"result": {"result": True}}],
            "conditions/1/entity_id/0": [{"result": {"result": True, "state": 105.0}}],
        }
    )

    opp.states.async_set("sensor.temperature", 100)
    assert test(opp)
    assert_condition_trace(
        {
            "": [{"result": {"result": True}}],
            "conditions/0": [{"result": {"result": True}}],
            "conditions/0/entity_id/0": [
                {"result": {"result": True, "state": "100", "wanted_state": "100"}}
            ],
        }
    )


async def test_or_condition_raises(opp):
    """Test the 'or' condition."""
    test = await condition.async_from_config(
        opp,
        {
            "alias": "Or Condition",
            "condition": "or",
            "conditions": [
                {
                    "condition": "state",
                    "entity_id": "sensor.temperature",
                    "state": "100",
                },
                {
                    "condition": "numeric_state",
                    "entity_id": "sensor.temperature2",
                    "above": 110,
                },
            ],
        },
    )

    # All subconditions raise, the OR-condition should raise
    with pytest.raises(ConditionError):
        test(opp)
    assert_condition_trace(
        {
            "": [{"error_type": ConditionError}],
            "conditions/0": [{"error_type": ConditionError}],
            "conditions/0/entity_id/0": [{"error_type": ConditionError}],
            "conditions/1": [{"error_type": ConditionError}],
            "conditions/1/entity_id/0": [{"error_type": ConditionError}],
        }
    )

    # The first subconditions raises, the second returns False, the OR-condition
    # should raise
    opp.states.async_set("sensor.temperature2", 100)
    with pytest.raises(ConditionError):
        test(opp)
    assert_condition_trace(
        {
            "": [{"error_type": ConditionError}],
            "conditions/0": [{"error_type": ConditionError}],
            "conditions/0/entity_id/0": [{"error_type": ConditionError}],
            "conditions/1": [{"result": {"result": False}}],
            "conditions/1/entity_id/0": [
                {
                    "result": {
                        "result": False,
                        "state": 100.0,
                        "wanted_state_above": 110.0,
                    }
                }
            ],
        }
    )

    # The first subconditions raises, the second returns True, the OR-condition
    # should return True
    opp.states.async_set("sensor.temperature2", 120)
    assert test(opp)
    assert_condition_trace(
        {
            "": [{"result": {"result": True}}],
            "conditions/0": [{"error_type": ConditionError}],
            "conditions/0/entity_id/0": [{"error_type": ConditionError}],
            "conditions/1": [{"result": {"result": True}}],
            "conditions/1/entity_id/0": [{"result": {"result": True, "state": 120.0}}],
        }
    )


async def test_or_condition_with_template(opp):
    """Test the 'or' condition."""
    test = await condition.async_from_config(
        opp,
        {
            "condition": "or",
            "conditions": [
                {'{{ states.sensor.temperature.state == "100" }}'},
                {
                    "condition": "numeric_state",
                    "entity_id": "sensor.temperature",
                    "below": 110,
                },
            ],
        },
    )

    opp.states.async_set("sensor.temperature", 120)
    assert not test(opp)

    opp.states.async_set("sensor.temperature", 105)
    assert test(opp)

    opp.states.async_set("sensor.temperature", 100)
    assert test(opp)


async def test_not_condition(opp):
    """Test the 'not' condition."""
    test = await condition.async_from_config(
        opp,
        {
            "alias": "Not Condition",
            "condition": "not",
            "conditions": [
                {
                    "condition": "state",
                    "entity_id": "sensor.temperature",
                    "state": "100",
                },
                {
                    "condition": "numeric_state",
                    "entity_id": "sensor.temperature",
                    "below": 50,
                },
            ],
        },
    )

    with pytest.raises(ConditionError):
        test(opp)
    assert_condition_trace(
        {
            "": [{"error_type": ConditionError}],
            "conditions/0": [{"error_type": ConditionError}],
            "conditions/0/entity_id/0": [{"error_type": ConditionError}],
            "conditions/1": [{"error_type": ConditionError}],
            "conditions/1/entity_id/0": [{"error_type": ConditionError}],
        }
    )

    opp.states.async_set("sensor.temperature", 101)
    assert test(opp)
    assert_condition_trace(
        {
            "": [{"result": {"result": True}}],
            "conditions/0": [{"result": {"result": False}}],
            "conditions/0/entity_id/0": [
                {"result": {"result": False, "state": "101", "wanted_state": "100"}}
            ],
            "conditions/1": [{"result": {"result": False}}],
            "conditions/1/entity_id/0": [
                {
                    "result": {
                        "result": False,
                        "state": 101.0,
                        "wanted_state_below": 50.0,
                    }
                }
            ],
        }
    )

    opp.states.async_set("sensor.temperature", 50)
    assert test(opp)
    assert_condition_trace(
        {
            "": [{"result": {"result": True}}],
            "conditions/0": [{"result": {"result": False}}],
            "conditions/0/entity_id/0": [
                {"result": {"result": False, "state": "50", "wanted_state": "100"}}
            ],
            "conditions/1": [{"result": {"result": False}}],
            "conditions/1/entity_id/0": [
                {"result": {"result": False, "state": 50.0, "wanted_state_below": 50.0}}
            ],
        }
    )

    opp.states.async_set("sensor.temperature", 49)
    assert not test(opp)
    assert_condition_trace(
        {
            "": [{"result": {"result": False}}],
            "conditions/0": [{"result": {"result": False}}],
            "conditions/0/entity_id/0": [
                {"result": {"result": False, "state": "49", "wanted_state": "100"}}
            ],
            "conditions/1": [{"result": {"result": True}}],
            "conditions/1/entity_id/0": [{"result": {"result": True, "state": 49.0}}],
        }
    )

    opp.states.async_set("sensor.temperature", 100)
    assert not test(opp)
    assert_condition_trace(
        {
            "": [{"result": {"result": False}}],
            "conditions/0": [{"result": {"result": True}}],
            "conditions/0/entity_id/0": [
                {"result": {"result": True, "state": "100", "wanted_state": "100"}}
            ],
        }
    )


async def test_not_condition_raises(opp):
    """Test the 'and' condition."""
    test = await condition.async_from_config(
        opp,
        {
            "alias": "Not Condition",
            "condition": "not",
            "conditions": [
                {
                    "condition": "state",
                    "entity_id": "sensor.temperature",
                    "state": "100",
                },
                {
                    "condition": "numeric_state",
                    "entity_id": "sensor.temperature2",
                    "below": 50,
                },
            ],
        },
    )

    # All subconditions raise, the NOT-condition should raise
    with pytest.raises(ConditionError):
        test(opp)
    assert_condition_trace(
        {
            "": [{"error_type": ConditionError}],
            "conditions/0": [{"error_type": ConditionError}],
            "conditions/0/entity_id/0": [{"error_type": ConditionError}],
            "conditions/1": [{"error_type": ConditionError}],
            "conditions/1/entity_id/0": [{"error_type": ConditionError}],
        }
    )

    # The first subconditions raises, the second returns False, the NOT-condition
    # should raise
    opp.states.async_set("sensor.temperature2", 90)
    with pytest.raises(ConditionError):
        test(opp)
    assert_condition_trace(
        {
            "": [{"error_type": ConditionError}],
            "conditions/0": [{"error_type": ConditionError}],
            "conditions/0/entity_id/0": [{"error_type": ConditionError}],
            "conditions/1": [{"result": {"result": False}}],
            "conditions/1/entity_id/0": [
                {"result": {"result": False, "state": 90.0, "wanted_state_below": 50.0}}
            ],
        }
    )

    # The first subconditions raises, the second returns True, the NOT-condition
    # should return False
    opp.states.async_set("sensor.temperature2", 40)
    assert not test(opp)
    assert_condition_trace(
        {
            "": [{"result": {"result": False}}],
            "conditions/0": [{"error_type": ConditionError}],
            "conditions/0/entity_id/0": [{"error_type": ConditionError}],
            "conditions/1": [{"result": {"result": True}}],
            "conditions/1/entity_id/0": [{"result": {"result": True, "state": 40.0}}],
        }
    )


async def test_not_condition_with_template(opp):
    """Test the 'or' condition."""
    test = await condition.async_from_config(
        opp,
        {
            "condition": "not",
            "conditions": [
                {
                    "condition": "template",
                    "value_template": '{{ states.sensor.temperature.state == "100" }}',
                },
                {
                    "condition": "numeric_state",
                    "entity_id": "sensor.temperature",
                    "below": 50,
                },
            ],
        },
    )

    opp.states.async_set("sensor.temperature", 101)
    assert test(opp)

    opp.states.async_set("sensor.temperature", 50)
    assert test(opp)

    opp.states.async_set("sensor.temperature", 49)
    assert not test(opp)

    opp.states.async_set("sensor.temperature", 100)
    assert not test(opp)


async def test_time_window(opp):
    """Test time condition windows."""
    sixam = "06:00:00"
    sixpm = "18:00:00"

    test1 = await condition.async_from_config(
        opp,
        {"alias": "Time Cond", "condition": "time", "after": sixam, "before": sixpm},
    )
    test2 = await condition.async_from_config(
        opp,
        {"alias": "Time Cond", "condition": "time", "after": sixpm, "before": sixam},
    )

    with patch(
        "openpeerpower.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=3),
    ):
        assert not test1(opp)
        assert test2(opp)

    with patch(
        "openpeerpower.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=9),
    ):
        assert test1(opp)
        assert not test2(opp)

    with patch(
        "openpeerpower.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=15),
    ):
        assert test1(opp)
        assert not test2(opp)

    with patch(
        "openpeerpower.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=21),
    ):
        assert not test1(opp)
        assert test2(opp)


async def test_time_using_input_datetime(opp):
    """Test time conditions using input_datetime entities."""
    await async_setup_component(
        opp,
        "input_datetime",
        {
            "input_datetime": {
                "am": {"has_date": True, "has_time": True},
                "pm": {"has_date": True, "has_time": True},
            }
        },
    )

    await opp.services.async_call(
        "input_datetime",
        "set_datetime",
        {
            "entity_id": "input_datetime.am",
            "datetime": str(
                dt_util.now()
                .replace(hour=6, minute=0, second=0, microsecond=0)
                .replace(tzinfo=None)
            ),
        },
        blocking=True,
    )

    await opp.services.async_call(
        "input_datetime",
        "set_datetime",
        {
            "entity_id": "input_datetime.pm",
            "datetime": str(
                dt_util.now()
                .replace(hour=18, minute=0, second=0, microsecond=0)
                .replace(tzinfo=None)
            ),
        },
        blocking=True,
    )

    with patch(
        "openpeerpower.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=3),
    ):
        assert not condition.time(
            opp, after="input_datetime.am", before="input_datetime.pm"
        )
        assert condition.time(
            opp, after="input_datetime.pm", before="input_datetime.am"
        )

    with patch(
        "openpeerpower.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=9),
    ):
        assert condition.time(
            opp, after="input_datetime.am", before="input_datetime.pm"
        )
        assert not condition.time(
            opp, after="input_datetime.pm", before="input_datetime.am"
        )

    with patch(
        "openpeerpower.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=15),
    ):
        assert condition.time(
            opp, after="input_datetime.am", before="input_datetime.pm"
        )
        assert not condition.time(
            opp, after="input_datetime.pm", before="input_datetime.am"
        )

    with patch(
        "openpeerpower.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=21),
    ):
        assert not condition.time(
            opp, after="input_datetime.am", before="input_datetime.pm"
        )
        assert condition.time(
            opp, after="input_datetime.pm", before="input_datetime.am"
        )

    # Trigger on PM time
    with patch(
        "openpeerpower.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=18, minute=0, second=0),
    ):
        assert condition.time(
            opp, after="input_datetime.pm", before="input_datetime.am"
        )
        assert not condition.time(
            opp, after="input_datetime.am", before="input_datetime.pm"
        )
        assert condition.time(opp, after="input_datetime.pm")
        assert not condition.time(opp, before="input_datetime.pm")

    # Trigger on AM time
    with patch(
        "openpeerpower.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=6, minute=0, second=0),
    ):
        assert not condition.time(
            opp, after="input_datetime.pm", before="input_datetime.am"
        )
        assert condition.time(
            opp, after="input_datetime.am", before="input_datetime.pm"
        )
        assert condition.time(opp, after="input_datetime.am")
        assert not condition.time(opp, before="input_datetime.am")

    with pytest.raises(ConditionError):
        condition.time(opp, after="input_datetime.not_existing")

    with pytest.raises(ConditionError):
        condition.time(opp, before="input_datetime.not_existing")


async def test_state_raises(opp):
    """Test that state raises ConditionError on errors."""
    # No entity
    with pytest.raises(ConditionError, match="no entity"):
        condition.state(opp, entity=None, req_state="missing")

    # Unknown entities
    test = await condition.async_from_config(
        opp,
        {
            "condition": "state",
            "entity_id": ["sensor.door_unknown", "sensor.window_unknown"],
            "state": "open",
        },
    )
    with pytest.raises(ConditionError, match="unknown entity.*door"):
        test(opp)
    with pytest.raises(ConditionError, match="unknown entity.*window"):
        test(opp)

    # Unknown attribute
    with pytest.raises(ConditionError, match=r"attribute .* does not exist"):
        test = await condition.async_from_config(
            opp,
            {
                "condition": "state",
                "entity_id": "sensor.door",
                "attribute": "model",
                "state": "acme",
            },
        )

        opp.states.async_set("sensor.door", "open")
        test(opp)

    # Unknown state entity
    with pytest.raises(ConditionError, match="input_text.missing"):
        test = await condition.async_from_config(
            opp,
            {
                "condition": "state",
                "entity_id": "sensor.door",
                "state": "input_text.missing",
            },
        )

        opp.states.async_set("sensor.door", "open")
        test(opp)


async def test_state_multiple_entities(opp):
    """Test with multiple entities in condition."""
    test = await condition.async_from_config(
        opp,
        {
            "condition": "and",
            "conditions": [
                {
                    "condition": "state",
                    "entity_id": ["sensor.temperature_1", "sensor.temperature_2"],
                    "state": "100",
                },
            ],
        },
    )

    opp.states.async_set("sensor.temperature_1", 100)
    opp.states.async_set("sensor.temperature_2", 100)
    assert test(opp)

    opp.states.async_set("sensor.temperature_1", 101)
    opp.states.async_set("sensor.temperature_2", 100)
    assert not test(opp)

    opp.states.async_set("sensor.temperature_1", 100)
    opp.states.async_set("sensor.temperature_2", 101)
    assert not test(opp)


async def test_multiple_states(opp):
    """Test with multiple states in condition."""
    test = await condition.async_from_config(
        opp,
        {
            "condition": "and",
            "conditions": [
                {
                    "alias": "State Condition",
                    "condition": "state",
                    "entity_id": "sensor.temperature",
                    "state": ["100", "200"],
                },
            ],
        },
    )

    opp.states.async_set("sensor.temperature", 100)
    assert test(opp)

    opp.states.async_set("sensor.temperature", 200)
    assert test(opp)

    opp.states.async_set("sensor.temperature", 42)
    assert not test(opp)


async def test_state_attribute(opp):
    """Test with state attribute in condition."""
    test = await condition.async_from_config(
        opp,
        {
            "condition": "and",
            "conditions": [
                {
                    "condition": "state",
                    "entity_id": "sensor.temperature",
                    "attribute": "attribute1",
                    "state": 200,
                },
            ],
        },
    )

    opp.states.async_set("sensor.temperature", 100, {"unkown_attr": 200})
    with pytest.raises(ConditionError):
        test(opp)

    opp.states.async_set("sensor.temperature", 100, {"attribute1": 200})
    assert test(opp)

    opp.states.async_set("sensor.temperature", 100, {"attribute1": "200"})
    assert not test(opp)

    opp.states.async_set("sensor.temperature", 100, {"attribute1": 201})
    assert not test(opp)

    opp.states.async_set("sensor.temperature", 100, {"attribute1": None})
    assert not test(opp)


async def test_state_attribute_boolean(opp):
    """Test with boolean state attribute in condition."""
    test = await condition.async_from_config(
        opp,
        {
            "condition": "state",
            "entity_id": "sensor.temperature",
            "attribute": "happening",
            "state": False,
        },
    )

    opp.states.async_set("sensor.temperature", 100, {"happening": 200})
    assert not test(opp)

    opp.states.async_set("sensor.temperature", 100, {"happening": True})
    assert not test(opp)

    opp.states.async_set("sensor.temperature", 100, {"no_happening": 201})
    with pytest.raises(ConditionError):
        test(opp)

    opp.states.async_set("sensor.temperature", 100, {"happening": False})
    assert test(opp)


async def test_state_using_input_entities(opp):
    """Test state conditions using input_* entities."""
    await async_setup_component(
        opp,
        "input_text",
        {
            "input_text": {
                "hello": {"initial": "goodbye"},
            }
        },
    )

    await async_setup_component(
        opp,
        "input_select",
        {
            "input_select": {
                "hello": {"options": ["cya", "goodbye", "welcome"], "initial": "cya"},
            }
        },
    )

    test = await condition.async_from_config(
        opp,
        {
            "condition": "and",
            "conditions": [
                {
                    "condition": "state",
                    "entity_id": "sensor.salut",
                    "state": [
                        "input_text.hello",
                        "input_select.hello",
                        "salut",
                    ],
                },
            ],
        },
    )

    opp.states.async_set("sensor.salut", "goodbye")
    assert test(opp)

    opp.states.async_set("sensor.salut", "salut")
    assert test(opp)

    opp.states.async_set("sensor.salut", "hello")
    assert not test(opp)

    await opp.services.async_call(
        "input_text",
        "set_value",
        {
            "entity_id": "input_text.hello",
            "value": "hi",
        },
        blocking=True,
    )
    assert not test(opp)

    opp.states.async_set("sensor.salut", "hi")
    assert test(opp)

    opp.states.async_set("sensor.salut", "cya")
    assert test(opp)

    await opp.services.async_call(
        "input_select",
        "select_option",
        {
            "entity_id": "input_select.hello",
            "option": "welcome",
        },
        blocking=True,
    )
    assert not test(opp)

    opp.states.async_set("sensor.salut", "welcome")
    assert test(opp)


async def test_numeric_state_known_non_matching(opp):
    """Test that numeric_state doesn't match on known non-matching states."""
    opp.states.async_set("sensor.temperature", "unavailable")
    test = await condition.async_from_config(
        opp,
        {
            "condition": "numeric_state",
            "entity_id": "sensor.temperature",
            "above": 0,
        },
    )

    # Unavailable state
    assert not test(opp)

    # Unknown state
    opp.states.async_set("sensor.temperature", "unknown")
    assert not test(opp)


async def test_numeric_state_raises(opp):
    """Test that numeric_state raises ConditionError on errors."""
    # Unknown entities
    test = await condition.async_from_config(
        opp,
        {
            "condition": "numeric_state",
            "entity_id": ["sensor.temperature_unknown", "sensor.humidity_unknown"],
            "above": 0,
        },
    )
    with pytest.raises(ConditionError, match="unknown entity.*temperature"):
        test(opp)
    with pytest.raises(ConditionError, match="unknown entity.*humidity"):
        test(opp)

    # Unknown attribute
    with pytest.raises(ConditionError, match=r"attribute .* does not exist"):
        test = await condition.async_from_config(
            opp,
            {
                "condition": "numeric_state",
                "entity_id": "sensor.temperature",
                "attribute": "temperature",
                "above": 0,
            },
        )

        opp.states.async_set("sensor.temperature", 50)
        test(opp)

    # Template error
    with pytest.raises(ConditionError, match="ZeroDivisionError"):
        test = await condition.async_from_config(
            opp,
            {
                "condition": "numeric_state",
                "entity_id": "sensor.temperature",
                "value_template": "{{ 1 / 0 }}",
                "above": 0,
            },
        )

        opp.states.async_set("sensor.temperature", 50)
        test(opp)

    # Bad number
    with pytest.raises(ConditionError, match="cannot be processed as a number"):
        test = await condition.async_from_config(
            opp,
            {
                "condition": "numeric_state",
                "entity_id": "sensor.temperature",
                "above": 0,
            },
        )

        opp.states.async_set("sensor.temperature", "fifty")
        test(opp)

    # Below entity missing
    with pytest.raises(ConditionError, match="'below' entity"):
        test = await condition.async_from_config(
            opp,
            {
                "condition": "numeric_state",
                "entity_id": "sensor.temperature",
                "below": "input_number.missing",
            },
        )

        opp.states.async_set("sensor.temperature", 50)
        test(opp)

    # Below entity not a number
    with pytest.raises(
        ConditionError,
        match="'below'.*input_number.missing.*cannot be processed as a number",
    ):
        opp.states.async_set("input_number.missing", "number")
        test(opp)

    # Above entity missing
    with pytest.raises(ConditionError, match="'above' entity"):
        test = await condition.async_from_config(
            opp,
            {
                "condition": "numeric_state",
                "entity_id": "sensor.temperature",
                "above": "input_number.missing",
            },
        )

        opp.states.async_set("sensor.temperature", 50)
        test(opp)

    # Above entity not a number
    with pytest.raises(
        ConditionError,
        match="'above'.*input_number.missing.*cannot be processed as a number",
    ):
        opp.states.async_set("input_number.missing", "number")
        test(opp)


async def test_numeric_state_multiple_entities(opp):
    """Test with multiple entities in condition."""
    test = await condition.async_from_config(
        opp,
        {
            "condition": "and",
            "conditions": [
                {
                    "alias": "Numeric State Condition",
                    "condition": "numeric_state",
                    "entity_id": ["sensor.temperature_1", "sensor.temperature_2"],
                    "below": 50,
                },
            ],
        },
    )

    opp.states.async_set("sensor.temperature_1", 49)
    opp.states.async_set("sensor.temperature_2", 49)
    assert test(opp)

    opp.states.async_set("sensor.temperature_1", 50)
    opp.states.async_set("sensor.temperature_2", 49)
    assert not test(opp)

    opp.states.async_set("sensor.temperature_1", 49)
    opp.states.async_set("sensor.temperature_2", 50)
    assert not test(opp)


async def test_numeric_state_attribute(opp):
    """Test with numeric state attribute in condition."""
    test = await condition.async_from_config(
        opp,
        {
            "condition": "and",
            "conditions": [
                {
                    "condition": "numeric_state",
                    "entity_id": "sensor.temperature",
                    "attribute": "attribute1",
                    "below": 50,
                },
            ],
        },
    )

    opp.states.async_set("sensor.temperature", 100, {"unkown_attr": 10})
    with pytest.raises(ConditionError):
        assert test(opp)

    opp.states.async_set("sensor.temperature", 100, {"attribute1": 49})
    assert test(opp)

    opp.states.async_set("sensor.temperature", 100, {"attribute1": "49"})
    assert test(opp)

    opp.states.async_set("sensor.temperature", 100, {"attribute1": 51})
    assert not test(opp)

    opp.states.async_set("sensor.temperature", 100, {"attribute1": None})
    with pytest.raises(ConditionError):
        assert test(opp)


async def test_numeric_state_using_input_number(opp):
    """Test numeric_state conditions using input_number entities."""
    await async_setup_component(
        opp,
        "input_number",
        {
            "input_number": {
                "low": {"min": 0, "max": 255, "initial": 10},
                "high": {"min": 0, "max": 255, "initial": 100},
            }
        },
    )

    test = await condition.async_from_config(
        opp,
        {
            "condition": "and",
            "conditions": [
                {
                    "condition": "numeric_state",
                    "entity_id": "sensor.temperature",
                    "below": "input_number.high",
                    "above": "input_number.low",
                },
            ],
        },
    )

    opp.states.async_set("sensor.temperature", 42)
    assert test(opp)

    opp.states.async_set("sensor.temperature", 10)
    assert not test(opp)

    opp.states.async_set("sensor.temperature", 100)
    assert not test(opp)

    opp.states.async_set("input_number.high", "unknown")
    assert not test(opp)

    opp.states.async_set("input_number.high", "unavailable")
    assert not test(opp)

    await opp.services.async_call(
        "input_number",
        "set_value",
        {
            "entity_id": "input_number.high",
            "value": 101,
        },
        blocking=True,
    )
    assert test(opp)

    opp.states.async_set("input_number.low", "unknown")
    assert not test(opp)

    opp.states.async_set("input_number.low", "unavailable")
    assert not test(opp)

    with pytest.raises(ConditionError):
        condition.async_numeric_state(
            opp, entity="sensor.temperature", below="input_number.not_exist"
        )
    with pytest.raises(ConditionError):
        condition.async_numeric_state(
            opp, entity="sensor.temperature", above="input_number.not_exist"
        )


async def test_zone_raises(opp):
    """Test that zone raises ConditionError on errors."""
    test = await condition.async_from_config(
        opp,
        {
            "condition": "zone",
            "entity_id": "device_tracker.cat",
            "zone": "zone.home",
        },
    )

    with pytest.raises(ConditionError, match="no zone"):
        condition.zone(opp, zone_ent=None, entity="sensor.any")

    with pytest.raises(ConditionError, match="unknown zone"):
        test(opp)

    opp.states.async_set(
        "zone.home",
        "zoning",
        {"name": "home", "latitude": 2.1, "longitude": 1.1, "radius": 10},
    )

    with pytest.raises(ConditionError, match="no entity"):
        condition.zone(opp, zone_ent="zone.home", entity=None)

    with pytest.raises(ConditionError, match="unknown entity"):
        test(opp)

    opp.states.async_set(
        "device_tracker.cat",
        "home",
        {"friendly_name": "cat"},
    )

    with pytest.raises(ConditionError, match="latitude"):
        test(opp)

    opp.states.async_set(
        "device_tracker.cat",
        "home",
        {"friendly_name": "cat", "latitude": 2.1},
    )

    with pytest.raises(ConditionError, match="longitude"):
        test(opp)

    opp.states.async_set(
        "device_tracker.cat",
        "home",
        {"friendly_name": "cat", "latitude": 2.1, "longitude": 1.1},
    )

    # All okay, now test multiple failed conditions
    assert test(opp)

    test = await condition.async_from_config(
        opp,
        {
            "condition": "zone",
            "entity_id": ["device_tracker.cat", "device_tracker.dog"],
            "zone": ["zone.home", "zone.work"],
        },
    )

    with pytest.raises(ConditionError, match="dog"):
        test(opp)

    with pytest.raises(ConditionError, match="work"):
        test(opp)

    opp.states.async_set(
        "zone.work",
        "zoning",
        {"name": "work", "latitude": 20, "longitude": 10, "radius": 25000},
    )

    opp.states.async_set(
        "device_tracker.dog",
        "work",
        {"friendly_name": "dog", "latitude": 20.1, "longitude": 10.1},
    )

    assert test(opp)


async def test_zone_multiple_entities(opp):
    """Test with multiple entities in condition."""
    test = await condition.async_from_config(
        opp,
        {
            "condition": "and",
            "conditions": [
                {
                    "alias": "Zone Condition",
                    "condition": "zone",
                    "entity_id": ["device_tracker.person_1", "device_tracker.person_2"],
                    "zone": "zone.home",
                },
            ],
        },
    )

    opp.states.async_set(
        "zone.home",
        "zoning",
        {"name": "home", "latitude": 2.1, "longitude": 1.1, "radius": 10},
    )

    opp.states.async_set(
        "device_tracker.person_1",
        "home",
        {"friendly_name": "person_1", "latitude": 2.1, "longitude": 1.1},
    )
    opp.states.async_set(
        "device_tracker.person_2",
        "home",
        {"friendly_name": "person_2", "latitude": 2.1, "longitude": 1.1},
    )
    assert test(opp)

    opp.states.async_set(
        "device_tracker.person_1",
        "home",
        {"friendly_name": "person_1", "latitude": 20.1, "longitude": 10.1},
    )
    opp.states.async_set(
        "device_tracker.person_2",
        "home",
        {"friendly_name": "person_2", "latitude": 2.1, "longitude": 1.1},
    )
    assert not test(opp)

    opp.states.async_set(
        "device_tracker.person_1",
        "home",
        {"friendly_name": "person_1", "latitude": 2.1, "longitude": 1.1},
    )
    opp.states.async_set(
        "device_tracker.person_2",
        "home",
        {"friendly_name": "person_2", "latitude": 20.1, "longitude": 10.1},
    )
    assert not test(opp)


async def test_multiple_zones(opp):
    """Test with multiple entities in condition."""
    test = await condition.async_from_config(
        opp,
        {
            "condition": "and",
            "conditions": [
                {
                    "condition": "zone",
                    "entity_id": "device_tracker.person",
                    "zone": ["zone.home", "zone.work"],
                },
            ],
        },
    )

    opp.states.async_set(
        "zone.home",
        "zoning",
        {"name": "home", "latitude": 2.1, "longitude": 1.1, "radius": 10},
    )
    opp.states.async_set(
        "zone.work",
        "zoning",
        {"name": "work", "latitude": 20.1, "longitude": 10.1, "radius": 10},
    )

    opp.states.async_set(
        "device_tracker.person",
        "home",
        {"friendly_name": "person", "latitude": 2.1, "longitude": 1.1},
    )
    assert test(opp)

    opp.states.async_set(
        "device_tracker.person",
        "home",
        {"friendly_name": "person", "latitude": 20.1, "longitude": 10.1},
    )
    assert test(opp)

    opp.states.async_set(
        "device_tracker.person",
        "home",
        {"friendly_name": "person", "latitude": 50.1, "longitude": 20.1},
    )
    assert not test(opp)


async def test_extract_entities():
    """Test extracting entities."""
    assert condition.async_extract_entities(
        {
            "condition": "and",
            "conditions": [
                {
                    "condition": "state",
                    "entity_id": "sensor.temperature",
                    "state": "100",
                },
                {
                    "condition": "numeric_state",
                    "entity_id": "sensor.temperature_2",
                    "below": 110,
                },
                {
                    "condition": "not",
                    "conditions": [
                        {
                            "condition": "state",
                            "entity_id": "sensor.temperature_3",
                            "state": "100",
                        },
                        {
                            "condition": "numeric_state",
                            "entity_id": "sensor.temperature_4",
                            "below": 110,
                        },
                    ],
                },
                {
                    "condition": "or",
                    "conditions": [
                        {
                            "condition": "state",
                            "entity_id": "sensor.temperature_5",
                            "state": "100",
                        },
                        {
                            "condition": "numeric_state",
                            "entity_id": "sensor.temperature_6",
                            "below": 110,
                        },
                    ],
                },
                {
                    "condition": "state",
                    "entity_id": ["sensor.temperature_7", "sensor.temperature_8"],
                    "state": "100",
                },
                {
                    "condition": "numeric_state",
                    "entity_id": ["sensor.temperature_9", "sensor.temperature_10"],
                    "below": 110,
                },
                Template("{{ is_state('light.example', 'on') }}"),
            ],
        }
    ) == {
        "sensor.temperature",
        "sensor.temperature_2",
        "sensor.temperature_3",
        "sensor.temperature_4",
        "sensor.temperature_5",
        "sensor.temperature_6",
        "sensor.temperature_7",
        "sensor.temperature_8",
        "sensor.temperature_9",
        "sensor.temperature_10",
    }


async def test_extract_devices():
    """Test extracting devices."""
    assert (
        condition.async_extract_devices(
            {
                "condition": "and",
                "conditions": [
                    {"condition": "device", "device_id": "abcd", "domain": "light"},
                    {"condition": "device", "device_id": "qwer", "domain": "switch"},
                    {
                        "condition": "state",
                        "entity_id": "sensor.not_a_device",
                        "state": "100",
                    },
                    {
                        "condition": "not",
                        "conditions": [
                            {
                                "condition": "device",
                                "device_id": "abcd_not",
                                "domain": "light",
                            },
                            {
                                "condition": "device",
                                "device_id": "qwer_not",
                                "domain": "switch",
                            },
                        ],
                    },
                    {
                        "condition": "or",
                        "conditions": [
                            {
                                "condition": "device",
                                "device_id": "abcd_or",
                                "domain": "light",
                            },
                            {
                                "condition": "device",
                                "device_id": "qwer_or",
                                "domain": "switch",
                            },
                        ],
                    },
                    Template("{{ is_state('light.example', 'on') }}"),
                ],
            }
        )
        == {"abcd", "qwer", "abcd_not", "qwer_not", "abcd_or", "qwer_or"}
    )


async def test_condition_template_error(opp):
    """Test invalid template."""
    test = await condition.async_from_config(
        opp, {"condition": "template", "value_template": "{{ undefined.state }}"}
    )

    with pytest.raises(ConditionError, match="template"):
        test(opp)


async def test_condition_template_invalid_results(opp):
    """Test template condition render false with invalid results."""
    test = await condition.async_from_config(
        opp, {"condition": "template", "value_template": "{{ 'string' }}"}
    )
    assert not test(opp)

    test = await condition.async_from_config(
        opp, {"condition": "template", "value_template": "{{ 10.1 }}"}
    )
    assert not test(opp)

    test = await condition.async_from_config(
        opp, {"condition": "template", "value_template": "{{ 42 }}"}
    )
    assert not test(opp)

    test = await condition.async_from_config(
        opp, {"condition": "template", "value_template": "{{ [1, 2, 3] }}"}
    )
    assert not test(opp)


def _find_run_id(traces, trace_type, item_id):
    """Find newest run_id for a script or automation."""
    for _trace in reversed(traces):
        if _trace["domain"] == trace_type and _trace["item_id"] == item_id:
            return _trace["run_id"]

    return None


async def assert_automation_condition_trace(opp_ws_client, automation_id, expected):
    """Test the result of automation condition."""
    id = 1

    def next_id():
        nonlocal id
        id += 1
        return id

    client = await opp_ws_client()

    # List traces
    await client.send_json(
        {"id": next_id(), "type": "trace/list", "domain": "automation"}
    )
    response = await client.receive_json()
    assert response["success"]
    run_id = _find_run_id(response["result"], "automation", automation_id)

    # Get trace
    await client.send_json(
        {
            "id": next_id(),
            "type": "trace/get",
            "domain": "automation",
            "item_id": "sun",
            "run_id": run_id,
        }
    )
    response = await client.receive_json()
    assert response["success"]
    trace = response["result"]
    assert len(trace["trace"]["condition/0"]) == 1
    condition_trace = trace["trace"]["condition/0"][0]["result"]
    assert condition_trace == expected


async def test_if_action_before_sunrise_no_offset(opp, opp_ws_client, calls):
    """
    Test if action was before sunrise.

    Before sunrise is true from midnight until sunset, local time.
    """
    await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "id": "sun",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "condition": {"condition": "sun", "before": SUN_EVENT_SUNRISE},
                "action": {"service": "test.automation"},
            }
        },
    )

    # sunrise: 2015-09-16 06:33:18 local, sunset: 2015-09-16 18:53:45 local
    # sunrise: 2015-09-16 13:33:18 UTC,   sunset: 2015-09-17 01:53:45 UTC
    # now = sunrise + 1s -> 'before sunrise' not true
    now = datetime(2015, 9, 16, 13, 33, 19, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 0
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_before": "2015-09-16T13:33:18.342542+00:00"},
    )

    # now = sunrise -> 'before sunrise' true
    now = datetime(2015, 9, 16, 13, 33, 18, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 1
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_before": "2015-09-16T13:33:18.342542+00:00"},
    )

    # now = local midnight -> 'before sunrise' true
    now = datetime(2015, 9, 16, 7, 0, 0, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 2
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_before": "2015-09-16T13:33:18.342542+00:00"},
    )

    # now = local midnight - 1s -> 'before sunrise' not true
    now = datetime(2015, 9, 17, 6, 59, 59, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 2
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_before": "2015-09-16T13:33:18.342542+00:00"},
    )


async def test_if_action_after_sunrise_no_offset(opp, opp_ws_client, calls):
    """
    Test if action was after sunrise.

    After sunrise is true from sunrise until midnight, local time.
    """
    await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "id": "sun",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "condition": {"condition": "sun", "after": SUN_EVENT_SUNRISE},
                "action": {"service": "test.automation"},
            }
        },
    )

    # sunrise: 2015-09-16 06:33:18 local, sunset: 2015-09-16 18:53:45 local
    # sunrise: 2015-09-16 13:33:18 UTC,   sunset: 2015-09-17 01:53:45 UTC
    # now = sunrise - 1s -> 'after sunrise' not true
    now = datetime(2015, 9, 16, 13, 33, 17, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 0
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_after": "2015-09-16T13:33:18.342542+00:00"},
    )

    # now = sunrise + 1s -> 'after sunrise' true
    now = datetime(2015, 9, 16, 13, 33, 19, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 1
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_after": "2015-09-16T13:33:18.342542+00:00"},
    )

    # now = local midnight -> 'after sunrise' not true
    now = datetime(2015, 9, 16, 7, 0, 0, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 1
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_after": "2015-09-16T13:33:18.342542+00:00"},
    )

    # now = local midnight - 1s -> 'after sunrise' true
    now = datetime(2015, 9, 17, 6, 59, 59, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 2
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_after": "2015-09-16T13:33:18.342542+00:00"},
    )


async def test_if_action_before_sunrise_with_offset(opp, opp_ws_client, calls):
    """
    Test if action was before sunrise with offset.

    Before sunrise is true from midnight until sunset, local time.
    """
    await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "id": "sun",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "condition": {
                    "condition": "sun",
                    "before": SUN_EVENT_SUNRISE,
                    "before_offset": "+1:00:00",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    # sunrise: 2015-09-16 06:33:18 local, sunset: 2015-09-16 18:53:45 local
    # sunrise: 2015-09-16 13:33:18 UTC,   sunset: 2015-09-17 01:53:45 UTC
    # now = sunrise + 1s + 1h -> 'before sunrise' with offset +1h not true
    now = datetime(2015, 9, 16, 14, 33, 19, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 0
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_before": "2015-09-16T14:33:18.342542+00:00"},
    )

    # now = sunrise + 1h -> 'before sunrise' with offset +1h true
    now = datetime(2015, 9, 16, 14, 33, 18, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 1
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_before": "2015-09-16T14:33:18.342542+00:00"},
    )

    # now = UTC midnight -> 'before sunrise' with offset +1h not true
    now = datetime(2015, 9, 17, 0, 0, 0, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 1
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_before": "2015-09-16T14:33:18.342542+00:00"},
    )

    # now = UTC midnight - 1s -> 'before sunrise' with offset +1h not true
    now = datetime(2015, 9, 16, 23, 59, 59, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 1
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_before": "2015-09-16T14:33:18.342542+00:00"},
    )

    # now = local midnight -> 'before sunrise' with offset +1h true
    now = datetime(2015, 9, 16, 7, 0, 0, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 2
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_before": "2015-09-16T14:33:18.342542+00:00"},
    )

    # now = local midnight - 1s -> 'before sunrise' with offset +1h not true
    now = datetime(2015, 9, 17, 6, 59, 59, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 2
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_before": "2015-09-16T14:33:18.342542+00:00"},
    )

    # now = sunset -> 'before sunrise' with offset +1h not true
    now = datetime(2015, 9, 17, 1, 53, 45, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 2
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_before": "2015-09-16T14:33:18.342542+00:00"},
    )

    # now = sunset -1s -> 'before sunrise' with offset +1h not true
    now = datetime(2015, 9, 17, 1, 53, 44, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 2
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_before": "2015-09-16T14:33:18.342542+00:00"},
    )


async def test_if_action_before_sunset_with_offset(opp, opp_ws_client, calls):
    """
    Test if action was before sunset with offset.

    Before sunset is true from midnight until sunset, local time.
    """
    await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "id": "sun",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "condition": {
                    "condition": "sun",
                    "before": "sunset",
                    "before_offset": "+1:00:00",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    # sunrise: 2015-09-16 06:33:18 local, sunset: 2015-09-16 18:53:45 local
    # sunrise: 2015-09-16 13:33:18 UTC,   sunset: 2015-09-17 01:53:45 UTC
    # now = local midnight -> 'before sunset' with offset +1h true
    now = datetime(2015, 9, 16, 7, 0, 0, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 1
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_before": "2015-09-17T02:53:44.723614+00:00"},
    )

    # now = sunset + 1s + 1h -> 'before sunset' with offset +1h not true
    now = datetime(2015, 9, 17, 2, 53, 46, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 1
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_before": "2015-09-17T02:53:44.723614+00:00"},
    )

    # now = sunset + 1h -> 'before sunset' with offset +1h true
    now = datetime(2015, 9, 17, 2, 53, 44, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 2
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_before": "2015-09-17T02:53:44.723614+00:00"},
    )

    # now = UTC midnight -> 'before sunset' with offset +1h true
    now = datetime(2015, 9, 17, 0, 0, 0, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 3
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_before": "2015-09-17T02:53:44.723614+00:00"},
    )

    # now = UTC midnight - 1s -> 'before sunset' with offset +1h true
    now = datetime(2015, 9, 16, 23, 59, 59, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 4
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_before": "2015-09-17T02:53:44.723614+00:00"},
    )

    # now = sunrise -> 'before sunset' with offset +1h true
    now = datetime(2015, 9, 16, 13, 33, 18, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 5
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_before": "2015-09-17T02:53:44.723614+00:00"},
    )

    # now = sunrise -1s -> 'before sunset' with offset +1h true
    now = datetime(2015, 9, 16, 13, 33, 17, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 6
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_before": "2015-09-17T02:53:44.723614+00:00"},
    )

    # now = local midnight-1s -> 'after sunrise' with offset +1h not true
    now = datetime(2015, 9, 17, 6, 59, 59, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 6
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_before": "2015-09-17T02:53:44.723614+00:00"},
    )


async def test_if_action_after_sunrise_with_offset(opp, opp_ws_client, calls):
    """
    Test if action was after sunrise with offset.

    After sunrise is true from sunrise until midnight, local time.
    """
    await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "id": "sun",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "condition": {
                    "condition": "sun",
                    "after": SUN_EVENT_SUNRISE,
                    "after_offset": "+1:00:00",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    # sunrise: 2015-09-16 06:33:18 local, sunset: 2015-09-16 18:53:45 local
    # sunrise: 2015-09-16 13:33:18 UTC,   sunset: 2015-09-17 01:53:45 UTC
    # now = sunrise - 1s + 1h -> 'after sunrise' with offset +1h not true
    now = datetime(2015, 9, 16, 14, 33, 17, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 0
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_after": "2015-09-16T14:33:18.342542+00:00"},
    )

    # now = sunrise + 1h -> 'after sunrise' with offset +1h true
    now = datetime(2015, 9, 16, 14, 33, 58, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 1
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_after": "2015-09-16T14:33:18.342542+00:00"},
    )

    # now = UTC noon -> 'after sunrise' with offset +1h not true
    now = datetime(2015, 9, 16, 12, 0, 0, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 1
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_after": "2015-09-16T14:33:18.342542+00:00"},
    )

    # now = UTC noon - 1s -> 'after sunrise' with offset +1h not true
    now = datetime(2015, 9, 16, 11, 59, 59, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 1
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_after": "2015-09-16T14:33:18.342542+00:00"},
    )

    # now = local noon -> 'after sunrise' with offset +1h true
    now = datetime(2015, 9, 16, 19, 1, 0, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 2
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_after": "2015-09-16T14:33:18.342542+00:00"},
    )

    # now = local noon - 1s -> 'after sunrise' with offset +1h true
    now = datetime(2015, 9, 16, 18, 59, 59, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 3
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_after": "2015-09-16T14:33:18.342542+00:00"},
    )

    # now = sunset -> 'after sunrise' with offset +1h true
    now = datetime(2015, 9, 17, 1, 53, 45, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 4
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_after": "2015-09-16T14:33:18.342542+00:00"},
    )

    # now = sunset + 1s -> 'after sunrise' with offset +1h true
    now = datetime(2015, 9, 17, 1, 53, 45, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 5
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_after": "2015-09-16T14:33:18.342542+00:00"},
    )

    # now = local midnight-1s -> 'after sunrise' with offset +1h true
    now = datetime(2015, 9, 17, 6, 59, 59, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 6
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_after": "2015-09-16T14:33:18.342542+00:00"},
    )

    # now = local midnight -> 'after sunrise' with offset +1h not true
    now = datetime(2015, 9, 17, 7, 0, 0, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 6
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_after": "2015-09-17T14:33:57.053037+00:00"},
    )


async def test_if_action_after_sunset_with_offset(opp, opp_ws_client, calls):
    """
    Test if action was after sunset with offset.

    After sunset is true from sunset until midnight, local time.
    """
    await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "id": "sun",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "condition": {
                    "condition": "sun",
                    "after": "sunset",
                    "after_offset": "+1:00:00",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    # sunrise: 2015-09-16 06:33:18 local, sunset: 2015-09-16 18:53:45 local
    # sunrise: 2015-09-16 13:33:18 UTC,   sunset: 2015-09-17 01:53:45 UTC
    # now = sunset - 1s + 1h -> 'after sunset' with offset +1h not true
    now = datetime(2015, 9, 17, 2, 53, 44, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 0
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_after": "2015-09-17T02:53:44.723614+00:00"},
    )

    # now = sunset + 1h -> 'after sunset' with offset +1h true
    now = datetime(2015, 9, 17, 2, 53, 45, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 1
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_after": "2015-09-17T02:53:44.723614+00:00"},
    )

    # now = midnight-1s -> 'after sunset' with offset +1h true
    now = datetime(2015, 9, 16, 6, 59, 59, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 2
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_after": "2015-09-16T02:55:06.099767+00:00"},
    )

    # now = midnight -> 'after sunset' with offset +1h not true
    now = datetime(2015, 9, 16, 7, 0, 0, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 2
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_after": "2015-09-17T02:53:44.723614+00:00"},
    )


async def test_if_action_before_and_after_during(opp, opp_ws_client, calls):
    """
    Test if action was after sunset and before sunrise.

    This is true from sunrise until sunset.
    """
    await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "id": "sun",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "condition": {
                    "condition": "sun",
                    "after": SUN_EVENT_SUNRISE,
                    "before": SUN_EVENT_SUNSET,
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    # sunrise: 2015-09-16 06:33:18 local, sunset: 2015-09-16 18:53:45 local
    # sunrise: 2015-09-16 13:33:18 UTC,   sunset: 2015-09-17 01:53:45 UTC
    # now = sunrise - 1s -> 'after sunrise' + 'before sunset' not true
    now = datetime(2015, 9, 16, 13, 33, 17, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 0
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {
            "result": False,
            "wanted_time_before": "2015-09-17T01:53:44.723614+00:00",
            "wanted_time_after": "2015-09-16T13:33:18.342542+00:00",
        },
    )

    # now = sunset + 1s -> 'after sunrise' + 'before sunset' not true
    now = datetime(2015, 9, 17, 1, 53, 46, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 0
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_before": "2015-09-17T01:53:44.723614+00:00"},
    )

    # now = sunrise + 1s -> 'after sunrise' + 'before sunset' true
    now = datetime(2015, 9, 16, 13, 33, 19, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 1
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {
            "result": True,
            "wanted_time_before": "2015-09-17T01:53:44.723614+00:00",
            "wanted_time_after": "2015-09-16T13:33:18.342542+00:00",
        },
    )

    # now = sunset - 1s -> 'after sunrise' + 'before sunset' true
    now = datetime(2015, 9, 17, 1, 53, 44, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 2
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {
            "result": True,
            "wanted_time_before": "2015-09-17T01:53:44.723614+00:00",
            "wanted_time_after": "2015-09-16T13:33:18.342542+00:00",
        },
    )

    # now = 9AM local  -> 'after sunrise' + 'before sunset' true
    now = datetime(2015, 9, 16, 16, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 3
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {
            "result": True,
            "wanted_time_before": "2015-09-17T01:53:44.723614+00:00",
            "wanted_time_after": "2015-09-16T13:33:18.342542+00:00",
        },
    )


async def test_if_action_before_sunrise_no_offset_kotzebue(opp, opp_ws_client, calls):
    """
    Test if action was before sunrise.

    Local timezone: Alaska time
    Location: Kotzebue, which has a very skewed local timezone with sunrise
    at 7 AM and sunset at 3AM during summer
    After sunrise is true from sunrise until midnight, local time.
    """
    tz = dt_util.get_time_zone("America/Anchorage")
    dt_util.set_default_time_zone(tz)
    opp.config.latitude = 66.5
    opp.config.longitude = 162.4
    await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "id": "sun",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "condition": {"condition": "sun", "before": SUN_EVENT_SUNRISE},
                "action": {"service": "test.automation"},
            }
        },
    )

    # sunrise: 2015-07-24 07:21:12 local, sunset: 2015-07-25 03:13:33 local
    # sunrise: 2015-07-24 15:21:12 UTC,   sunset: 2015-07-25 11:13:33 UTC
    # now = sunrise + 1s -> 'before sunrise' not true
    now = datetime(2015, 7, 24, 15, 21, 13, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 0
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_before": "2015-07-24T15:16:46.975735+00:00"},
    )

    # now = sunrise - 1h -> 'before sunrise' true
    now = datetime(2015, 7, 24, 14, 21, 12, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 1
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_before": "2015-07-24T15:16:46.975735+00:00"},
    )

    # now = local midnight -> 'before sunrise' true
    now = datetime(2015, 7, 24, 8, 0, 0, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 2
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_before": "2015-07-24T15:16:46.975735+00:00"},
    )

    # now = local midnight - 1s -> 'before sunrise' not true
    now = datetime(2015, 7, 24, 7, 59, 59, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 2
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_before": "2015-07-23T15:12:19.155123+00:00"},
    )


async def test_if_action_after_sunrise_no_offset_kotzebue(opp, opp_ws_client, calls):
    """
    Test if action was after sunrise.

    Local timezone: Alaska time
    Location: Kotzebue, which has a very skewed local timezone with sunrise
    at 7 AM and sunset at 3AM during summer
    Before sunrise is true from midnight until sunrise, local time.
    """
    tz = dt_util.get_time_zone("America/Anchorage")
    dt_util.set_default_time_zone(tz)
    opp.config.latitude = 66.5
    opp.config.longitude = 162.4
    await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "id": "sun",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "condition": {"condition": "sun", "after": SUN_EVENT_SUNRISE},
                "action": {"service": "test.automation"},
            }
        },
    )

    # sunrise: 2015-07-24 07:21:12 local, sunset: 2015-07-25 03:13:33 local
    # sunrise: 2015-07-24 15:21:12 UTC,   sunset: 2015-07-25 11:13:33 UTC
    # now = sunrise -> 'after sunrise' true
    now = datetime(2015, 7, 24, 15, 21, 12, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 1
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_after": "2015-07-24T15:16:46.975735+00:00"},
    )

    # now = sunrise - 1h -> 'after sunrise' not true
    now = datetime(2015, 7, 24, 14, 21, 12, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 1
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_after": "2015-07-24T15:16:46.975735+00:00"},
    )

    # now = local midnight -> 'after sunrise' not true
    now = datetime(2015, 7, 24, 8, 0, 1, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 1
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_after": "2015-07-24T15:16:46.975735+00:00"},
    )

    # now = local midnight - 1s -> 'after sunrise' true
    now = datetime(2015, 7, 24, 7, 59, 59, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 2
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_after": "2015-07-23T15:12:19.155123+00:00"},
    )


async def test_if_action_before_sunset_no_offset_kotzebue(opp, opp_ws_client, calls):
    """
    Test if action was before sunrise.

    Local timezone: Alaska time
    Location: Kotzebue, which has a very skewed local timezone with sunrise
    at 7 AM and sunset at 3AM during summer
    Before sunset is true from midnight until sunset, local time.
    """
    tz = dt_util.get_time_zone("America/Anchorage")
    dt_util.set_default_time_zone(tz)
    opp.config.latitude = 66.5
    opp.config.longitude = 162.4
    await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "id": "sun",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "condition": {"condition": "sun", "before": SUN_EVENT_SUNSET},
                "action": {"service": "test.automation"},
            }
        },
    )

    # sunrise: 2015-07-24 07:21:12 local, sunset: 2015-07-25 03:13:33 local
    # sunrise: 2015-07-24 15:21:12 UTC,   sunset: 2015-07-25 11:13:33 UTC
    # now = sunset + 1s -> 'before sunset' not true
    now = datetime(2015, 7, 25, 11, 13, 34, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 0
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_before": "2015-07-25T11:13:32.501837+00:00"},
    )

    # now = sunset - 1h-> 'before sunset' true
    now = datetime(2015, 7, 25, 10, 13, 33, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 1
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_before": "2015-07-25T11:13:32.501837+00:00"},
    )

    # now = local midnight -> 'before sunrise' true
    now = datetime(2015, 7, 24, 8, 0, 0, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 2
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_before": "2015-07-24T11:17:54.446913+00:00"},
    )

    # now = local midnight - 1s -> 'before sunrise' not true
    now = datetime(2015, 7, 24, 7, 59, 59, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 2
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_before": "2015-07-23T11:22:18.467277+00:00"},
    )


async def test_if_action_after_sunset_no_offset_kotzebue(opp, opp_ws_client, calls):
    """
    Test if action was after sunrise.

    Local timezone: Alaska time
    Location: Kotzebue, which has a very skewed local timezone with sunrise
    at 7 AM and sunset at 3AM during summer
    After sunset is true from sunset until midnight, local time.
    """
    tz = dt_util.get_time_zone("America/Anchorage")
    dt_util.set_default_time_zone(tz)
    opp.config.latitude = 66.5
    opp.config.longitude = 162.4
    await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "id": "sun",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "condition": {"condition": "sun", "after": SUN_EVENT_SUNSET},
                "action": {"service": "test.automation"},
            }
        },
    )

    # sunrise: 2015-07-24 07:21:12 local, sunset: 2015-07-25 03:13:33 local
    # sunrise: 2015-07-24 15:21:12 UTC,   sunset: 2015-07-25 11:13:33 UTC
    # now = sunset -> 'after sunset' true
    now = datetime(2015, 7, 25, 11, 13, 33, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 1
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_after": "2015-07-25T11:13:32.501837+00:00"},
    )

    # now = sunset - 1s -> 'after sunset' not true
    now = datetime(2015, 7, 25, 11, 13, 32, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 1
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_after": "2015-07-25T11:13:32.501837+00:00"},
    )

    # now = local midnight -> 'after sunset' not true
    now = datetime(2015, 7, 24, 8, 0, 1, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 1
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": False, "wanted_time_after": "2015-07-24T11:17:54.446913+00:00"},
    )

    # now = local midnight - 1s -> 'after sunset' true
    now = datetime(2015, 7, 24, 7, 59, 59, tzinfo=dt_util.UTC)
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 2
    await assert_automation_condition_trace(
        opp_ws_client,
        "sun",
        {"result": True, "wanted_time_after": "2015-07-23T11:22:18.467277+00:00"},
    )
