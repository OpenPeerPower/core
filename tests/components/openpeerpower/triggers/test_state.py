"""The test for state automation."""
from datetime import timedelta
from unittest.mock import patch

import pytest

import openpeerpower.components.automation as automation
from openpeerpower.components.openpeerpower.triggers import state as state_trigger
from openpeerpower.const import ATTR_ENTITY_ID, ENTITY_MATCH_ALL, SERVICE_TURN_OFF
from openpeerpower.core import Context
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util

from tests.common import (
    assert_setup_component,
    async_fire_time_changed,
    async_mock_service,
    mock_component,
)


@pytest.fixture
def calls(opp):
    """Track calls to a mock service."""
    return async_mock_service(opp, "test", "automation")


@pytest.fixture(autouse=True)
def setup_comp(opp):
    """Initialize components."""
    mock_component(opp, "group")
    opp.states.async_set("test.entity", "hello")


async def test_if_fires_on_entity_change(opp, calls):
    """Test for firing on entity change."""
    context = Context()
    opp.states.async_set("test.entity", "hello")
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "state", "entity_id": "test.entity"},
                "action": {
                    "service": "test.automation",
                    "data_template": {
                        "some": "{{ trigger.%s }}"
                        % "}} - {{ trigger.".join(
                            (
                                "platform",
                                "entity_id",
                                "from_state.state",
                                "to_state.state",
                                "for",
                            )
                        )
                    },
                },
            }
        },
    )
    await opp.async_block_till_done()

    opp.states.async_set("test.entity", "world", context=context)
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].context.parent_id == context.id
    assert calls[0].data["some"] == "state - test.entity - hello - world - None"

    await opp.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )
    opp.states.async_set("test.entity", "planet")
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_entity_change_with_from_filter(opp, calls):
    """Test for firing on entity change with filter."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": "test.entity",
                    "from": "hello",
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_entity_change_with_to_filter(opp, calls):
    """Test for firing on entity change with no filter."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": "test.entity",
                    "to": "world",
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_attribute_change_with_to_filter(opp, calls):
    """Test for not firing on attribute change."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": "test.entity",
                    "to": "world",
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    opp.states.async_set("test.entity", "world", {"test_attribute": 11})
    opp.states.async_set("test.entity", "world", {"test_attribute": 12})
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_entity_change_with_both_filters(opp, calls):
    """Test for firing if both filters are a non match."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": "test.entity",
                    "from": "hello",
                    "to": "world",
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_not_fires_if_to_filter_not_match(opp, calls):
    """Test for not firing if to filter is not a match."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": "test.entity",
                    "from": "hello",
                    "to": "world",
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    opp.states.async_set("test.entity", "moon")
    await opp.async_block_till_done()
    assert len(calls) == 0


async def test_if_not_fires_if_from_filter_not_match(opp, calls):
    """Test for not firing if from filter is not a match."""
    opp.states.async_set("test.entity", "bye")

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": "test.entity",
                    "from": "hello",
                    "to": "world",
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 0


async def test_if_not_fires_if_entity_not_match(opp, calls):
    """Test for not firing if entity is not matching."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "state", "entity_id": "test.another_entity"},
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 0


async def test_if_action(opp, calls):
    """Test for to action."""
    entity_id = "domain.test_entity"
    test_state = "new_state"
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "event", "event_type": "test_event"},
                "condition": [
                    {"condition": "state", "entity_id": entity_id, "state": test_state}
                ],
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    opp.states.async_set(entity_id, test_state)
    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()

    assert len(calls) == 1

    opp.states.async_set(entity_id, test_state + "something")
    opp.bus.async_fire("test_event")
    await opp.async_block_till_done()

    assert len(calls) == 1


async def test_if_fails_setup_if_to_boolean_value(opp, calls):
    """Test for setup failure for boolean to."""
    with assert_setup_component(0, automation.DOMAIN):
        assert await async_setup_component(
            opp,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "to": True,
                    },
                    "action": {"service": "openpeerpower.turn_on"},
                }
            },
        )


async def test_if_fails_setup_if_from_boolean_value(opp, calls):
    """Test for setup failure for boolean from."""
    with assert_setup_component(0, automation.DOMAIN):
        assert await async_setup_component(
            opp,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "from": True,
                    },
                    "action": {"service": "openpeerpower.turn_on"},
                }
            },
        )


