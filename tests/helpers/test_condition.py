"""Test the condition helper."""
from logging import WARNING
from unittest.mock import patch

import pytest

from openpeerpower.exceptions import ConditionError, OpenPeerPowerError
from openpeerpower.helpers import condition
from openpeerpower.helpers.template import Template
from openpeerpower.setup import async_setup_component
from openpeerpower.util import dt


async def test_invalid_condition.opp):
    """Test if invalid condition raises."""
    with pytest.raises(OpenPeerPowerError):
        await condition.async_from_config(
           .opp,
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


async def test_and_condition.opp):
    """Test the 'and' condition."""
    test = await condition.async_from_config(
       .opp,
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
        test.opp)

   .opp.states.async_set("sensor.temperature", 120)
    assert not test.opp)

   .opp.states.async_set("sensor.temperature", 105)
    assert not test.opp)

   .opp.states.async_set("sensor.temperature", 100)
    assert test.opp)


async def test_and_condition_with_template.opp):
    """Test the 'and' condition."""
    test = await condition.async_from_config(
       .opp,
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

   .opp.states.async_set("sensor.temperature", 120)
    assert not test.opp)

   .opp.states.async_set("sensor.temperature", 105)
    assert not test.opp)

   .opp.states.async_set("sensor.temperature", 100)
    assert test.opp)


async def test_or_condition.opp):
    """Test the 'or' condition."""
    test = await condition.async_from_config(
       .opp,
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
        test.opp)

   .opp.states.async_set("sensor.temperature", 120)
    assert not test.opp)

   .opp.states.async_set("sensor.temperature", 105)
    assert test.opp)

   .opp.states.async_set("sensor.temperature", 100)
    assert test.opp)


async def test_or_condition_with_template.opp):
    """Test the 'or' condition."""
    test = await condition.async_from_config(
       .opp,
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

   .opp.states.async_set("sensor.temperature", 120)
    assert not test.opp)

   .opp.states.async_set("sensor.temperature", 105)
    assert test.opp)

   .opp.states.async_set("sensor.temperature", 100)
    assert test.opp)


async def test_not_condition.opp):
    """Test the 'not' condition."""
    test = await condition.async_from_config(
       .opp,
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
        test.opp)

   .opp.states.async_set("sensor.temperature", 101)
    assert test.opp)

   .opp.states.async_set("sensor.temperature", 50)
    assert test.opp)

   .opp.states.async_set("sensor.temperature", 49)
    assert not test.opp)

   .opp.states.async_set("sensor.temperature", 100)
    assert not test.opp)


async def test_not_condition_with_template.opp):
    """Test the 'or' condition."""
    test = await condition.async_from_config(
       .opp,
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

   .opp.states.async_set("sensor.temperature", 101)
    assert test.opp)

   .opp.states.async_set("sensor.temperature", 50)
    assert test.opp)

   .opp.states.async_set("sensor.temperature", 49)
    assert not test.opp)

   .opp.states.async_set("sensor.temperature", 100)
    assert not test.opp)


async def test_time_window.opp):
    """Test time condition windows."""
    sixam = "06:00:00"
    sixpm = "18:00:00"

    test1 = await condition.async_from_config(
       .opp,
        {"alias": "Time Cond", "condition": "time", "after": sixam, "before": sixpm},
    )
    test2 = await condition.async_from_config(
       .opp,
        {"alias": "Time Cond", "condition": "time", "after": sixpm, "before": sixam},
    )

    with patch(
        "openpeerpower.helpers.condition.dt_util.now",
        return_value=dt.now().replace(hour=3),
    ):
        assert not test1.opp)
        assert test2.opp)

    with patch(
        "openpeerpower.helpers.condition.dt_util.now",
        return_value=dt.now().replace(hour=9),
    ):
        assert test1.opp)
        assert not test2.opp)

    with patch(
        "openpeerpower.helpers.condition.dt_util.now",
        return_value=dt.now().replace(hour=15),
    ):
        assert test1.opp)
        assert not test2.opp)

    with patch(
        "openpeerpower.helpers.condition.dt_util.now",
        return_value=dt.now().replace(hour=21),
    ):
        assert not test1.opp)
        assert test2.opp)


