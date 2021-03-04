"""The tests for the Event automation."""
import pytest

import openpeerpower.components.automation as automation
from openpeerpower.const import ATTR_ENTITY_ID, ENTITY_MATCH_ALL, SERVICE_TURN_OFF
from openpeerpower.core import Context
from openpeerpower.setup import async_setup_component

from tests.common import async_mock_service, mock_component


@pytest.fixture
def calls(opp):
    """Track calls to a mock service."""
    return async_mock_service(opp, "test", "automation")


@pytest.fixture
def context_with_user():
    """Create a context with default user_id."""
    return Context(user_id="test_user_id")


@pytest.fixture(autouse=True)
def setup_comp(opp):
    """Initialize components."""
    mock_component(opp, "group")


async def test_if_fires_on_event(opp, calls):
    """Test the firing of events."""
    context = Context()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.bus.async_fire("test_event", context=context)
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].context.parent_id == context.id

    await opp.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )

    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_templated_event(opp, calls):
    """Test the firing of events."""
    context = Context()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger_variables": {"event_type": "test_event"},
                "trigger": {"platform": "event", "event_type": "{{event_type}}"},
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.bus.async_fire("test_event", context=context)
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].context.parent_id == context.id

    await opp.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )

    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_multiple_events(opp, calls):
    """Test the firing of events."""
    context = Context()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "event",
                    "event_type": ["test_event", "test2_event"],
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.bus.async_fire("test_event", context=context)
    await opp.async_block_till_done()
    opp.bus.async_fire("test2_event", context=context)
    await opp.async_block_till_done()
    assert len(calls) == 2
    assert calls[0].context.parent_id == context.id
    assert calls[1].context.parent_id == context.id


async def test_if_fires_on_event_extra_data(opp, calls, context_with_user):
    """Test the firing of events still matches with event data and context."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {"service": "test.automation"},
            }
        },
    )
    opp.bus.async_fire(
        "test_event", {"extra_key": "extra_data"}, context=context_with_user
    )
    await opp.async_block_till_done()
    assert len(calls) == 1

    await opp.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )

    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_event_with_data_and_context(opp, calls, context_with_user):
    """Test the firing of events with data and context."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "event",
                    "event_type": "test_event",
                    "event_data": {
                        "some_attr": "some_value",
                        "second_attr": "second_value",
                    },
                    "context": {"user_id": context_with_user.user_id},
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.bus.async_fire(
        "test_event",
        {"some_attr": "some_value", "another": "value", "second_attr": "second_value"},
        context=context_with_user,
    )
    await opp.async_block_till_done()
    assert len(calls) == 1

    opp.bus.async_fire(
        "test_event",
        {"some_attr": "some_value", "another": "value"},
        context=context_with_user,
    )
    await opp.async_block_till_done()
    assert len(calls) == 1  # No new call

    opp.bus.async_fire(
        "test_event",
        {"some_attr": "some_value", "another": "value", "second_attr": "second_value"},
    )
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_event_with_templated_data_and_context(
    opp, calls, context_with_user
):
    """Test the firing of events with templated data and context."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger_variables": {
                    "attr_1_val": "milk",
                    "attr_2_val": "beer",
                    "user_id": context_with_user.user_id,
                },
                "trigger": {
                    "platform": "event",
                    "event_type": "test_event",
                    "event_data": {
                        "attr_1": "{{attr_1_val}}",
                        "attr_2": "{{attr_2_val}}",
                    },
                    "context": {"user_id": "{{user_id}}"},
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.bus.async_fire(
        "test_event",
        {"attr_1": "milk", "another": "value", "attr_2": "beer"},
        context=context_with_user,
    )
    await opp.async_block_till_done()
    assert len(calls) == 1

    opp.bus.async_fire(
        "test_event",
        {"attr_1": "milk", "another": "value"},
        context=context_with_user,
    )
    await opp.async_block_till_done()
    assert len(calls) == 1  # No new call

    opp.bus.async_fire(
        "test_event",
        {"attr_1": "milk", "another": "value", "attr_2": "beer"},
    )
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_event_with_empty_data_and_context_config(
    opp, calls, context_with_user
):
    """Test the firing of events with empty data and context config.

    The frontend automation editor can produce configurations with an
    empty dict for event_data instead of no key.
    """
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "event",
                    "event_type": "test_event",
                    "event_data": {},
                    "context": {},
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.bus.async_fire(
        "test_event",
        {"some_attr": "some_value", "another": "value"},
        context=context_with_user,
    )
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_event_with_nested_data(opp, calls):
    """Test the firing of events with nested data."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "event",
                    "event_type": "test_event",
                    "event_data": {"parent_attr": {"some_attr": "some_value"}},
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.bus.async_fire(
        "test_event", {"parent_attr": {"some_attr": "some_value", "another": "value"}}
    )
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_not_fires_if_event_data_not_matches(opp, calls):
    """Test firing of event if no data match."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "event",
                    "event_type": "test_event",
                    "event_data": {"some_attr": "some_value"},
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.bus.async_fire("test_event", {"some_attr": "some_other_value"})
    await opp.async_block_till_done()
    assert len(calls) == 0


async def test_if_not_fires_if_event_context_not_matches(
    opp, calls, context_with_user
):
    """Test firing of event if no context match."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "event",
                    "event_type": "test_event",
                    "context": {"user_id": "some_user"},
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.bus.async_fire("test_event", {}, context=context_with_user)
    await opp.async_block_till_done()
    assert len(calls) == 0


async def test_if_fires_on_multiple_user_ids(opp, calls, context_with_user):
    """Test the firing of event when the trigger has multiple user ids."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "event",
                    "event_type": "test_event",
                    "event_data": {},
                    "context": {"user_id": [context_with_user.user_id, "another id"]},
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.bus.async_fire("test_event", {}, context=context_with_user)
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_event_data_with_list(opp, calls):
    """Test the (non)firing of event when the data schema has lists."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "event",
                    "event_type": "test_event",
                    "event_data": {"some_attr": [1, 2]},
                    "context": {},
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.bus.async_fire("test_event", {"some_attr": [1, 2]})
    await opp.async_block_till_done()
    assert len(calls) == 1

    # don't match a single value
    opp.bus.async_fire("test_event", {"some_attr": 1})
    await opp.async_block_till_done()
    assert len(calls) == 1

    # don't match a containing list
    opp.bus.async_fire("test_event", {"some_attr": [1, 2, 3]})
    await opp.async_block_till_done()
    assert len(calls) == 1