async def test_if_fails_setup_bad_for(opp, calls):
    """Test for setup failure for bad for."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": "test.entity",
                    "to": "world",
                    "for": {"invalid": 5},
                },
                "action": {"service": "openpeerpower.turn_on"},
            }
        },
    )

    with patch.object(state_trigger, "_LOGGER") as mock_logger:
        opp.states.async_set("test.entity", "world")
        await opp.async_block_till_done()
        assert mock_logger.error.called


async def test_if_not_fires_on_entity_change_with_for(opp, calls):
    """Test for not firing on entity change with for."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": "test.entity",
                    "to": "world",
                    "for": {"seconds": 5},
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    opp.states.async_set("test.entity", "not_world")
    await opp.async_block_till_done()
    async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 0


async def test_if_not_fires_on_entities_change_with_for_after_stop(opp, calls):
    """Test for not firing on entity change with for after stop trigger."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": ["test.entity_1", "test.entity_2"],
                    "to": "world",
                    "for": {"seconds": 5},
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    opp.states.async_set("test.entity_1", "world")
    opp.states.async_set("test.entity_2", "world")
    await opp.async_block_till_done()
    async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 1

    opp.states.async_set("test.entity_1", "world_no")
    opp.states.async_set("test.entity_2", "world_no")
    await opp.async_block_till_done()
    opp.states.async_set("test.entity_1", "world")
    opp.states.async_set("test.entity_2", "world")
    await opp.async_block_till_done()
    await opp.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )

    async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_entity_change_with_for_attribute_change(opp, calls):
    """Test for firing on entity change with for and attribute change."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": "test.entity",
                    "to": "world",
                    "for": {"seconds": 5},
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    utcnow = dt_util.utcnow()
    with patch("openpeerpower.core.dt_util.utcnow") as mock_utcnow:
        mock_utcnow.return_value = utcnow
        opp.states.async_set("test.entity", "world")
        await opp.async_block_till_done()
        mock_utcnow.return_value += timedelta(seconds=4)
        async_fire_time_changed(opp, mock_utcnow.return_value)
        opp.states.async_set(
            "test.entity", "world", attributes={"mock_attr": "attr_change"}
        )
        await opp.async_block_till_done()
        assert len(calls) == 0
        mock_utcnow.return_value += timedelta(seconds=4)
        async_fire_time_changed(opp, mock_utcnow.return_value)
        await opp.async_block_till_done()
        assert len(calls) == 1


async def test_if_fires_on_entity_change_with_for_multiple_force_update(opp, calls):
    """Test for firing on entity change with for and force update."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": "test.force_entity",
                    "to": "world",
                    "for": {"seconds": 5},
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    utcnow = dt_util.utcnow()
    with patch("openpeerpower.core.dt_util.utcnow") as mock_utcnow:
        mock_utcnow.return_value = utcnow
        opp.states.async_set("test.force_entity", "world", None, True)
        await opp.async_block_till_done()
        for _ in range(4):
            mock_utcnow.return_value += timedelta(seconds=1)
            async_fire_time_changed(opp, mock_utcnow.return_value)
            opp.states.async_set("test.force_entity", "world", None, True)
            await opp.async_block_till_done()
        assert len(calls) == 0
        mock_utcnow.return_value += timedelta(seconds=4)
        async_fire_time_changed(opp, mock_utcnow.return_value)
        await opp.async_block_till_done()
        assert len(calls) == 1


async def test_if_fires_on_entity_change_with_for(opp, calls):
    """Test for firing on entity change with for."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": "test.entity",
                    "to": "world",
                    "for": {"seconds": 5},
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert 1 == len(calls)


async def test_if_fires_on_entity_change_with_for_without_to(opp, calls):
    """Test for firing on entity change with for."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": "test.entity",
                    "for": {"seconds": 5},
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    opp.states.async_set("test.entity", "hello")
    await opp.async_block_till_done()

    async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=2))
    await opp.async_block_till_done()
    assert len(calls) == 0

    opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()

    async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=4))
    await opp.async_block_till_done()
    assert len(calls) == 0

    async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_does_not_fires_on_entity_change_with_for_without_to_2(opp, calls):
    """Test for firing on entity change with for."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": "test.entity",
                    "for": {"seconds": 5},
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    utcnow = dt_util.utcnow()
    with patch("openpeerpower.core.dt_util.utcnow") as mock_utcnow:
        mock_utcnow.return_value = utcnow

        for i in range(10):
            opp.states.async_set("test.entity", str(i))
            await opp.async_block_till_done()

            mock_utcnow.return_value += timedelta(seconds=1)
            async_fire_time_changed(opp, mock_utcnow.return_value)
            await opp.async_block_till_done()

    assert len(calls) == 0


