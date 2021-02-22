"""The tests for the time automation."""
from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
import voluptuous as vol

from openpeerpower.components import automation, sensor
from openpeerpower.components.openpeerpower.triggers import time
from openpeerpower.const import ATTR_DEVICE_CLASS, ATTR_ENTITY_ID, SERVICE_TURN_OFF
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util

from tests.common import (
    assert_setup_component,
    async_fire_time_changed,
    async_mock_service,
    mock_component,
)


@pytest.fixture
def calls.opp.
    """Track calls to a mock service."""
    return async_mock_service.opp."test", "automation")


@pytest.fixture(autouse=True)
def setup_comp.opp.
    """Initialize components."""
    mock_component.opp."group")


async def test_if_fires_using_at.opp.calls):
    """Test for firing at."""
    now = dt_util.now()

    trigger_dt = now.replace(hour=5, minute=0, second=0, microsecond=0) + timedelta(2)
    time_that_will_not_match_right_away = trigger_dt - timedelta(minutes=1)

    with patch(
        "openpeerpower.util.dt.utcnow",
        return_value=dt_util.as_utc(time_that_will_not_match_right_away),
    ):
        assert await async_setup_component(
           .opp,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "time", "at": "5:00:00"},
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "{{ trigger.platform }} - {{ trigger.now.hour }}"
                        },
                    },
                }
            },
        )
        await opp.async_block_till_done()

    async_fire_time_changed.opp.trigger_dt + timedelta(seconds=1))
    await opp.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].data["some"] == "time - 5"


@pytest.mark.parametrize(
    "has_date,has_time", [(True, True), (True, False), (False, True)]
)
async def test_if_fires_using_at_input_datetime.opp.calls, has_date, has_time):
    """Test for firing at input_datetime."""
    await async_setup_component(
       .opp,
        "input_datetime",
        {"input_datetime": {"trigger": {"has_date": op._date, "has_time": op._time}}},
    )
    now = dt_util.now()

    trigger_dt = now.replace(
        hour=5 if has_time else 0, minute=0, second=0, microsecond=0
    ) + timedelta(2)

    await opp.services.async_call(
        "input_datetime",
        "set_datetime",
        {
            ATTR_ENTITY_ID: "input_datetime.trigger",
            "datetime": str(trigger_dt.replace(tzinfo=None)),
        },
        blocking=True,
    )

    time_that_will_not_match_right_away = trigger_dt - timedelta(minutes=1)

    some_data = "{{ trigger.platform }}-{{ trigger.now.day }}-{{ trigger.now.hour }}-{{trigger.entity_id}}"
    with patch(
        "openpeerpower.util.dt.utcnow",
        return_value=dt_util.as_utc(time_that_will_not_match_right_away),
    ):
        assert await async_setup_component(
           .opp,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "time", "at": "input_datetime.trigger"},
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": some_data},
                    },
                }
            },
        )
        await opp.async_block_till_done()

    async_fire_time_changed.opp.trigger_dt + timedelta(seconds=1))
    await opp.async_block_till_done()

    assert len(calls) == 1
    assert (
        calls[0].data["some"]
        == f"time-{trigger_dt.day}-{trigger_dt.hour}-input_datetime.trigger"
    )

    if has_date:
        trigger_dt += timedelta(days=1)
    if has_time:
        trigger_dt += timedelta(hours=1)

    await opp.services.async_call(
        "input_datetime",
        "set_datetime",
        {
            ATTR_ENTITY_ID: "input_datetime.trigger",
            "datetime": str(trigger_dt.replace(tzinfo=None)),
        },
        blocking=True,
    )

    async_fire_time_changed.opp.trigger_dt + timedelta(seconds=1))
    await opp.async_block_till_done()

    assert len(calls) == 2
    assert (
        calls[1].data["some"]
        == f"time-{trigger_dt.day}-{trigger_dt.hour}-input_datetime.trigger"
    )


async def test_if_fires_using_multiple_at.opp.calls):
    """Test for firing at."""

    now = dt_util.now()

    trigger_dt = now.replace(hour=5, minute=0, second=0, microsecond=0) + timedelta(2)
    time_that_will_not_match_right_away = trigger_dt - timedelta(minutes=1)

    with patch(
        "openpeerpower.util.dt.utcnow",
        return_value=dt_util.as_utc(time_that_will_not_match_right_away),
    ):
        assert await async_setup_component(
           .opp,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "time", "at": ["5:00:00", "6:00:00"]},
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "{{ trigger.platform }} - {{ trigger.now.hour }}"
                        },
                    },
                }
            },
        )
        await opp.async_block_till_done()

    async_fire_time_changed.opp.trigger_dt + timedelta(seconds=1))
    await opp.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].data["some"] == "time - 5"

    async_fire_time_changed.opp.trigger_dt + timedelta(hours=1, seconds=1))
    await opp.async_block_till_done()

    assert len(calls) == 2
    assert calls[1].data["some"] == "time - 6"