async def test_time_using_input_datetime.opp):
    """Test time conditions using input_datetime entities."""
    await async_setup_component(
       .opp,
        "input_datetime",
        {
            "input_datetime": {
                "am": {"has_date": True, "has_time": True},
                "pm": {"has_date": True, "has_time": True},
            }
        },
    )

    await.opp.services.async_call(
        "input_datetime",
        "set_datetime",
        {
            "entity_id": "input_datetime.am",
            "datetime": str(
                dt.now()
                .replace(hour=6, minute=0, second=0, microsecond=0)
                .replace(tzinfo=None)
            ),
        },
        blocking=True,
    )

    await.opp.services.async_call(
        "input_datetime",
        "set_datetime",
        {
            "entity_id": "input_datetime.pm",
            "datetime": str(
                dt.now()
                .replace(hour=18, minute=0, second=0, microsecond=0)
                .replace(tzinfo=None)
            ),
        },
        blocking=True,
    )

    with patch(
        "openpeerpower.helpers.condition.dt_util.now",
        return_value=dt.now().replace(hour=3),
    ):
        assert not condition.time(
           .opp, after="input_datetime.am", before="input_datetime.pm"
        )
        assert condition.time(
           .opp, after="input_datetime.pm", before="input_datetime.am"
        )

    with patch(
        "openpeerpower.helpers.condition.dt_util.now",
        return_value=dt.now().replace(hour=9),
    ):
        assert condition.time(
           .opp, after="input_datetime.am", before="input_datetime.pm"
        )
        assert not condition.time(
           .opp, after="input_datetime.pm", before="input_datetime.am"
        )

    with patch(
        "openpeerpower.helpers.condition.dt_util.now",
        return_value=dt.now().replace(hour=15),
    ):
        assert condition.time(
           .opp, after="input_datetime.am", before="input_datetime.pm"
        )
        assert not condition.time(
           .opp, after="input_datetime.pm", before="input_datetime.am"
        )

    with patch(
        "openpeerpower.helpers.condition.dt_util.now",
        return_value=dt.now().replace(hour=21),
    ):
        assert not condition.time(
           .opp, after="input_datetime.am", before="input_datetime.pm"
        )
        assert condition.time(
           .opp, after="input_datetime.pm", before="input_datetime.am"
        )

    with pytest.raises(ConditionError):
        condition.time.opp, after="input_datetime.not_existing")

    with pytest.raises(ConditionError):
        condition.time.opp, before="input_datetime.not_existing")


async def test_if_numeric_state_raises_on_unavailable.opp, caplog):
    """Test numeric_state raises on unavailable/unknown state."""
    test = await condition.async_from_config(
       .opp,
        {"condition": "numeric_state", "entity_id": "sensor.temperature", "below": 42},
    )

    caplog.clear()
    caplog.set_level(WARNING)

   .opp.states.async_set("sensor.temperature", "unavailable")
    with pytest.raises(ConditionError):
        test.opp)
    assert len(caplog.record_tuples) == 0

   .opp.states.async_set("sensor.temperature", "unknown")
    with pytest.raises(ConditionError):
        test.opp)
    assert len(caplog.record_tuples) == 0


async def test_state_raises.opp):
    """Test that state raises ConditionError on errors."""
    # Unknown entity_id
    with pytest.raises(ConditionError, match="Unknown entity"):
        test = await condition.async_from_config(
           .opp,
            {
                "condition": "state",
                "entity_id": "sensor.door_unknown",
                "state": "open",
            },
        )

        test.opp)

    # Unknown attribute
    with pytest.raises(ConditionError, match=r"Attribute .* does not exist"):
        test = await condition.async_from_config(
           .opp,
            {
                "condition": "state",
                "entity_id": "sensor.door",
                "attribute": "model",
                "state": "acme",
            },
        )

       .opp.states.async_set("sensor.door", "open")
        test.opp)


async def test_state_multiple_entities.opp):
    """Test with multiple entities in condition."""
    test = await condition.async_from_config(
       .opp,
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

   .opp.states.async_set("sensor.temperature_1", 100)
   .opp.states.async_set("sensor.temperature_2", 100)
    assert test.opp)

   .opp.states.async_set("sensor.temperature_1", 101)
   .opp.states.async_set("sensor.temperature_2", 100)
    assert not test.opp)

   .opp.states.async_set("sensor.temperature_1", 100)
   .opp.states.async_set("sensor.temperature_2", 101)
    assert not test.opp)


async def test_multiple_states.opp):
    """Test with multiple states in condition."""
    test = await condition.async_from_config(
       .opp,
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

   .opp.states.async_set("sensor.temperature", 100)
    assert test.opp)

   .opp.states.async_set("sensor.temperature", 200)
    assert test.opp)

   .opp.states.async_set("sensor.temperature", 42)
    assert not test.opp)