async def test_if_fires_on_entity_creation_and_removal(opp, calls):
    """Test for firing on entity creation and removal, with to/from constraints."""
    # set automations for multiple combinations to/from
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"platform": "state", "entity_id": "test.entity_0"},
                    "action": {"service": "test.automation"},
                },
                {
                    "trigger": {
                        "platform": "state",
                        "from": "hello",
                        "entity_id": "test.entity_1",
                    },
                    "action": {"service": "test.automation"},
                },
                {
                    "trigger": {
                        "platform": "state",
                        "to": "world",
                        "entity_id": "test.entity_2",
                    },
                    "action": {"service": "test.automation"},
                },
            ],
        },
    )
    await opp.async_block_till_done()

    # use contexts to identify trigger entities
    context_0 = Context()
    context_1 = Context()
    context_2 = Context()

    # automation with match_all triggers on creation
    opp.states.async_set("test.entity_0", "any", context=context_0)
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].context.parent_id == context_0.id

    # create entities, trigger on test.entity_2 ('to' matches, no 'from')
    opp.states.async_set("test.entity_1", "hello", context=context_1)
    opp.states.async_set("test.entity_2", "world", context=context_2)
    await opp.async_block_till_done()
    assert len(calls) == 2
    assert calls[1].context.parent_id == context_2.id

    # removal of both, trigger on test.entity_1 ('from' matches, no 'to')
    assert opp.states.async_remove("test.entity_1", context=context_1)
    assert opp.states.async_remove("test.entity_2", context=context_2)
    await opp.async_block_till_done()
    assert len(calls) == 3
    assert calls[2].context.parent_id == context_1.id

    # automation with match_all triggers on removal
    assert opp.states.async_remove("test.entity_0", context=context_0)
    await opp.async_block_till_done()
    assert len(calls) == 4
    assert calls[3].context.parent_id == context_0.id


async def test_if_fires_on_for_condition(opp, calls):
    """Test for firing if condition is on."""
    point1 = dt_util.utcnow()
    point2 = point1 + timedelta(seconds=10)
    with patch("openpeerpower.core.dt_util.utcnow") as mock_utcnow:
        mock_utcnow.return_value = point1
        opp.states.async_set("test.entity", "on")
        assert await async_setup_component(
            opp,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "condition": {
                        "condition": "state",
                        "entity_id": "test.entity",
                        "state": "on",
                        "for": {"seconds": 5},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
        await opp.async_block_till_done()

        # not enough time has passed
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 0

        # Time travel 10 secs into the future
        mock_utcnow.return_value = point2
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 1


async def test_if_fires_on_for_condition_attribute_change(opp, calls):
    """Test for firing if condition is on with attribute change."""
    point1 = dt_util.utcnow()
    point2 = point1 + timedelta(seconds=4)
    point3 = point1 + timedelta(seconds=8)
    with patch("openpeerpower.core.dt_util.utcnow") as mock_utcnow:
        mock_utcnow.return_value = point1
        opp.states.async_set("test.entity", "on")
        assert await async_setup_component(
            opp,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "condition": {
                        "condition": "state",
                        "entity_id": "test.entity",
                        "state": "on",
                        "for": {"seconds": 5},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
        await opp.async_block_till_done()

        # not enough time has passed
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 0

        # Still not enough time has passed, but an attribute is changed
        mock_utcnow.return_value = point2
        opp.states.async_set(
            "test.entity", "on", attributes={"mock_attr": "attr_change"}
        )
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 0

        # Enough time has now passed
        mock_utcnow.return_value = point3
        opp.bus.async_fire("test_event")
        await opp.async_block_till_done()
        assert len(calls) == 1


async def test_if_fails_setup_for_without_time(opp, calls):
    """Test for setup failure if no time is provided."""
    with assert_setup_component(0, automation.DOMAIN):
        assert await async_setup_component(
            opp,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "event", "event_type": "bla"},
                    "condition": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "state": "on",
                        "for": {},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )


async def test_if_fails_setup_for_without_entity(opp, calls):
    """Test for setup failure if no entity is provided."""
    with assert_setup_component(0, automation.DOMAIN):
        assert await async_setup_component(
            opp,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"event_type": "bla"},
                    "condition": {
                        "platform": "state",
                        "state": "on",
                        "for": {"seconds": 5},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )


async def test_wait_template_with_trigger(opp, calls):
    """Test using wait template with 'trigger.entity_id'."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": "test.entity",
                    "to": "world",
                },
                "action": [
                    {"wait_template": "{{ is_state(trigger.entity_id, 'hello') }}"},
                    {
                        "service": "test.automation",
                        "data_template": {
                            "some": "{{ trigger.%s }}"
                            % "}} - {{ trigger.".join(
                                (
                                    "platform",
                                    "entity_id",
                                    "from_state.state",
                                    "to_state.state",
                                )
                            )
                        },
                    },
                ],
            }
        },
    )

    await opp.async_block_till_done()

    opp.states.async_set("test.entity", "world")
    opp.states.async_set("test.entity", "hello")
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["some"] == "state - test.entity - hello - world"


async def test_if_fires_on_entities_change_no_overlap(opp, calls):
    """Test for firing on entities change with no overlap."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": ["test.entity_1", "test.entity_2"],
                    "to": "world",
                    "for": {"seconds": 5},
                },
                "action": {
                    "service": "test.automation",
                    "data_template": {"some": "{{ trigger.entity_id }}"},
                },
            }
        },
    )
    await opp.async_block_till_done()

    utcnow = dt_util.utcnow()
    with patch("openpeerpower.core.dt_util.utcnow") as mock_utcnow:
        mock_utcnow.return_value = utcnow
        opp.states.async_set("test.entity_1", "world")
        await opp.async_block_till_done()
        mock_utcnow.return_value += timedelta(seconds=10)
        async_fire_time_changed(opp, mock_utcnow.return_value)
        await opp.async_block_till_done()
        assert len(calls) == 1
        assert calls[0].data["some"] == "test.entity_1"

        opp.states.async_set("test.entity_2", "world")
        await opp.async_block_till_done()
        mock_utcnow.return_value += timedelta(seconds=10)
        async_fire_time_changed(opp, mock_utcnow.return_value)
        await opp.async_block_till_done()
        assert len(calls) == 2
        assert calls[1].data["some"] == "test.entity_2"


