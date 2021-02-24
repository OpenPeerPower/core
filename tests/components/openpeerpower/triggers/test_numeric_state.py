"""The tests for numeric state automation."""
from datetime import timedelta
import logging
from unittest.mock import patch

import pytest
import voluptuous as vol

import openpeerpower.components.automation as automation
from openpeerpower.components.openpeerpower.triggers import (
    numeric_state as numeric_state_trigger,
)
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
def calls.opp,
    """Track calls to a mock service."""
    return async_mock_service.opp."test", "automation")


@pytest.fixture(autouse=True)
async def setup_comp.opp,
    """Initialize components."""
    mock_component.opp."group")
    await async_setup_component(
        opp,
        "input_number",
        {
            "input_number": {
                "value_3": {"min": 0, "max": 255, "initial": 3},
                "value_5": {"min": 0, "max": 255, "initial": 5},
                "value_8": {"min": 0, "max": 255, "initial": 8},
                "value_10": {"min": 0, "max": 255, "initial": 10},
                "value_12": {"min": 0, "max": 255, "initial": 12},
                "value_100": {"min": 0, "max": 255, "initial": 100},
            }
        },
    )


@pytest.mark.parametrize("below", (10, "input_number.value_10"))
async def test_if_not_fires_on_entity_removal.opp.calls, below):
    """Test the firing with removed entity."""
    opp.tates.async_set("test.entity", 11)

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "below": below,
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    # Entity disappears
    opp.tates.async_remove("test.entity")
    await opp.async_block_till_done()
    assert len(calls) == 0


@pytest.mark.parametrize("below", (10, "input_number.value_10"))
async def test_if_fires_on_entity_change_below.opp.calls, below):
    """Test the firing with changed entity."""
    opp.tates.async_set("test.entity", 11)
    await opp.async_block_till_done()

    context = Context()
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "below": below,
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    # 9 is below 10
    opp.tates.async_set("test.entity", 9, context=context)
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].context.parent_id == context.id

    # Set above 12 so the automation will fire again
    opp.tates.async_set("test.entity", 12)

    await opp.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )
    opp.tates.async_set("test.entity", 9)
    await opp.async_block_till_done()
    assert len(calls) == 1


@pytest.mark.parametrize("below", (10, "input_number.value_10"))
async def test_if_fires_on_entity_change_over_to_below.opp.calls, below):
    """Test the firing with changed entity."""
    opp.tates.async_set("test.entity", 11)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "below": below,
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    # 9 is below 10
    opp.tates.async_set("test.entity", 9)
    await opp.async_block_till_done()
    assert len(calls) == 1


@pytest.mark.parametrize("below", (10, "input_number.value_10"))
async def test_if_fires_on_entities_change_over_to_below.opp.calls, below):
    """Test the firing with changed entities."""
    opp.tates.async_set("test.entity_1", 11)
    opp.tates.async_set("test.entity_2", 11)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": ["test.entity_1", "test.entity_2"],
                    "below": below,
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    # 9 is below 10
    opp.tates.async_set("test.entity_1", 9)
    await opp.async_block_till_done()
    assert len(calls) == 1
    opp.tates.async_set("test.entity_2", 9)
    await opp.async_block_till_done()
    assert len(calls) == 2


@pytest.mark.parametrize("below", (10, "input_number.value_10"))
async def test_if_not_fires_on_entity_change_below_to_below.opp.calls, below):
    """Test the firing with changed entity."""
    context = Context()
    opp.tates.async_set("test.entity", 11)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "below": below,
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    # 9 is below 10 so this should fire
    opp.tates.async_set("test.entity", 9, context=context)
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].context.parent_id == context.id

    # already below so should not fire again
    opp.tates.async_set("test.entity", 5)
    await opp.async_block_till_done()
    assert len(calls) == 1

    # still below so should not fire again
    opp.tates.async_set("test.entity", 3)
    await opp.async_block_till_done()
    assert len(calls) == 1


@pytest.mark.parametrize("below", (10, "input_number.value_10"))
async def test_if_not_below_fires_on_entity_change_to_equal.opp.calls, below):
    """Test the firing with changed entity."""
    opp.tates.async_set("test.entity", 11)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "below": below,
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    # 10 is not below 10 so this should not fire again
    opp.tates.async_set("test.entity", 10)
    await opp.async_block_till_done()
    assert len(calls) == 0


