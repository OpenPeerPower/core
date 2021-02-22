"""The tests for the Template automation."""
from datetime import timedelta
from unittest import mock
from unittest.mock import patch

import pytest

import openpeerpower.components.automation as automation
from openpeerpower.components.template import trigger as template_trigger
from openpeerpower.const import ATTR_ENTITY_ID, ENTITY_MATCH_ALL, SERVICE_TURN_OFF
from openpeerpower.core import Context, callback
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util

from tests.common import (
    assert_setup_component,
    async_fire_time_changed,
    async_mock_service,
    mock_component,
)
from tests.components.blueprint.conftest import stub_blueprint_populate  # noqa


@pytest.fixture
def calls.opp):
    """Track calls to a mock service."""
    return async_mock_service.opp, "test", "automation")


@pytest.fixture(autouse=True)
def setup_comp.opp):
    """Initialize components."""
    mock_component.opp, "group")
   .opp.states.async_set("test.entity", "hello")


async def test_if_fires_on_change_bool.opp, calls):
    """Test for firing on boolean change."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": '{{ states.test.entity.state == "world" and true }}',
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    assert len(calls) == 0

   .opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 1

    await opp.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )

   .opp.states.async_set("test.entity", "planet")
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_change_str.opp, calls):
    """Test for firing on change."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": '{{ states.test.entity.state == "world" and "true" }}',
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    assert len(calls) == 0

   .opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_change_str_crazy.opp, calls):
    """Test for firing on change."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": '{{ states.test.entity.state == "world" and "TrUE" }}',
                },
                "action": {"service": "test.automation"},
            }
        },
    )

   .opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_not_fires_when_true_at_setup_opp, calls):
    """Test for not firing during startup."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": '{{ states.test.entity.state == "hello" }}',
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    assert len(calls) == 0

   .opp.states.async_set("test.entity", "hello", force_update=True)
    await opp.async_block_till_done()
    assert len(calls) == 0


async def test_if_not_fires_because_fail.opp, calls):
    """Test for not firing after TemplateError."""
   .opp.states.async_set("test.number", "1")

    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": "{{ 84 / states.test.number.state|int == 42 }}",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    assert len(calls) == 0

   .opp.states.async_set("test.number", "2")
    await opp.async_block_till_done()
    assert len(calls) == 1

   .opp.states.async_set("test.number", "0")
    await opp.async_block_till_done()
    assert len(calls) == 1

   .opp.states.async_set("test.number", "2")
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_not_fires_on_change_bool.opp, calls):
    """Test for not firing on boolean change."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": '{{ states.test.entity.state == "world" and false }}',
                },
                "action": {"service": "test.automation"},
            }
        },
    )

   .opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 0


async def test_if_not_fires_on_change_str.opp, calls):
    """Test for not firing on string change."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "template", "value_template": "true"},
                "action": {"service": "test.automation"},
            }
        },
    )

   .opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 0


async def test_if_not_fires_on_change_str_crazy.opp, calls):
    """Test for not firing on string change."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": '{{ "Anything other than true is false." }}',
                },
                "action": {"service": "test.automation"},
            }
        },
    )

   .opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 0


async def test_if_fires_on_no_change.opp, calls):
    """Test for firing on no change."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "template", "value_template": "{{ true }}"},
                "action": {"service": "test.automation"},
            }
        },
    )

    await opp.async_block_till_done()
    cur_len = len(calls)

   .opp.states.async_set("test.entity", "hello")
    await opp.async_block_till_done()
    assert cur_len == len(calls)


async def test_if_fires_on_two_change.opp, calls):
    """Test for firing on two changes."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": "{{ states.test.entity.state == 'world' }}",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    # Trigger once
   .opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 1

    # Trigger again
   .opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_change_with_template.opp, calls):
    """Test for firing on change with template."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": '{{ is_state("test.entity", "world") }}',
                },
                "action": {"service": "test.automation"},
            }
        },
    )

   .opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_not_fires_on_change_with_template.opp, calls):
    """Test for not firing on change with template."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": '{{ is_state("test.entity", "hello") }}',
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    await opp.async_block_till_done()

   .opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 0


async def test_if_fires_on_change_with_template_advanced.opp, calls):
    """Test for firing on change with template advanced."""
    context = Context()
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": '{{ is_state("test.entity", "world") }}',
                },
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

   .opp.states.async_set("test.entity", "world", context=context)
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].context.parent_id == context.id
    assert "template - test.entity - hello - world - None" == calls[0].data["some"]


async def test_if_fires_on_no_change_with_template_advanced.opp, calls):
    """Test for firing on no change with template advanced."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": """{%- if is_state("test.entity", "world") -%}
                                        true
                                        {%- else -%}
                                        false
                                        {%- endif -%}""",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    # Different state
   .opp.states.async_set("test.entity", "worldz")
    await opp.async_block_till_done()
    assert len(calls) == 0

    # Different state
   .opp.states.async_set("test.entity", "hello")
    await opp.async_block_till_done()
    assert len(calls) == 0