async def test_if_fires_on_entities_change_overlap(opp, calls):
    """Test for firing on entities change with overlap."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": ["test.entity_1", "test.entity_2"],
                    "to": "world",
                    "for": {"seconds": 5},
                },
                "action": {
                    "service": "test.automation",
                    "data_template": {"some": "{{ trigger.entity_id }}"},
                },
            }
        },
    )
    await opp.async_block_till_done()

    utcnow = dt_util.utcnow()
    with patch("openpeerpower.core.dt_util.utcnow") as mock_utcnow:
        mock_utcnow.return_value = utcnow
        opp.states.async_set("test.entity_1", "world")
        await opp.async_block_till_done()
        mock_utcnow.return_value += timedelta(seconds=1)
        async_fire_time_changed(opp, mock_utcnow.return_value)
        opp.states.async_set("test.entity_2", "world")
        await opp.async_block_till_done()
        mock_utcnow.return_value += timedelta(seconds=1)
        async_fire_time_changed(opp, mock_utcnow.return_value)
        opp.states.async_set("test.entity_2", "hello")
        await opp.async_block_till_done()
        mock_utcnow.return_value += timedelta(seconds=1)
        async_fire_time_changed(opp, mock_utcnow.return_value)
        opp.states.async_set("test.entity_2", "world")
        await opp.async_block_till_done()
        assert len(calls) == 0
        mock_utcnow.return_value += timedelta(seconds=3)
        async_fire_time_changed(opp, mock_utcnow.return_value)
        await opp.async_block_till_done()
        assert len(calls) == 1
        assert calls[0].data["some"] == "test.entity_1"

        mock_utcnow.return_value += timedelta(seconds=3)
        async_fire_time_changed(opp, mock_utcnow.return_value)
        await opp.async_block_till_done()
        assert len(calls) == 2
        assert calls[1].data["some"] == "test.entity_2"


async def test_if_fires_on_change_with_for_template_1(opp, calls):
    """Test for firing on change with for template."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": "test.entity",
                    "to": "world",
                    "for": {"seconds": "{{ 5 }}"},
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 0
    async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_change_with_for_template_2(opp, calls):
    """Test for firing on change with for template."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": "test.entity",
                    "to": "world",
                    "for": "{{ 5 }}",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 0
    async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_change_with_for_template_3(opp, calls):
    """Test for firing on change with for template."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": "test.entity",
                    "to": "world",
                    "for": "00:00:{{ 5 }}",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 0
    async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_change_with_for_template_4(opp, calls):
    """Test for firing on change with for template."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger_variables": {"seconds": 5},
                "trigger": {
                    "platform": "state",
                    "entity_id": "test.entity",
                    "to": "world",
                    "for": {"seconds": "{{ seconds }}"},
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 0
    async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_change_from_with_for(opp, calls):
    """Test for firing on change with from/for."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": "media_player.foo",
                    "from": "playing",
                    "for": "00:00:30",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.states.async_set("media_player.foo", "playing")
    await opp.async_block_till_done()
    opp.states.async_set("media_player.foo", "paused")
    await opp.async_block_till_done()
    opp.states.async_set("media_player.foo", "stopped")
    await opp.async_block_till_done()
    async_fire_time_changed(opp, dt_util.utcnow() + timedelta(minutes=1))
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_not_fires_on_change_from_with_for(opp, calls):
    """Test for firing on change with from/for."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": "media_player.foo",
                    "from": "playing",
                    "for": "00:00:30",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.states.async_set("media_player.foo", "playing")
    await opp.async_block_till_done()
    opp.states.async_set("media_player.foo", "paused")
    await opp.async_block_till_done()
    opp.states.async_set("media_player.foo", "playing")
    await opp.async_block_till_done()
    async_fire_time_changed(opp, dt_util.utcnow() + timedelta(minutes=1))
    await opp.async_block_till_done()
    assert len(calls) == 0


async def test_invalid_for_template_1(opp, calls):
    """Test for invalid for template."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": "test.entity",
                    "to": "world",
                    "for": {"seconds": "{{ five }}"},
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    with patch.object(state_trigger, "_LOGGER") as mock_logger:
        opp.states.async_set("test.entity", "world")
        await opp.async_block_till_done()
        assert mock_logger.error.called