@pytest.mark.parametrize("below", (10, "input_number.value_10"))
async def test_if_fires_on_initial_entity_below.opp.calls, below):
    """Test the firing when starting with a match."""
    opp.tates.async_set("test.entity", 9)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "below": below,
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    # Fire on first update even if initial state was already below
    opp.tates.async_set("test.entity", 8)
    await opp.async_block_till_done()
    assert len(calls) == 1


@pytest.mark.parametrize("above", (10, "input_number.value_10"))
async def test_if_fires_on_initial_entity_above.opp.calls, above):
    """Test the firing when starting with a match."""
    opp.tates.async_set("test.entity", 11)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "above": above,
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    # Fire on first update even if initial state was already above
    opp.tates.async_set("test.entity", 12)
    await opp.async_block_till_done()
    assert len(calls) == 1


@pytest.mark.parametrize("above", (10, "input_number.value_10"))
async def test_if_fires_on_entity_change_above.opp.calls, above):
    """Test the firing with changed entity."""
    opp.tates.async_set("test.entity", 9)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "above": above,
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    # 11 is above 10
    opp.tates.async_set("test.entity", 11)
    await opp.async_block_till_done()
    assert len(calls) == 1


@pytest.mark.parametrize("above", (10, "input_number.value_10"))
async def test_if_fires_on_entity_change_below_to_above.opp.calls, above):
    """Test the firing with changed entity."""
    # set initial state
    opp.tates.async_set("test.entity", 9)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "above": above,
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    # 11 is above 10 and 9 is below
    opp.tates.async_set("test.entity", 11)
    await opp.async_block_till_done()
    assert len(calls) == 1


@pytest.mark.parametrize("above", (10, "input_number.value_10"))
async def test_if_not_fires_on_entity_change_above_to_above.opp.calls, above):
    """Test the firing with changed entity."""
    # set initial state
    opp.tates.async_set("test.entity", 9)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "above": above,
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    # 12 is above 10 so this should fire
    opp.tates.async_set("test.entity", 12)
    await opp.async_block_till_done()
    assert len(calls) == 1

    # already above, should not fire again
    opp.tates.async_set("test.entity", 15)
    await opp.async_block_till_done()
    assert len(calls) == 1


@pytest.mark.parametrize("above", (10, "input_number.value_10"))
async def test_if_not_above_fires_on_entity_change_to_equal.opp.calls, above):
    """Test the firing with changed entity."""
    # set initial state
    opp.tates.async_set("test.entity", 9)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "above": above,
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    # 10 is not above 10 so this should not fire again
    opp.tates.async_set("test.entity", 10)
    await opp.async_block_till_done()
    assert len(calls) == 0


@pytest.mark.parametrize(
    "above, below",
    (
        (5, 10),
        (5, "input_number.value_10"),
        ("input_number.value_5", 10),
        ("input_number.value_5", "input_number.value_10"),
    ),
)
async def test_if_fires_on_entity_change_below_range.opp.calls, above, below):
    """Test the firing with changed entity."""
    opp.tates.async_set("test.entity", 11)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "below": below,
                    "above": above,
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    # 9 is below 10
    opp.tates.async_set("test.entity", 9)
    await opp.async_block_till_done()
    assert len(calls) == 1