async def test_if_fires_on_change_with_template_2.opp, calls):
    """Test for firing on change with template."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": '{{ not is_state("test.entity", "world") }}',
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    await opp.async_block_till_done()

   .opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 0

   .opp.states.async_set("test.entity", "home")
    await opp.async_block_till_done()
    assert len(calls) == 1

   .opp.states.async_set("test.entity", "work")
    await opp.async_block_till_done()
    assert len(calls) == 1

   .opp.states.async_set("test.entity", "not_home")
    await opp.async_block_till_done()
    assert len(calls) == 1

   .opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 1

   .opp.states.async_set("test.entity", "home")
    await opp.async_block_till_done()
    assert len(calls) == 2


async def test_if_action.opp, calls):
    """Test for firing if action."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "event", "event_type": "test_event"},
                "condition": [
                    {
                        "condition": "template",
                        "value_template": '{{ is_state("test.entity", "world") }}',
                    }
                ],
                "action": {"service": "test.automation"},
            }
        },
    )

    # Condition is not true yet
   .opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 0

    # Change condition to true, but it shouldn't be triggered yet
   .opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 0

    # Condition is true and event is triggered
   .opp.bus.async_fire("test_event")
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_change_with_bad_template.opp, calls):
    """Test for firing on change with bad template."""
    with assert_setup_component(0, automation.DOMAIN):
        assert await async_setup_component(
           .opp,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "template", "value_template": "{{ "},
                    "action": {"service": "test.automation"},
                }
            },
        )


async def test_if_fires_on_change_with_bad_template_2.opp, calls):
    """Test for firing on change with bad template."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": "{{ xyz | round(0) }}",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

   .opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 0


async def test_wait_template_with_trigger.opp, calls):
    """Test using wait template with 'trigger.entity_id'."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": "{{ states.test.entity.state == 'world' }}",
                },
                "action": [
                    {"event": "test_event"},
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
                                    "for",
                                )
                            )
                        },
                    },
                ],
            }
        },
    )

    await opp.async_block_till_done()

    @callback
    def event_handler(event):
       .opp.states.async_set("test.entity", "hello")

   .opp.bus.async_listen_once("test_event", event_handler)

   .opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["some"] == "template - test.entity - hello - world - None"


async def test_if_fires_on_change_with_for.opp, calls):
    """Test for firing on change with for."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": "{{ is_state('test.entity', 'world') }}",
                    "for": {"seconds": 5},
                },
                "action": {"service": "test.automation"},
            }
        },
    )

   .opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 0
    async_fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_change_with_for_advanced.opp, calls):
    """Test for firing on change with for advanced."""
    context = Context()
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": '{{ is_state("test.entity", "world") }}',
                    "for": {"seconds": 5},
                },
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

   .opp.states.async_set("test.entity", "world", context=context)
    await opp.async_block_till_done()
    assert len(calls) == 0
    async_fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].context.parent_id == context.id
    assert "template - test.entity - hello - world - 0:00:05" == calls[0].data["some"]


async def test_if_fires_on_change_with_for_0.opp, calls):
    """Test for firing on change with for: 0."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": "{{ is_state('test.entity', 'world') }}",
                    "for": {"seconds": 0},
                },
                "action": {"service": "test.automation"},
            }
        },
    )

   .opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_change_with_for_0_advanced.opp, calls):
    """Test for firing on change with for: 0 advanced."""
    context = Context()
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": '{{ is_state("test.entity", "world") }}',
                    "for": {"seconds": 0},
                },
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

   .opp.states.async_set("test.entity", "world", context=context)
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].context.parent_id == context.id
    assert calls[0].data["some"] == "template - test.entity - hello - world - 0:00:00"