async def test_if_fires_on_entities_change_overlap_for_template(opp, calls):
    """Test for firing on entities change with overlap and for template."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": ["test.entity_1", "test.entity_2"],
                    "to": "world",
                    "for": '{{ 5 if trigger.entity_id == "test.entity_1"'
                    "   else 10 }}",
                },
                "action": {
                    "service": "test.automation",
                    "data_template": {
                        "some": "{{ trigger.entity_id }} - {{ trigger.for }}"
                    },
                },
            }
        },
    )
    await opp.async_block_till_done()

    utcnow = dt_util.utcnow()
    with patch("openpeerpower.core.dt_util.utcnow") as mock_utcnow:
        mock_utcnow.return_value = utcnow
        opp.states.async_set("test.entity_1", "world")
        await opp.async_block_till_done()
        mock_utcnow.return_value += timedelta(seconds=1)
        async_fire_time_changed(opp, mock_utcnow.return_value)
        opp.states.async_set("test.entity_2", "world")
        await opp.async_block_till_done()
        mock_utcnow.return_value += timedelta(seconds=1)
        async_fire_time_changed(opp, mock_utcnow.return_value)
        opp.states.async_set("test.entity_2", "hello")
        await opp.async_block_till_done()
        mock_utcnow.return_value += timedelta(seconds=1)
        async_fire_time_changed(opp, mock_utcnow.return_value)
        opp.states.async_set("test.entity_2", "world")
        await opp.async_block_till_done()
        assert len(calls) == 0
        mock_utcnow.return_value += timedelta(seconds=3)
        async_fire_time_changed(opp, mock_utcnow.return_value)
        await opp.async_block_till_done()
        assert len(calls) == 1
        assert calls[0].data["some"] == "test.entity_1 - 0:00:05"

        mock_utcnow.return_value += timedelta(seconds=3)
        async_fire_time_changed(opp, mock_utcnow.return_value)
        await opp.async_block_till_done()
        assert len(calls) == 1
        mock_utcnow.return_value += timedelta(seconds=5)
        async_fire_time_changed(opp, mock_utcnow.return_value)
        await opp.async_block_till_done()
        assert len(calls) == 2
        assert calls[1].data["some"] == "test.entity_2 - 0:00:10"


async def test_attribute_if_fires_on_entity_change_with_both_filters(opp, calls):
    """Test for firing if both filters are match attribute."""
    opp.states.async_set("test.entity", "bla", {"name": "hello"})

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": "test.entity",
                    "from": "hello",
                    "to": "world",
                    "attribute": "name",
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    opp.states.async_set("test.entity", "bla", {"name": "world"})
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_attribute_if_fires_on_entity_where_attr_stays_constant(opp, calls):
    """Test for firing if attribute stays the same."""
    opp.states.async_set("test.entity", "bla", {"name": "hello", "other": "old_value"})

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": "test.entity",
                    "attribute": "name",
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    # Leave all attributes the same
    opp.states.async_set("test.entity", "bla", {"name": "hello", "other": "old_value"})
    await opp.async_block_till_done()
    assert len(calls) == 0

    # Change the untracked attribute
    opp.states.async_set("test.entity", "bla", {"name": "hello", "other": "new_value"})
    await opp.async_block_till_done()
    assert len(calls) == 0

    # Change the tracked attribute
    opp.states.async_set("test.entity", "bla", {"name": "world", "other": "old_value"})
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_attribute_if_not_fires_on_entities_change_with_for_after_stop(
    opp, calls
):
    """Test for not firing on entity change with for after stop trigger."""
    opp.states.async_set("test.entity", "bla", {"name": "hello"})

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": "test.entity",
                    "from": "hello",
                    "to": "world",
                    "attribute": "name",
                    "for": 5,
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    # Test that the for-check works
    opp.states.async_set("test.entity", "bla", {"name": "world"})
    await opp.async_block_till_done()
    assert len(calls) == 0

    async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=2))
    opp.states.async_set("test.entity", "bla", {"name": "world", "something": "else"})
    await opp.async_block_till_done()
    assert len(calls) == 0

    async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 1

    # Now remove state while inside "for"
    opp.states.async_set("test.entity", "bla", {"name": "hello"})
    opp.states.async_set("test.entity", "bla", {"name": "world"})
    await opp.async_block_till_done()
    assert len(calls) == 1

    opp.states.async_remove("test.entity")
    await opp.async_block_till_done()

    async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_attribute_if_fires_on_entity_change_with_both_filters_boolean(
    opp, calls
):
    """Test for firing if both filters are match attribute."""
    opp.states.async_set("test.entity", "bla", {"happening": False})

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "state",
                    "entity_id": "test.entity",
                    "from": False,
                    "to": True,
                    "attribute": "happening",
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    opp.states.async_set("test.entity", "bla", {"happening": True})
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_variables_priority(opp, calls):
    """Test an externally defined trigger variable is overridden."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger_variables": {"trigger": "illegal"},
                "trigger": {
                    "platform": "state",
                    "entity_id": ["test.entity_1", "test.entity_2"],
                    "to": "world",
                    "for": '{{ 5 if trigger.entity_id == "test.entity_1"'
                    "   else 10 }}",
                },
                "action": {
                    "service": "test.automation",
                    "data_template": {
                        "some": "{{ trigger.entity_id }} - {{ trigger.for }}"
                    },
                },
            }
        },
    )
    await opp.async_block_till_done()

    utcnow = dt_util.utcnow()
    with patch("openpeerpower.core.dt_util.utcnow") as mock_utcnow:
        mock_utcnow.return_value = utcnow
        opp.states.async_set("test.entity_1", "world")
        await opp.async_block_till_done()
        mock_utcnow.return_value += timedelta(seconds=1)
        async_fire_time_changed(opp, mock_utcnow.return_value)
        opp.states.async_set("test.entity_2", "world")
        await opp.async_block_till_done()
        mock_utcnow.return_value += timedelta(seconds=1)
        async_fire_time_changed(opp, mock_utcnow.return_value)
        opp.states.async_set("test.entity_2", "hello")
        await opp.async_block_till_done()
        mock_utcnow.return_value += timedelta(seconds=1)
        async_fire_time_changed(opp, mock_utcnow.return_value)
        opp.states.async_set("test.entity_2", "world")
        await opp.async_block_till_done()
        assert len(calls) == 0
        mock_utcnow.return_value += timedelta(seconds=3)
        async_fire_time_changed(opp, mock_utcnow.return_value)
        await opp.async_block_till_done()
        assert len(calls) == 1
        assert calls[0].data["some"] == "test.entity_1 - 0:00:05"

        mock_utcnow.return_value += timedelta(seconds=3)
        async_fire_time_changed(opp, mock_utcnow.return_value)
        await opp.async_block_till_done()
        assert len(calls) == 1
        mock_utcnow.return_value += timedelta(seconds=5)
        async_fire_time_changed(opp, mock_utcnow.return_value)
        await opp.async_block_till_done()
        assert len(calls) == 2
        assert calls[1].data["some"] == "test.entity_2 - 0:00:10"