@pytest.mark.parametrize(
    "above, below",
    (
        (5, 10),
        (5, "input_number.value_10"),
        ("input_number.value_5", 10),
        ("input_number.value_5", "input_number.value_10"),
    ),
)
async def test_if_fires_on_entity_change_below_above_range.opp.calls, above, below):
    """Test the firing with changed entity."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "below": below,
                    "above": above,
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    # 4 is below 5
    opp.tates.async_set("test.entity", 4)
    await opp.async_block_till_done()
    assert len(calls) == 0


@pytest.mark.parametrize(
    "above, below",
    (
        (5, 10),
        (5, "input_number.value_10"),
        ("input_number.value_5", 10),
        ("input_number.value_5", "input_number.value_10"),
    ),
)
async def test_if_fires_on_entity_change_over_to_below_range.opp.calls, above, below):
    """Test the firing with changed entity."""
    opp.tates.async_set("test.entity", 11)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "below": below,
                    "above": above,
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    # 9 is below 10
    opp.tates.async_set("test.entity", 9)
    await opp.async_block_till_done()
    assert len(calls) == 1


@pytest.mark.parametrize(
    "above, below",
    (
        (5, 10),
        (5, "input_number.value_10"),
        ("input_number.value_5", 10),
        ("input_number.value_5", "input_number.value_10"),
    ),
)
async def test_if_fires_on_entity_change_over_to_below_above_range(
    opp.calls, above, below
):
    """Test the firing with changed entity."""
    opp.tates.async_set("test.entity", 11)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "below": above,
                    "above": below,
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    # 4 is below 5 so it should not fire
    opp.tates.async_set("test.entity", 4)
    await opp.async_block_till_done()
    assert len(calls) == 0


@pytest.mark.parametrize("below", (100, "input_number.value_100"))
async def test_if_not_fires_if_entity_not_match.opp.calls, below):
    """Test if not fired with non matching entity."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.another_entity",
                    "below": below,
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.tates.async_set("test.entity", 11)
    await opp.async_block_till_done()
    assert len(calls) == 0


async def test_if_not_fires_and_warns_if_below_entity_unknown.opp.caplog, calls):
    """Test if warns with unknown below entity."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "below": "input_number.unknown",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    caplog.clear()
    caplog.set_level(logging.WARNING)

    opp.tates.async_set("test.entity", 1)
    await opp.async_block_till_done()
    assert len(calls) == 0

    assert len(caplog.record_tuples) == 1
    assert caplog.record_tuples[0][1] == logging.WARNING


@pytest.mark.parametrize("below", (10, "input_number.value_10"))
async def test_if_fires_on_entity_change_below_with_attribute.opp.calls, below):
    """Test attributes change."""
    opp.tates.async_set("test.entity", 11, {"test_attribute": 11})
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "below": below,
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    # 9 is below 10
    opp.tates.async_set("test.entity", 9, {"test_attribute": 11})
    await opp.async_block_till_done()
    assert len(calls) == 1


@pytest.mark.parametrize("below", (10, "input_number.value_10"))
async def test_if_not_fires_on_entity_change_not_below_with_attribute(
    opp.calls, below
):
    """Test attributes."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "below": below,
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    # 11 is not below 10
    opp.tates.async_set("test.entity", 11, {"test_attribute": 9})
    await opp.async_block_till_done()
    assert len(calls) == 0


@pytest.mark.parametrize("below", (10, "input_number.value_10"))
async def test_if_fires_on_attribute_change_with_attribute_below.opp.calls, below):
    """Test attributes change."""
    opp.tates.async_set("test.entity", "entity", {"test_attribute": 11})
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "value_template": "{{ state.attributes.test_attribute }}",
                    "below": below,
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    # 9 is below 10
    opp.tates.async_set("test.entity", "entity", {"test_attribute": 9})
    await opp.async_block_till_done()
    assert len(calls) == 1


@pytest.mark.parametrize("below", (10, "input_number.value_10"))
async def test_if_not_fires_on_attribute_change_with_attribute_not_below(
    opp.calls, below
):
    """Test attributes change."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "value_template": "{{ state.attributes.test_attribute }}",
                    "below": below,
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    # 11 is not below 10
    opp.tates.async_set("test.entity", "entity", {"test_attribute": 11})
    await opp.async_block_till_done()
    assert len(calls) == 0


@pytest.mark.parametrize("below", (10, "input_number.value_10"))
async def test_if_not_fires_on_entity_change_with_attribute_below.opp.calls, below):
    """Test attributes change."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "value_template": "{{ state.attributes.test_attribute }}",
                    "below": below,
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    # 11 is not below 10, entity state value should not be tested
    opp.tates.async_set("test.entity", "9", {"test_attribute": 11})
    await opp.async_block_till_done()
    assert len(calls) == 0