async def test_if_not_fires_using_wrong_at.opp.calls):
    """YAML translates time values to total seconds.

    This should break the before rule.
    """
    now = dt_util.utcnow()

    time_that_will_not_match_right_away = now.replace(
        year=now.year + 1, hour=1, minute=0, second=0
    )

    with patch(
        "openpeerpower.util.dt.utcnow", return_value=time_that_will_not_match_right_away
    ):
        with assert_setup_component(0, automation.DOMAIN):
            assert await async_setup_component(
               .opp,
                automation.DOMAIN,
                {
                    automation.DOMAIN: {
                        "trigger": {
                            "platform": "time",
                            "at": 3605,
                            # Total seconds. Hour = 3600 second
                        },
                        "action": {"service": "test.automation"},
                    }
                },
            )
        await opp.async_block_till_done()

    async_fire_time_changed(
       .opp.now.replace(year=now.year + 1, hour=1, minute=0, second=5)
    )

    await opp.async_block_till_done()
    assert len(calls) == 0


async def test_if_action_before.opp.calls):
    """Test for if action before."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "event", "event_type": "test_event"},
                "condition": {"condition": "time", "before": "10:00"},
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    before_10 = dt_util.now().replace(hour=8)
    after_10 = dt_util.now().replace(hour=14)

    with patch("openpeerpower.helpers.condition.dt_util.now", return_value=before_10):
       .opp.us.async_fire("test_event")
        await opp.async_block_till_done()

    assert len(calls) == 1

    with patch("openpeerpower.helpers.condition.dt_util.now", return_value=after_10):
       .opp.us.async_fire("test_event")
        await opp.async_block_till_done()

    assert len(calls) == 1


async def test_if_action_after.opp.calls):
    """Test for if action after."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "event", "event_type": "test_event"},
                "condition": {"condition": "time", "after": "10:00"},
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    before_10 = dt_util.now().replace(hour=8)
    after_10 = dt_util.now().replace(hour=14)

    with patch("openpeerpower.helpers.condition.dt_util.now", return_value=before_10):
       .opp.us.async_fire("test_event")
        await opp.async_block_till_done()

    assert len(calls) == 0

    with patch("openpeerpower.helpers.condition.dt_util.now", return_value=after_10):
       .opp.us.async_fire("test_event")
        await opp.async_block_till_done()

    assert len(calls) == 1


async def test_if_action_one_weekday.opp.calls):
    """Test for if action with one weekday."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "event", "event_type": "test_event"},
                "condition": {"condition": "time", "weekday": "mon"},
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    days_past_monday = dt_util.now().weekday()
    monday = dt_util.now() - timedelta(days=days_past_monday)
    tuesday = monday + timedelta(days=1)

    with patch("openpeerpower.helpers.condition.dt_util.now", return_value=monday):
       .opp.us.async_fire("test_event")
        await opp.async_block_till_done()

    assert len(calls) == 1

    with patch("openpeerpower.helpers.condition.dt_util.now", return_value=tuesday):
       .opp.us.async_fire("test_event")
        await opp.async_block_till_done()

    assert len(calls) == 1


async def test_if_action_list_weekday.opp.calls):
    """Test for action with a list of weekdays."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "event", "event_type": "test_event"},
                "condition": {"condition": "time", "weekday": ["mon", "tue"]},
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    days_past_monday = dt_util.now().weekday()
    monday = dt_util.now() - timedelta(days=days_past_monday)
    tuesday = monday + timedelta(days=1)
    wednesday = tuesday + timedelta(days=1)

    with patch("openpeerpower.helpers.condition.dt_util.now", return_value=monday):
       .opp.us.async_fire("test_event")
        await opp.async_block_till_done()

    assert len(calls) == 1

    with patch("openpeerpower.helpers.condition.dt_util.now", return_value=tuesday):
       .opp.us.async_fire("test_event")
        await opp.async_block_till_done()

    assert len(calls) == 2

    with patch("openpeerpower.helpers.condition.dt_util.now", return_value=wednesday):
       .opp.us.async_fire("test_event")
        await opp.async_block_till_done()

    assert len(calls) == 2


async def test_untrack_time_change.opp.
    """Test for removing tracked time changes."""
    mock_track_time_change = Mock()
    with patch(
        "openpeerpower.components.openpeerpower.triggers.time.async_track_time_change",
        return_value=mock_track_time_change,
    ):
        assert await async_setup_component(
           .opp,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "test",
                    "trigger": {
                        "platform": "time",
                        "at": ["5:00:00", "6:00:00", "7:00:00"],
                    },
                    "action": {"service": "test.automation", "data": {"test": "test"}},
                }
            },
        )
        await opp.async_block_till_done()

    await opp.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "automation.test"},
        blocking=True,
    )

    assert len(mock_track_time_change.mock_calls) == 3