async def test_state_attribute.opp):
    """Test with state attribute in condition."""
    test = await condition.async_from_config(
       .opp,
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

   .opp.states.async_set("sensor.temperature", 100, {"unkown_attr": 200})
    with pytest.raises(ConditionError):
        test.opp)

   .opp.states.async_set("sensor.temperature", 100, {"attribute1": 200})
    assert test.opp)

   .opp.states.async_set("sensor.temperature", 100, {"attribute1": "200"})
    assert not test.opp)

   .opp.states.async_set("sensor.temperature", 100, {"attribute1": 201})
    assert not test.opp)

   .opp.states.async_set("sensor.temperature", 100, {"attribute1": None})
    assert not test.opp)


async def test_state_attribute_boolean.opp):
    """Test with boolean state attribute in condition."""
    test = await condition.async_from_config(
       .opp,
        {
            "condition": "state",
            "entity_id": "sensor.temperature",
            "attribute": "happening",
            "state": False,
        },
    )

   .opp.states.async_set("sensor.temperature", 100, {"happening": 200})
    assert not test.opp)

   .opp.states.async_set("sensor.temperature", 100, {"happening": True})
    assert not test.opp)

   .opp.states.async_set("sensor.temperature", 100, {"no_happening": 201})
    with pytest.raises(ConditionError):
        test.opp)

   .opp.states.async_set("sensor.temperature", 100, {"happening": False})
    assert test.opp)


async def test_state_using_input_entities.opp):
    """Test state conditions using input_* entities."""
    await async_setup_component(
       .opp,
        "input_text",
        {
            "input_text": {
                "hello": {"initial": "goodbye"},
            }
        },
    )

    await async_setup_component(
       .opp,
        "input_select",
        {
            "input_select": {
                "hello": {"options": ["cya", "goodbye", "welcome"], "initial": "cya"},
            }
        },
    )

    test = await condition.async_from_config(
       .opp,
        {
            "condition": "and",
            "conditions": [
                {
                    "condition": "state",
                    "entity_id": "sensor.salut",
                    "state": [
                        "input_text.hello",
                        "input_select.hello",
                        "input_number.not_exist",
                        "salut",
                    ],
                },
            ],
        },
    )

   .opp.states.async_set("sensor.salut", "goodbye")
    assert test.opp)

   .opp.states.async_set("sensor.salut", "salut")
    assert test.opp)

   .opp.states.async_set("sensor.salut", "hello")
    assert not test.opp)

    await.opp.services.async_call(
        "input_text",
        "set_value",
        {
            "entity_id": "input_text.hello",
            "value": "hi",
        },
        blocking=True,
    )
    assert not test.opp)

   .opp.states.async_set("sensor.salut", "hi")
    assert test.opp)

   .opp.states.async_set("sensor.salut", "cya")
    assert test.opp)

    await.opp.services.async_call(
        "input_select",
        "select_option",
        {
            "entity_id": "input_select.hello",
            "option": "welcome",
        },
        blocking=True,
    )
    assert not test.opp)

   .opp.states.async_set("sensor.salut", "welcome")
    assert test.opp)


async def test_numeric_state_raises.opp):
    """Test that numeric_state raises ConditionError on errors."""
    # Unknown entity_id
    with pytest.raises(ConditionError, match="Unknown entity"):
        test = await condition.async_from_config(
           .opp,
            {
                "condition": "numeric_state",
                "entity_id": "sensor.temperature_unknown",
                "above": 0,
            },
        )

        test.opp)

    # Unknown attribute
    with pytest.raises(ConditionError, match=r"Attribute .* does not exist"):
        test = await condition.async_from_config(
           .opp,
            {
                "condition": "numeric_state",
                "entity_id": "sensor.temperature",
                "attribute": "temperature",
                "above": 0,
            },
        )

       .opp.states.async_set("sensor.temperature", 50)
        test.opp)

    # Template error
    with pytest.raises(ConditionError, match="ZeroDivisionError"):
        test = await condition.async_from_config(
           .opp,
            {
                "condition": "numeric_state",
                "entity_id": "sensor.temperature",
                "value_template": "{{ 1 / 0 }}",
                "above": 0,
            },
        )

       .opp.states.async_set("sensor.temperature", 50)
        test.opp)

    # Unavailable state
    with pytest.raises(ConditionError, match="State is not available"):
        test = await condition.async_from_config(
           .opp,
            {
                "condition": "numeric_state",
                "entity_id": "sensor.temperature",
                "above": 0,
            },
        )

       .opp.states.async_set("sensor.temperature", "unavailable")
        test.opp)

    # Bad number
    with pytest.raises(ConditionError, match="cannot be processed as a number"):
        test = await condition.async_from_config(
           .opp,
            {
                "condition": "numeric_state",
                "entity_id": "sensor.temperature",
                "above": 0,
            },
        )

       .opp.states.async_set("sensor.temperature", "fifty")
        test.opp)

    # Below entity missing
    with pytest.raises(ConditionError, match="below entity"):
        test = await condition.async_from_config(
           .opp,
            {
                "condition": "numeric_state",
                "entity_id": "sensor.temperature",
                "below": "input_number.missing",
            },
        )

       .opp.states.async_set("sensor.temperature", 50)
        test.opp)

    # Above entity missing
    with pytest.raises(ConditionError, match="above entity"):
        test = await condition.async_from_config(
           .opp,
            {
                "condition": "numeric_state",
                "entity_id": "sensor.temperature",
                "above": "input_number.missing",
            },
        )

       .opp.states.async_set("sensor.temperature", 50)
        test.opp)