async def test_if_fires_on_change_with_for_2.opp, calls):
    """Test for firing on change with for."""
    context = Context()
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": "{{ is_state('test.entity', 'world') }}",
                    "for": 5,
                },
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

   .opp.states.async_set("test.entity", "world", context=context)
    await opp.async_block_till_done()
    assert len(calls) == 0
    async_fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].context.parent_id == context.id
    assert calls[0].data["some"] == "template - test.entity - hello - world - 0:00:05"


async def test_if_not_fires_on_change_with_for.opp, calls):
    """Test for firing on change with for."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": "{{ is_state('test.entity', 'world') }}",
                    "for": {"seconds": 5},
                },
                "action": {"service": "test.automation"},
            }
        },
    )

   .opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 0
    async_fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=4))
    await opp.async_block_till_done()
    assert len(calls) == 0
   .opp.states.async_set("test.entity", "hello")
    await opp.async_block_till_done()
    assert len(calls) == 0
    async_fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=6))
    await opp.async_block_till_done()
    assert len(calls) == 0


async def test_if_not_fires_when_turned_off_with_for.opp, calls):
    """Test for firing on change with for."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": "{{ is_state('test.entity', 'world') }}",
                    "for": {"seconds": 5},
                },
                "action": {"service": "test.automation"},
            }
        },
    )

   .opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 0
    async_fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=4))
    await opp.async_block_till_done()
    assert len(calls) == 0
    await opp.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )
    assert len(calls) == 0
    async_fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=6))
    await opp.async_block_till_done()
    assert len(calls) == 0


async def test_if_fires_on_change_with_for_template_1.opp, calls):
    """Test for firing on change with for template."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": "{{ is_state('test.entity', 'world') }}",
                    "for": {"seconds": "{{ 5 }}"},
                },
                "action": {"service": "test.automation"},
            }
        },
    )

   .opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 0
    async_fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_change_with_for_template_2.opp, calls):
    """Test for firing on change with for template."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": "{{ is_state('test.entity', 'world') }}",
                    "for": "{{ 5 }}",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

   .opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 0
    async_fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_on_change_with_for_template_3.opp, calls):
    """Test for firing on change with for template."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": "{{ is_state('test.entity', 'world') }}",
                    "for": "00:00:{{ 5 }}",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

   .opp.states.async_set("test.entity", "world")
    await opp.async_block_till_done()
    assert len(calls) == 0
    async_fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 1


async def test_invalid_for_template_1.opp, calls):
    """Test for invalid for template."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "template",
                    "value_template": "{{ is_state('test.entity', 'world') }}",
                    "for": {"seconds": "{{ five }}"},
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    with mock.patch.object(template_trigger, "_LOGGER") as mock_logger:
       .opp.states.async_set("test.entity", "world")
        await opp.async_block_till_done()
        assert mock_logger.error.called


async def test_if_fires_on_time_change.opp, calls):
    """Test for firing on time changes."""
    start_time = dt_util.utcnow() + timedelta(hours=24)
    time_that_will_not_match_right_away = start_time.replace(minute=1, second=0)
    with patch(
        "openpeerpower.util.dt.utcnow", return_value=time_that_will_not_match_right_away
    ):
        assert await async_setup_component(
           .opp,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "template",
                        "value_template": "{{ utcnow().minute % 2 == 0 }}",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
        await opp.async_block_till_done()
        assert len(calls) == 0

    # Trigger once (match template)
    first_time = start_time.replace(minute=2, second=0)
    with patch("openpeerpower.util.dt.utcnow", return_value=first_time):
        async_fire_time_changed.opp, first_time)
        await opp.async_block_till_done()
    assert len(calls) == 1

    # Trigger again (match template)
    second_time = start_time.replace(minute=4, second=0)
    with patch("openpeerpower.util.dt.utcnow", return_value=second_time):
        async_fire_time_changed.opp, second_time)
        await opp.async_block_till_done()
    await opp.async_block_till_done()
    assert len(calls) == 1

    # Trigger again (do not match template)
    third_time = start_time.replace(minute=5, second=0)
    with patch("openpeerpower.util.dt.utcnow", return_value=third_time):
        async_fire_time_changed.opp, third_time)
        await opp.async_block_till_done()
    await opp.async_block_till_done()
    assert len(calls) == 1

    # Trigger again (match template)
    forth_time = start_time.replace(minute=8, second=0)
    with patch("openpeerpower.util.dt.utcnow", return_value=forth_time):
        async_fire_time_changed.opp, forth_time)
        await opp.async_block_till_done()
    await opp.async_block_till_done()
    assert len(calls) == 2