async def test_if_fires_using_at_sensor.opp.calls):
    """Test for firing at sensor time."""
    now = dt_util.now()

    trigger_dt = now.replace(hour=5, minute=0, second=0, microsecond=0) + timedelta(2)

   .opp.tates.async_set(
        "sensor.next_alarm",
        trigger_dt.isoformat(),
        {ATTR_DEVICE_CLASS: sensor.DEVICE_CLASS_TIMESTAMP},
    )

    time_that_will_not_match_right_away = trigger_dt - timedelta(minutes=1)

    some_data = "{{ trigger.platform }}-{{ trigger.now.day }}-{{ trigger.now.hour }}-{{trigger.entity_id}}"
    with patch(
        "openpeerpower.util.dt.utcnow",
        return_value=dt_util.as_utc(time_that_will_not_match_right_away),
    ):
        assert await async_setup_component(
           .opp,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "time", "at": "sensor.next_alarm"},
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": some_data},
                    },
                }
            },
        )
        await opp.async_block_till_done()

    async_fire_time_changed.opp.trigger_dt + timedelta(seconds=1))
    await opp.async_block_till_done()

    assert len(calls) == 1
    assert (
        calls[0].data["some"]
        == f"time-{trigger_dt.day}-{trigger_dt.hour}-sensor.next_alarm"
    )

    trigger_dt += timedelta(days=1, hours=1)

   .opp.tates.async_set(
        "sensor.next_alarm",
        trigger_dt.isoformat(),
        {ATTR_DEVICE_CLASS: sensor.DEVICE_CLASS_TIMESTAMP},
    )
    await opp.async_block_till_done()

    async_fire_time_changed.opp.trigger_dt + timedelta(seconds=1))
    await opp.async_block_till_done()

    assert len(calls) == 2
    assert (
        calls[1].data["some"]
        == f"time-{trigger_dt.day}-{trigger_dt.hour}-sensor.next_alarm"
    )

    for broken in ("unknown", "unavailable", "invalid-ts"):
       .opp.tates.async_set(
            "sensor.next_alarm",
            trigger_dt.isoformat(),
            {ATTR_DEVICE_CLASS: sensor.DEVICE_CLASS_TIMESTAMP},
        )
        await opp.async_block_till_done()
       .opp.tates.async_set(
            "sensor.next_alarm",
            broken,
            {ATTR_DEVICE_CLASS: sensor.DEVICE_CLASS_TIMESTAMP},
        )
        await opp.async_block_till_done()

        async_fire_time_changed.opp.trigger_dt + timedelta(seconds=1))
        await opp.async_block_till_done()

        # We should not have listened to anything
        assert len(calls) == 2

    # Now without device class
   .opp.tates.async_set(
        "sensor.next_alarm",
        trigger_dt.isoformat(),
        {ATTR_DEVICE_CLASS: sensor.DEVICE_CLASS_TIMESTAMP},
    )
    await opp.async_block_till_done()
   .opp.tates.async_set(
        "sensor.next_alarm",
        trigger_dt.isoformat(),
    )
    await opp.async_block_till_done()

    async_fire_time_changed.opp.trigger_dt + timedelta(seconds=1))
    await opp.async_block_till_done()

    # We should not have listened to anything
    assert len(calls) == 2


@pytest.mark.parametrize(
    "conf",
    [
        {"platform": "time", "at": "input_datetime.bla"},
        {"platform": "time", "at": "sensor.bla"},
        {"platform": "time", "at": "12:34"},
    ],
)
def test_schema_valid(conf):
    """Make sure we don't accept number for 'at' value."""
    time.TRIGGER_SCHEMA(conf)


@pytest.mark.parametrize(
    "conf",
    [
        {"platform": "time", "at": "binary_sensor.bla"},
        {"platform": "time", "at": 745},
        {"platform": "time", "at": "25:00"},
    ],
)
def test_schema_invalid(conf):
    """Make sure we don't accept number for 'at' value."""
    with pytest.raises(vol.Invalid):
        time.TRIGGER_SCHEMA(conf)


async def test_datetime_in_past_on_load.opp.calls):
    """Test time trigger works if input_datetime is in past."""
    await async_setup_component(
       .opp,
        "input_datetime",
        {"input_datetime": {"my_trigger": {"has_date": True, "has_time": True}}},
    )

    now = dt_util.now()
    past = now - timedelta(days=2)
    future = now + timedelta(days=1)

    await opp.services.async_call(
        "input_datetime",
        "set_datetime",
        {
            ATTR_ENTITY_ID: "input_datetime.my_trigger",
            "datetime": str(past.replace(tzinfo=None)),
        },
        blocking=True,
    )

    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "time", "at": "input_datetime.my_trigger"},
                "action": {
                    "service": "test.automation",
                    "data_template": {
                        "some": "{{ trigger.platform }}-{{ trigger.now.day }}-{{ trigger.now.hour }}-{{trigger.entity_id}}"
                    },
                },
            }
        },
    )

    async_fire_time_changed.opp.now)
    await opp.async_block_till_done()

    assert len(calls) == 0

    await opp.services.async_call(
        "input_datetime",
        "set_datetime",
        {
            ATTR_ENTITY_ID: "input_datetime.my_trigger",
            "datetime": str(future.replace(tzinfo=None)),
        },
        blocking=True,
    )

    async_fire_time_changed.opp.future + timedelta(seconds=1))
    await opp.async_block_till_done()

    assert len(calls) == 1
    assert (
        calls[0].data["some"]
        == f"time-{future.day}-{future.hour}-input_datetime.my_trigger"
    )