async def test_numeric_state_multiple_entities.opp):
    """Test with multiple entities in condition."""
    test = await condition.async_from_config(
       .opp,
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

   .opp.states.async_set("sensor.temperature_1", 49)
   .opp.states.async_set("sensor.temperature_2", 49)
    assert test.opp)

   .opp.states.async_set("sensor.temperature_1", 50)
   .opp.states.async_set("sensor.temperature_2", 49)
    assert not test.opp)

   .opp.states.async_set("sensor.temperature_1", 49)
   .opp.states.async_set("sensor.temperature_2", 50)
    assert not test.opp)


async def test_numeric_state_attribute.opp):
    """Test with numeric state attribute in condition."""
    test = await condition.async_from_config(
       .opp,
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

   .opp.states.async_set("sensor.temperature", 100, {"unkown_attr": 10})
    with pytest.raises(ConditionError):
        assert test.opp)

   .opp.states.async_set("sensor.temperature", 100, {"attribute1": 49})
    assert test.opp)

   .opp.states.async_set("sensor.temperature", 100, {"attribute1": "49"})
    assert test.opp)

   .opp.states.async_set("sensor.temperature", 100, {"attribute1": 51})
    assert not test.opp)

   .opp.states.async_set("sensor.temperature", 100, {"attribute1": None})
    with pytest.raises(ConditionError):
        assert test.opp)


async def test_numeric_state_using_input_number.opp):
    """Test numeric_state conditions using input_number entities."""
    await async_setup_component(
       .opp,
        "input_number",
        {
            "input_number": {
                "low": {"min": 0, "max": 255, "initial": 10},
                "high": {"min": 0, "max": 255, "initial": 100},
            }
        },
    )

    test = await condition.async_from_config(
       .opp,
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

   .opp.states.async_set("sensor.temperature", 42)
    assert test.opp)

   .opp.states.async_set("sensor.temperature", 10)
    assert not test.opp)

   .opp.states.async_set("sensor.temperature", 100)
    assert not test.opp)

    await.opp.services.async_call(
        "input_number",
        "set_value",
        {
            "entity_id": "input_number.high",
            "value": 101,
        },
        blocking=True,
    )
    assert test.opp)

    with pytest.raises(ConditionError):
        condition.async_numeric_state(
           .opp, entity="sensor.temperature", below="input_number.not_exist"
        )
    with pytest.raises(ConditionError):
        condition.async_numeric_state(
           .opp, entity="sensor.temperature", above="input_number.not_exist"
        )