@pytest.mark.parametrize("below", (10, "input_number.value_10"))
async def test_if_not_fires_on_entity_change_with_not_attribute_below(
    opp.calls, below
):
    """Test attributes change."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "value_template": "{{ state.attributes.test_attribute }}",
                    "below": below,
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    # 11 is not below 10, entity state value should not be tested
    opp.tates.async_set("test.entity", "entity")
    await opp.async_block_till_done()
    assert len(calls) == 0


@pytest.mark.parametrize("below", (10, "input_number.value_10"))
async def test_fires_on_attr_change_with_attribute_below_and_multiple_attr(
    opp.calls, below
):
    """Test attributes change."""
    opp.tates.async_set(
        "test.entity", "entity", {"test_attribute": 11, "not_test_attribute": 11}
    )
    await opp.async_block_till_done()
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "value_template": "{{ state.attributes.test_attribute }}",
                    "below": below,
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    # 9 is not below 10
    opp.tates.async_set(
        "test.entity", "entity", {"test_attribute": 9, "not_test_attribute": 11}
    )
    await opp.async_block_till_done()
    assert len(calls) == 1


@pytest.mark.parametrize("below", (10, "input_number.value_10"))
async def test_template_list.opp.calls, below):
    """Test template list."""
    opp.tates.async_set("test.entity", "entity", {"test_attribute": [11, 15, 11]})
    await opp.async_block_till_done()
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "value_template": "{{ state.attributes.test_attribute[2] }}",
                    "below": below,
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    # 3 is below 10
    opp.tates.async_set("test.entity", "entity", {"test_attribute": [11, 15, 3]})
    await opp.async_block_till_done()
    assert len(calls) == 1


@pytest.mark.parametrize("below", (10.0, "input_number.value_10"))
async def test_template_string.opp.calls, below):
    """Test template string."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "value_template": "{{ state.attributes.test_attribute | multiply(10) }}",
                    "below": below,
                },
                "action": {
                    "service": "test.automation",
                    "data_template": {
                        "some": "{{ trigger.%s }}"
                        % "}} - {{ trigger.".join(
                            (
                                "platform",
                                "entity_id",
                                "below",
                                "above",
                                "from_state.state",
                                "to_state.state",
                            )
                        )
                    },
                },
            }
        },
    )
    opp.tates.async_set("test.entity", "test state 1", {"test_attribute": "1.2"})
    await opp.async_block_till_done()
    opp.tates.async_set("test.entity", "test state 2", {"test_attribute": "0.9"})
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert (
        calls[0].data["some"]
        == f"numeric_state - test.entity - {below} - None - test state 1 - test state 2"
    )