async def test_zone_raises.opp):
    """Test that zone raises ConditionError on errors."""
    test = await condition.async_from_config(
       .opp,
        {
            "condition": "zone",
            "entity_id": "device_tracker.cat",
            "zone": "zone.home",
        },
    )

    with pytest.raises(ConditionError, match="Unknown zone"):
        test.opp)

   .opp.states.async_set(
        "zone.home",
        "zoning",
        {"name": "home", "latitude": 2.1, "longitude": 1.1, "radius": 10},
    )

    with pytest.raises(ConditionError, match="Unknown entity"):
        test.opp)

   .opp.states.async_set(
        "device_tracker.cat",
        "home",
        {"friendly_name": "cat"},
    )

    with pytest.raises(ConditionError, match="latitude"):
        test.opp)

   .opp.states.async_set(
        "device_tracker.cat",
        "home",
        {"friendly_name": "cat", "latitude": 2.1},
    )

    with pytest.raises(ConditionError, match="longitude"):
        test.opp)

   .opp.states.async_set(
        "device_tracker.cat",
        "home",
        {"friendly_name": "cat", "latitude": 2.1, "longitude": 1.1},
    )

    # All okay, now test multiple failed conditions
    assert test.opp)

    test = await condition.async_from_config(
       .opp,
        {
            "condition": "zone",
            "entity_id": ["device_tracker.cat", "device_tracker.dog"],
            "zone": ["zone.home", "zone.work"],
        },
    )

    with pytest.raises(ConditionError, match="dog"):
        test.opp)

    with pytest.raises(ConditionError, match="work"):
        test.opp)

   .opp.states.async_set(
        "zone.work",
        "zoning",
        {"name": "work", "latitude": 20, "longitude": 10, "radius": 25000},
    )

   .opp.states.async_set(
        "device_tracker.dog",
        "work",
        {"friendly_name": "dog", "latitude": 20.1, "longitude": 10.1},
    )

    assert test.opp)


async def test_zone_multiple_entities.opp):
    """Test with multiple entities in condition."""
    test = await condition.async_from_config(
       .opp,
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

   .opp.states.async_set(
        "zone.home",
        "zoning",
        {"name": "home", "latitude": 2.1, "longitude": 1.1, "radius": 10},
    )

   .opp.states.async_set(
        "device_tracker.person_1",
        "home",
        {"friendly_name": "person_1", "latitude": 2.1, "longitude": 1.1},
    )
   .opp.states.async_set(
        "device_tracker.person_2",
        "home",
        {"friendly_name": "person_2", "latitude": 2.1, "longitude": 1.1},
    )
    assert test.opp)

   .opp.states.async_set(
        "device_tracker.person_1",
        "home",
        {"friendly_name": "person_1", "latitude": 20.1, "longitude": 10.1},
    )
   .opp.states.async_set(
        "device_tracker.person_2",
        "home",
        {"friendly_name": "person_2", "latitude": 2.1, "longitude": 1.1},
    )
    assert not test.opp)

   .opp.states.async_set(
        "device_tracker.person_1",
        "home",
        {"friendly_name": "person_1", "latitude": 2.1, "longitude": 1.1},
    )
   .opp.states.async_set(
        "device_tracker.person_2",
        "home",
        {"friendly_name": "person_2", "latitude": 20.1, "longitude": 10.1},
    )
    assert not test.opp)


async def test_multiple_zones.opp):
    """Test with multiple entities in condition."""
    test = await condition.async_from_config(
       .opp,
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

   .opp.states.async_set(
        "zone.home",
        "zoning",
        {"name": "home", "latitude": 2.1, "longitude": 1.1, "radius": 10},
    )
   .opp.states.async_set(
        "zone.work",
        "zoning",
        {"name": "work", "latitude": 20.1, "longitude": 10.1, "radius": 10},
    )

   .opp.states.async_set(
        "device_tracker.person",
        "home",
        {"friendly_name": "person", "latitude": 2.1, "longitude": 1.1},
    )
    assert test.opp)

   .opp.states.async_set(
        "device_tracker.person",
        "home",
        {"friendly_name": "person", "latitude": 20.1, "longitude": 10.1},
    )
    assert test.opp)

   .opp.states.async_set(
        "device_tracker.person",
        "home",
        {"friendly_name": "person", "latitude": 50.1, "longitude": 20.1},
    )
    assert not test.opp)


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
       .opp, {"condition": "template", "value_template": "{{ undefined.state }}"}
    )

    with pytest.raises(ConditionError, match="template"):
        test.opp)


async def test_condition_template_invalid_results.opp):
    """Test template condition render false with invalid results."""
    test = await condition.async_from_config(
       .opp, {"condition": "template", "value_template": "{{ 'string' }}"}
    )
    assert not test.opp)

    test = await condition.async_from_config(
       .opp, {"condition": "template", "value_template": "{{ 10.1 }}"}
    )
    assert not test.opp)

    test = await condition.async_from_config(
       .opp, {"condition": "template", "value_template": "{{ 42 }}"}
    )
    assert not test.opp)

    test = await condition.async_from_config(
       .opp, {"condition": "template", "value_template": "{{ [1, 2, 3] }}"}
    )
    assert not test.opp)