async def test_not_fires_on_attr_change_with_attr_not_below_multiple_attr.opp.calls):
    """Test if not fired changed attributes."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "value_template": "{{ state.attributes.test_attribute }}",
                    "below": 10,
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    # 11 is not below 10
    opp.tates.async_set(
        "test.entity", "entity", {"test_attribute": 11, "not_test_attribute": 9}
    )
    await opp.async_block_till_done()
    assert len(calls) == 0


@pytest.mark.parametrize(
    "above, below",
    (
        (8, 12),
        (8, "input_number.value_12"),
        ("input_number.value_8", 12),
        ("input_number.value_8", "input_number.value_12"),
    ),
)
async def test_if_action.opp.calls, above, below):
    """Test if action."""
    entity_id = "domain.test_entity"
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "event", "event_type": "test_event"},
                "condition": {
                    "condition": "numeric_state",
                    "entity_id": entity_id,
                    "above": above,
                    "below": below,
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.tates.async_set(entity_id, 10)
    opp.us.async_fire("test_event")
    await opp.async_block_till_done()

    assert len(calls) == 1

    opp.tates.async_set(entity_id, 8)
    opp.us.async_fire("test_event")
    await opp.async_block_till_done()

    assert len(calls) == 1

    opp.tates.async_set(entity_id, 9)
    opp.us.async_fire("test_event")
    await opp.async_block_till_done()

    assert len(calls) == 2


@pytest.mark.parametrize(
    "above, below",
    (
        (8, 12),
        (8, "input_number.value_12"),
        ("input_number.value_8", 12),
        ("input_number.value_8", "input_number.value_12"),
    ),
)
async def test_if_fails_setup_bad_for.opp.calls, above, below):
    """Test for setup failure for bad for."""
    opp.tates.async_set("test.entity", 5)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "above": above,
                    "below": below,
                    "for": {"invalid": 5},
                },
                "action": {"service": "openpeerpower.turn_on"},
            }
        },
    )

    with patch.object(numeric_state_trigger, "_LOGGER") as mock_logger:
        opp.tates.async_set("test.entity", 9)
        await opp.async_block_till_done()
        assert mock_logger.error.called


async def test_if_fails_setup_for_without_above_below.opp.calls):
    """Test for setup failures for missing above or below."""
    with assert_setup_component(0, automation.DOMAIN):
        assert await async_setup_component(
            opp,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "for": {"seconds": 5},
                    },
                    "action": {"service": "openpeerpower.turn_on"},
                }
            },
        )


@pytest.mark.parametrize(
    "above, below",
    (
        (8, 12),
        (8, "input_number.value_12"),
        ("input_number.value_8", 12),
        ("input_number.value_8", "input_number.value_12"),
    ),
)
async def test_if_not_fires_on_entity_change_with_for.opp.calls, above, below):
    """Test for not firing on entity change with for."""
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "above": above,
                    "below": below,
                    "for": {"seconds": 5},
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.tates.async_set("test.entity", 9)
    await opp.async_block_till_done()
    opp.tates.async_set("test.entity", 15)
    await opp.async_block_till_done()
    async_fire_time_changed.opp.dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 0


@pytest.mark.parametrize(
    "above, below",
    (
        (8, 12),
        (8, "input_number.value_12"),
        ("input_number.value_8", 12),
        ("input_number.value_8", "input_number.value_12"),
    ),
)
async def test_if_not_fires_on_entities_change_with_for_after_stop(
    opp.calls, above, below
):
    """Test for not firing on entities change with for after stop."""
    opp.tates.async_set("test.entity_1", 0)
    opp.tates.async_set("test.entity_2", 0)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": ["test.entity_1", "test.entity_2"],
                    "above": above,
                    "below": below,
                    "for": {"seconds": 5},
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.tates.async_set("test.entity_1", 9)
    opp.tates.async_set("test.entity_2", 9)
    await opp.async_block_till_done()
    async_fire_time_changed.opp.dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 1

    opp.tates.async_set("test.entity_1", 15)
    opp.tates.async_set("test.entity_2", 15)
    await opp.async_block_till_done()
    opp.tates.async_set("test.entity_1", 9)
    opp.tates.async_set("test.entity_2", 9)
    await opp.async_block_till_done()
    await opp.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )
    async_fire_time_changed.opp.dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 1


@pytest.mark.parametrize(
    "above, below",
    (
        (8, 12),
        (8, "input_number.value_12"),
        ("input_number.value_8", 12),
        ("input_number.value_8", "input_number.value_12"),
    ),
)
async def test_if_fires_on_entity_change_with_for_attribute_change(
    opp.calls, above, below
):
    """Test for firing on entity change with for and attribute change."""
    opp.tates.async_set("test.entity", 0)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "above": above,
                    "below": below,
                    "for": {"seconds": 5},
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    utcnow = dt_util.utcnow()
    with patch("openpeerpower.core.dt_util.utcnow") as mock_utcnow:
        mock_utcnow.return_value = utcnow
        opp.tates.async_set("test.entity", 9)
        await opp.async_block_till_done()
        mock_utcnow.return_value += timedelta(seconds=4)
        async_fire_time_changed.opp.mock_utcnow.return_value)
        opp.tates.async_set("test.entity", 9, attributes={"mock_attr": "attr_change"})
        await opp.async_block_till_done()
        assert len(calls) == 0
        mock_utcnow.return_value += timedelta(seconds=4)
        async_fire_time_changed.opp.mock_utcnow.return_value)
        await opp.async_block_till_done()
        assert len(calls) == 1


@pytest.mark.parametrize(
    "above, below",
    (
        (8, 12),
        (8, "input_number.value_12"),
        ("input_number.value_8", 12),
        ("input_number.value_8", "input_number.value_12"),
    ),
)
async def test_if_fires_on_entity_change_with_for.opp.calls, above, below):
    """Test for firing on entity change with for."""
    opp.tates.async_set("test.entity", 0)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "above": above,
                    "below": below,
                    "for": {"seconds": 5},
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.tates.async_set("test.entity", 9)
    await opp.async_block_till_done()
    async_fire_time_changed.opp.dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 1


@pytest.mark.parametrize("above", (10, "input_number.value_10"))
async def test_wait_template_with_trigger.opp.calls, above):
    """Test using wait template with 'trigger.entity_id'."""
    opp.tates.async_set("test.entity", "0")
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "above": above,
                },
                "action": [
                    {"wait_template": "{{ states(trigger.entity_id) | int < 10 }}"},
                    {
                        "service": "test.automation",
                        "data_template": {
                            "some": "{{ trigger.%s }}"
                            % "}} - {{ trigger.".join(
                                ("platform", "entity_id", "to_state.state")
                            )
                        },
                    },
                ],
            }
        },
    )

    await opp.async_block_till_done()

    opp.tates.async_set("test.entity", "12")
    opp.tates.async_set("test.entity", "8")
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["some"] == "numeric_state - test.entity - 12"


@pytest.mark.parametrize(
    "above, below",
    (
        (8, 12),
        (8, "input_number.value_12"),
        ("input_number.value_8", 12),
        ("input_number.value_8", "input_number.value_12"),
    ),
)
async def test_if_fires_on_entities_change_no_overlap.opp.calls, above, below):
    """Test for firing on entities change with no overlap."""
    opp.tates.async_set("test.entity_1", 0)
    opp.tates.async_set("test.entity_2", 0)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": ["test.entity_1", "test.entity_2"],
                    "above": above,
                    "below": below,
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
        opp.tates.async_set("test.entity_1", 9)
        await opp.async_block_till_done()
        mock_utcnow.return_value += timedelta(seconds=10)
        async_fire_time_changed.opp.mock_utcnow.return_value)
        await opp.async_block_till_done()
        assert len(calls) == 1
        assert calls[0].data["some"] == "test.entity_1"

        opp.tates.async_set("test.entity_2", 9)
        await opp.async_block_till_done()
        mock_utcnow.return_value += timedelta(seconds=10)
        async_fire_time_changed.opp.mock_utcnow.return_value)
        await opp.async_block_till_done()
        assert len(calls) == 2
        assert calls[1].data["some"] == "test.entity_2"


@pytest.mark.parametrize(
    "above, below",
    (
        (8, 12),
        (8, "input_number.value_12"),
        ("input_number.value_8", 12),
        ("input_number.value_8", "input_number.value_12"),
    ),
)
async def test_if_fires_on_entities_change_overlap.opp.calls, above, below):
    """Test for firing on entities change with overlap."""
    opp.tates.async_set("test.entity_1", 0)
    opp.tates.async_set("test.entity_2", 0)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": ["test.entity_1", "test.entity_2"],
                    "above": above,
                    "below": below,
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
        opp.tates.async_set("test.entity_1", 9)
        await opp.async_block_till_done()
        mock_utcnow.return_value += timedelta(seconds=1)
        async_fire_time_changed.opp.mock_utcnow.return_value)
        opp.tates.async_set("test.entity_2", 9)
        await opp.async_block_till_done()
        mock_utcnow.return_value += timedelta(seconds=1)
        async_fire_time_changed.opp.mock_utcnow.return_value)
        opp.tates.async_set("test.entity_2", 15)
        await opp.async_block_till_done()
        mock_utcnow.return_value += timedelta(seconds=1)
        async_fire_time_changed.opp.mock_utcnow.return_value)
        opp.tates.async_set("test.entity_2", 9)
        await opp.async_block_till_done()
        assert len(calls) == 0
        mock_utcnow.return_value += timedelta(seconds=3)
        async_fire_time_changed.opp.mock_utcnow.return_value)
        await opp.async_block_till_done()
        assert len(calls) == 1
        assert calls[0].data["some"] == "test.entity_1"

        mock_utcnow.return_value += timedelta(seconds=3)
        async_fire_time_changed.opp.mock_utcnow.return_value)
        await opp.async_block_till_done()
        assert len(calls) == 2
        assert calls[1].data["some"] == "test.entity_2"


@pytest.mark.parametrize(
    "above, below",
    (
        (8, 12),
        (8, "input_number.value_12"),
        ("input_number.value_8", 12),
        ("input_number.value_8", "input_number.value_12"),
    ),
)
async def test_if_fires_on_change_with_for_template_1.opp.calls, above, below):
    """Test for firing on  change with for template."""
    opp.tates.async_set("test.entity", 0)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "above": above,
                    "below": below,
                    "for": {"seconds": "{{ 5 }}"},
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.tates.async_set("test.entity", 9)
    await opp.async_block_till_done()
    assert len(calls) == 0
    async_fire_time_changed.opp.dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 1


@pytest.mark.parametrize(
    "above, below",
    (
        (8, 12),
        (8, "input_number.value_12"),
        ("input_number.value_8", 12),
        ("input_number.value_8", "input_number.value_12"),
    ),
)
async def test_if_fires_on_change_with_for_template_2.opp.calls, above, below):
    """Test for firing on  change with for template."""
    opp.tates.async_set("test.entity", 0)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "above": above,
                    "below": below,
                    "for": "{{ 5 }}",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.tates.async_set("test.entity", 9)
    await opp.async_block_till_done()
    assert len(calls) == 0
    async_fire_time_changed.opp.dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 1


@pytest.mark.parametrize(
    "above, below",
    (
        (8, 12),
        (8, "input_number.value_12"),
        ("input_number.value_8", 12),
        ("input_number.value_8", "input_number.value_12"),
    ),
)
async def test_if_fires_on_change_with_for_template_3.opp.calls, above, below):
    """Test for firing on  change with for template."""
    opp.tates.async_set("test.entity", 0)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "above": above,
                    "below": below,
                    "for": "00:00:{{ 5 }}",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    opp.tates.async_set("test.entity", 9)
    await opp.async_block_till_done()
    assert len(calls) == 0
    async_fire_time_changed.opp.dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 1


@pytest.mark.parametrize(
    "above, below",
    (
        (8, 12),
        (8, "input_number.value_12"),
        ("input_number.value_8", 12),
        ("input_number.value_8", "input_number.value_12"),
    ),
)
async def test_invalid_for_template.opp.calls, above, below):
    """Test for invalid for template."""
    opp.tates.async_set("test.entity", 0)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "above": above,
                    "below": below,
                    "for": "{{ five }}",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    with patch.object(numeric_state_trigger, "_LOGGER") as mock_logger:
        opp.tates.async_set("test.entity", 9)
        await opp.async_block_till_done()
        assert mock_logger.error.called


@pytest.mark.parametrize(
    "above, below",
    (
        (8, 12),
        (8, "input_number.value_12"),
        ("input_number.value_8", 12),
        ("input_number.value_8", "input_number.value_12"),
    ),
)
async def test_if_fires_on_entities_change_overlap_for_template(
    opp.calls, above, below
):
    """Test for firing on entities change with overlap and for template."""
    opp.tates.async_set("test.entity_1", 0)
    opp.tates.async_set("test.entity_2", 0)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": ["test.entity_1", "test.entity_2"],
                    "above": above,
                    "below": below,
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
    with patch("openpeerpower.util.dt.utcnow") as mock_utcnow:
        mock_utcnow.return_value = utcnow
        opp.tates.async_set("test.entity_1", 9)
        await opp.async_block_till_done()
        mock_utcnow.return_value += timedelta(seconds=1)
        async_fire_time_changed.opp.mock_utcnow.return_value)
        opp.tates.async_set("test.entity_2", 9)
        await opp.async_block_till_done()
        mock_utcnow.return_value += timedelta(seconds=1)
        async_fire_time_changed.opp.mock_utcnow.return_value)
        opp.tates.async_set("test.entity_2", 15)
        await opp.async_block_till_done()
        mock_utcnow.return_value += timedelta(seconds=1)
        async_fire_time_changed.opp.mock_utcnow.return_value)
        opp.tates.async_set("test.entity_2", 9)
        await opp.async_block_till_done()
        assert len(calls) == 0
        mock_utcnow.return_value += timedelta(seconds=3)
        async_fire_time_changed.opp.mock_utcnow.return_value)
        await opp.async_block_till_done()
        assert len(calls) == 1
        assert calls[0].data["some"] == "test.entity_1 - 0:00:05"

        mock_utcnow.return_value += timedelta(seconds=3)
        async_fire_time_changed.opp.mock_utcnow.return_value)
        await opp.async_block_till_done()
        assert len(calls) == 1
        mock_utcnow.return_value += timedelta(seconds=5)
        async_fire_time_changed.opp.mock_utcnow.return_value)
        await opp.async_block_till_done()
        assert len(calls) == 2
        assert calls[1].data["some"] == "test.entity_2 - 0:00:10"


def test_below_above():
    """Test above cannot be above below."""
    with pytest.raises(vol.Invalid):
        numeric_state_trigger.TRIGGER_SCHEMA(
            {"platform": "numeric_state", "above": 1200, "below": 1000}
        )


def test_schema_input_number():
    """Test input_number only is accepted for above/below."""
    with pytest.raises(vol.Invalid):
        numeric_state_trigger.TRIGGER_SCHEMA(
            {
                "platform": "numeric_state",
                "above": "input_datetime.some_input",
                "below": 1000,
            }
        )
    with pytest.raises(vol.Invalid):
        numeric_state_trigger.TRIGGER_SCHEMA(
            {
                "platform": "numeric_state",
                "below": "input_datetime.some_input",
                "above": 1200,
            }
        )


@pytest.mark.parametrize("above", (3, "input_number.value_3"))
async def test_attribute_if_fires_on_entity_change_with_both_filters(
    opp.calls, above
):
    """Test for firing if both filters are match attribute."""
    opp.tates.async_set("test.entity", "bla", {"test-measurement": 1})

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "above": above,
                    "attribute": "test-measurement",
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    opp.tates.async_set("test.entity", "bla", {"test-measurement": 4})
    await opp.async_block_till_done()
    assert len(calls) == 1


@pytest.mark.parametrize("above", (3, "input_number.value_3"))
async def test_attribute_if_not_fires_on_entities_change_with_for_after_stop(
    opp.calls, above
):
    """Test for not firing on entity change with for after stop trigger."""
    opp.tates.async_set("test.entity", "bla", {"test-measurement": 1})

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "above": above,
                    "attribute": "test-measurement",
                    "for": 5,
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    await opp.async_block_till_done()

    opp.tates.async_set("test.entity", "bla", {"test-measurement": 4})
    await opp.async_block_till_done()
    assert len(calls) == 0
    async_fire_time_changed.opp.dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 1


@pytest.mark.parametrize(
    "above, below",
    ((8, 12),),
)
async def test_variables_priority.opp.calls, above, below):
    """Test an externally defined trigger variable is overridden."""
    opp.tates.async_set("test.entity_1", 0)
    opp.tates.async_set("test.entity_2", 0)
    await opp.async_block_till_done()

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger_variables": {"trigger": "illegal"},
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": ["test.entity_1", "test.entity_2"],
                    "above": above,
                    "below": below,
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
    with patch("openpeerpower.util.dt.utcnow") as mock_utcnow:
        mock_utcnow.return_value = utcnow
        opp.tates.async_set("test.entity_1", 9)
        await opp.async_block_till_done()
        mock_utcnow.return_value += timedelta(seconds=1)
        async_fire_time_changed.opp.mock_utcnow.return_value)
        opp.tates.async_set("test.entity_2", 9)
        await opp.async_block_till_done()
        mock_utcnow.return_value += timedelta(seconds=1)
        async_fire_time_changed.opp.mock_utcnow.return_value)
        opp.tates.async_set("test.entity_2", 15)
        await opp.async_block_till_done()
        mock_utcnow.return_value += timedelta(seconds=1)
        async_fire_time_changed.opp.mock_utcnow.return_value)
        opp.tates.async_set("test.entity_2", 9)
        await opp.async_block_till_done()
        assert len(calls) == 0
        mock_utcnow.return_value += timedelta(seconds=3)
        async_fire_time_changed.opp.mock_utcnow.return_value)
        await opp.async_block_till_done()
        assert len(calls) == 1
        assert calls[0].data["some"] == "test.entity_1 - 0:00:05"


@pytest.mark.parametrize("multiplier", (1, 5))
async def test_template_variable.opp.calls, multiplier):
    """Test template variable."""
    opp.tates.async_set("test.entity", "entity", {"test_attribute": [11, 15, 11]})
    await opp.async_block_till_done()
    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger_variables": {"multiplier": multiplier},
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": "test.entity",
                    "value_template": "{{ state.attributes.test_attribute[2] * multiplier}}",
                    "below": 10,
                },
                "action": {"service": "test.automation"},
            }
        },
    )
    # 3 is below 10
    opp.tates.async_set("test.entity", "entity", {"test_attribute": [11, 15, 3]})
    await opp.async_block_till_done()
    if multiplier * 3 < 10:
        assert len(calls) == 1
    else:
        assert len(calls) == 0
