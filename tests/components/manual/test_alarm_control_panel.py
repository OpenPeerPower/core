"""The tests for the manual Alarm Control Panel component."""
from datetime import timedelta
from unittest.mock import MagicMock, patch

from openpeerpower.components import alarm_control_panel
from openpeerpower.components.demo import alarm_control_panel as demo
from openpeerpower.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_CUSTOM_BYPASS,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMING,
    STATE_ALARM_DISARMED,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
)
from openpeerpower.core import CoreState, State
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util

from tests.common import async_fire_time_changed, mock_component, mock_restore_cache
from tests.components.alarm_control_panel import common

CODE = "HELLO_CODE"


async def test_setup_demo_platform.opp):
    """Test setup."""
    mock = MagicMock()
    add_entities = mock.MagicMock()
    await demo.async_setup_platform.opp, {}, add_entities)
    assert add_entities.call_count == 1


async def test_arm_home_no_pending.opp):
    """Test arm home method."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code": CODE,
                "arming_time": 0,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_home.opp, CODE)

    assert STATE_ALARM_ARMED_HOME == opp.states.get(entity_id).state


async def test_arm_home_no_pending_when_code_not_req.opp):
    """Test arm home method."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code": CODE,
                "code_arm_required": False,
                "arming_time": 0,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_home.opp, 0)

    assert STATE_ALARM_ARMED_HOME == opp.states.get(entity_id).state


async def test_arm_home_with_pending.opp):
    """Test arm home method."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code": CODE,
                "arming_time": 1,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_home.opp, CODE, entity_id)

    assert STATE_ALARM_ARMING == opp.states.get(entity_id).state

    state = opp.states.get(entity_id)
    assert state.attributes["next_state"] == STATE_ALARM_ARMED_HOME

    future = dt_util.utcnow() + timedelta(seconds=1)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state.state == STATE_ALARM_ARMED_HOME


async def test_arm_home_with_invalid_code.opp):
    """Attempt to arm home without a valid code."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code": CODE,
                "arming_time": 1,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_home.opp, CODE + "2")

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state


async def test_arm_away_no_pending.opp):
    """Test arm home method."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code": CODE,
                "arming_time": 0,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_away.opp, CODE, entity_id)

    assert STATE_ALARM_ARMED_AWAY == opp.states.get(entity_id).state


async def test_arm_away_no_pending_when_code_not_req.opp):
    """Test arm home method."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code": CODE,
                "code_arm_required": False,
                "arming_time": 0,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_away.opp, 0, entity_id)

    assert STATE_ALARM_ARMED_AWAY == opp.states.get(entity_id).state


async def test_arm_home_with_template_code.opp):
    """Attempt to arm with a template-based code."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code_template": '{{ "abc" }}',
                "arming_time": 0,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_home.opp, "abc")

    state = opp.states.get(entity_id)
    assert STATE_ALARM_ARMED_HOME == state.state


async def test_arm_away_with_pending.opp):
    """Test arm home method."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code": CODE,
                "arming_time": 1,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_away.opp, CODE)

    assert STATE_ALARM_ARMING == opp.states.get(entity_id).state

    state = opp.states.get(entity_id)
    assert state.attributes["next_state"] == STATE_ALARM_ARMED_AWAY

    future = dt_util.utcnow() + timedelta(seconds=1)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state.state == STATE_ALARM_ARMED_AWAY


async def test_arm_away_with_invalid_code.opp):
    """Attempt to arm away without a valid code."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code": CODE,
                "arming_time": 1,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_away.opp, CODE + "2")

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state


async def test_arm_night_no_pending.opp):
    """Test arm night method."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code": CODE,
                "arming_time": 0,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_night.opp, CODE)

    assert STATE_ALARM_ARMED_NIGHT == opp.states.get(entity_id).state


async def test_arm_night_no_pending_when_code_not_req.opp):
    """Test arm night method."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code": CODE,
                "code_arm_required": False,
                "arming_time": 0,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_night.opp, 0)

    assert STATE_ALARM_ARMED_NIGHT == opp.states.get(entity_id).state


async def test_arm_night_with_pending.opp):
    """Test arm night method."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code": CODE,
                "arming_time": 1,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_night.opp, CODE, entity_id)

    assert STATE_ALARM_ARMING == opp.states.get(entity_id).state

    state = opp.states.get(entity_id)
    assert state.attributes["next_state"] == STATE_ALARM_ARMED_NIGHT

    future = dt_util.utcnow() + timedelta(seconds=1)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state.state == STATE_ALARM_ARMED_NIGHT

    # Do not go to the pending state when updating to the same state
    await common.async_alarm_arm_night.opp, CODE, entity_id)

    assert STATE_ALARM_ARMED_NIGHT == opp.states.get(entity_id).state


async def test_arm_night_with_invalid_code.opp):
    """Attempt to night home without a valid code."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code": CODE,
                "arming_time": 1,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_night.opp, CODE + "2")

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state


async def test_trigger_no_pending.opp):
    """Test triggering when no pending submitted method."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "trigger_time": 1,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_trigger.opp, entity_id=entity_id)

    assert STATE_ALARM_PENDING == opp.states.get(entity_id).state

    future = dt_util.utcnow() + timedelta(seconds=60)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    assert STATE_ALARM_TRIGGERED == opp.states.get(entity_id).state


async def test_trigger_with_delay.opp):
    """Test trigger method and switch from pending to triggered."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code": CODE,
                "delay_time": 1,
                "arming_time": 0,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_away.opp, CODE)

    assert STATE_ALARM_ARMED_AWAY == opp.states.get(entity_id).state

    await common.async_alarm_trigger.opp, entity_id=entity_id)

    state = opp.states.get(entity_id)
    assert STATE_ALARM_PENDING == state.state
    assert STATE_ALARM_TRIGGERED == state.attributes["next_state"]

    future = dt_util.utcnow() + timedelta(seconds=1)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert STATE_ALARM_TRIGGERED == state.state


async def test_trigger_zero_trigger_time.opp):
    """Test disabled trigger."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "arming_time": 0,
                "trigger_time": 0,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_trigger.opp)

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state


async def test_trigger_zero_trigger_time_with_pending.opp):
    """Test disabled trigger."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "arming_time": 2,
                "trigger_time": 0,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_trigger.opp)

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state


async def test_trigger_with_pending.opp):
    """Test arm home method."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "delay_time": 2,
                "trigger_time": 3,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_trigger.opp)

    assert STATE_ALARM_PENDING == opp.states.get(entity_id).state

    state = opp.states.get(entity_id)
    assert state.attributes["next_state"] == STATE_ALARM_TRIGGERED

    future = dt_util.utcnow() + timedelta(seconds=2)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state.state == STATE_ALARM_TRIGGERED

    future = dt_util.utcnow() + timedelta(seconds=5)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state.state == STATE_ALARM_DISARMED


async def test_trigger_with_unused_specific_delay.opp):
    """Test trigger method and switch from pending to triggered."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code": CODE,
                "delay_time": 5,
                "arming_time": 0,
                "armed_home": {"delay_time": 10},
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_away.opp, CODE)

    assert STATE_ALARM_ARMED_AWAY == opp.states.get(entity_id).state

    await common.async_alarm_trigger.opp, entity_id=entity_id)

    state = opp.states.get(entity_id)
    assert STATE_ALARM_PENDING == state.state
    assert STATE_ALARM_TRIGGERED == state.attributes["next_state"]

    future = dt_util.utcnow() + timedelta(seconds=5)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state.state == STATE_ALARM_TRIGGERED


async def test_trigger_with_specific_delay.opp):
    """Test trigger method and switch from pending to triggered."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code": CODE,
                "delay_time": 10,
                "arming_time": 0,
                "armed_away": {"delay_time": 1},
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_away.opp, CODE)

    assert STATE_ALARM_ARMED_AWAY == opp.states.get(entity_id).state

    await common.async_alarm_trigger.opp, entity_id=entity_id)

    state = opp.states.get(entity_id)
    assert STATE_ALARM_PENDING == state.state
    assert STATE_ALARM_TRIGGERED == state.attributes["next_state"]

    future = dt_util.utcnow() + timedelta(seconds=1)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state.state == STATE_ALARM_TRIGGERED


async def test_trigger_with_pending_and_delay.opp):
    """Test trigger method and switch from pending to triggered."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code": CODE,
                "delay_time": 2,
                "arming_time": 0,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_away.opp, CODE)

    assert STATE_ALARM_ARMED_AWAY == opp.states.get(entity_id).state

    await common.async_alarm_trigger.opp, entity_id=entity_id)

    state = opp.states.get(entity_id)
    assert state.state == STATE_ALARM_PENDING
    assert state.attributes["next_state"] == STATE_ALARM_TRIGGERED

    future = dt_util.utcnow() + timedelta(seconds=1)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state.state == STATE_ALARM_PENDING
    assert state.attributes["next_state"] == STATE_ALARM_TRIGGERED

    future += timedelta(seconds=1)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state.state == STATE_ALARM_TRIGGERED


async def test_trigger_with_pending_and_specific_delay.opp):
    """Test trigger method and switch from pending to triggered."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code": CODE,
                "delay_time": 10,
                "arming_time": 0,
                "armed_away": {"delay_time": 2},
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_away.opp, CODE)

    assert STATE_ALARM_ARMED_AWAY == opp.states.get(entity_id).state

    await common.async_alarm_trigger.opp, entity_id=entity_id)

    state = opp.states.get(entity_id)
    assert state.state == STATE_ALARM_PENDING
    assert state.attributes["next_state"] == STATE_ALARM_TRIGGERED

    future = dt_util.utcnow() + timedelta(seconds=1)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state.state == STATE_ALARM_PENDING
    assert state.attributes["next_state"] == STATE_ALARM_TRIGGERED

    future += timedelta(seconds=1)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state.state == STATE_ALARM_TRIGGERED


async def test_armed_home_with_specific_pending.opp):
    """Test arm home method."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "arming_time": 10,
                "armed_home": {"arming_time": 2},
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    await common.async_alarm_arm_home.opp)

    assert STATE_ALARM_ARMING == opp.states.get(entity_id).state

    future = dt_util.utcnow() + timedelta(seconds=2)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    assert STATE_ALARM_ARMED_HOME == opp.states.get(entity_id).state


async def test_armed_away_with_specific_pending.opp):
    """Test arm home method."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "arming_time": 10,
                "armed_away": {"arming_time": 2},
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    await common.async_alarm_arm_away.opp)

    assert STATE_ALARM_ARMING == opp.states.get(entity_id).state

    future = dt_util.utcnow() + timedelta(seconds=2)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    assert STATE_ALARM_ARMED_AWAY == opp.states.get(entity_id).state


async def test_armed_night_with_specific_pending.opp):
    """Test arm home method."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "arming_time": 10,
                "armed_night": {"arming_time": 2},
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    await common.async_alarm_arm_night.opp)

    assert STATE_ALARM_ARMING == opp.states.get(entity_id).state

    future = dt_util.utcnow() + timedelta(seconds=2)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    assert STATE_ALARM_ARMED_NIGHT == opp.states.get(entity_id).state


async def test_trigger_with_specific_pending.opp):
    """Test arm home method."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "delay_time": 10,
                "disarmed": {"delay_time": 2},
                "trigger_time": 3,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    await common.async_alarm_trigger.opp)

    assert STATE_ALARM_PENDING == opp.states.get(entity_id).state

    future = dt_util.utcnow() + timedelta(seconds=2)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    assert STATE_ALARM_TRIGGERED == opp.states.get(entity_id).state

    future = dt_util.utcnow() + timedelta(seconds=5)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state


async def test_trigger_with_disarm_after_trigger.opp):
    """Test disarm after trigger."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "trigger_time": 5,
                "delay_time": 0,
                "disarm_after_trigger": True,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_trigger.opp, entity_id=entity_id)

    assert STATE_ALARM_TRIGGERED == opp.states.get(entity_id).state

    future = dt_util.utcnow() + timedelta(seconds=5)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state


async def test_trigger_with_zero_specific_trigger_time.opp):
    """Test trigger method."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "trigger_time": 5,
                "disarmed": {"trigger_time": 0},
                "arming_time": 0,
                "disarm_after_trigger": True,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_trigger.opp, entity_id=entity_id)

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state


async def test_trigger_with_unused_zero_specific_trigger_time.opp):
    """Test disarm after trigger."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "trigger_time": 5,
                "armed_home": {"trigger_time": 0},
                "delay_time": 0,
                "disarm_after_trigger": True,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_trigger.opp, entity_id=entity_id)

    assert STATE_ALARM_TRIGGERED == opp.states.get(entity_id).state

    future = dt_util.utcnow() + timedelta(seconds=5)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state


async def test_trigger_with_specific_trigger_time.opp):
    """Test disarm after trigger."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "disarmed": {"trigger_time": 5},
                "delay_time": 0,
                "disarm_after_trigger": True,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_trigger.opp, entity_id=entity_id)

    assert STATE_ALARM_TRIGGERED == opp.states.get(entity_id).state

    future = dt_util.utcnow() + timedelta(seconds=5)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state


async def test_trigger_with_no_disarm_after_trigger.opp):
    """Test disarm after trigger."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "trigger_time": 5,
                "arming_time": 0,
                "delay_time": 0,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_away.opp, CODE, entity_id)

    assert STATE_ALARM_ARMED_AWAY == opp.states.get(entity_id).state

    await common.async_alarm_trigger.opp, entity_id=entity_id)

    assert STATE_ALARM_TRIGGERED == opp.states.get(entity_id).state

    future = dt_util.utcnow() + timedelta(seconds=5)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    assert STATE_ALARM_ARMED_AWAY == opp.states.get(entity_id).state


async def test_back_to_back_trigger_with_no_disarm_after_trigger.opp):
    """Test disarm after trigger."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "trigger_time": 5,
                "arming_time": 0,
                "delay_time": 0,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_away.opp, CODE, entity_id)

    assert STATE_ALARM_ARMED_AWAY == opp.states.get(entity_id).state

    await common.async_alarm_trigger.opp, entity_id=entity_id)

    assert STATE_ALARM_TRIGGERED == opp.states.get(entity_id).state

    future = dt_util.utcnow() + timedelta(seconds=5)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    assert STATE_ALARM_ARMED_AWAY == opp.states.get(entity_id).state

    await common.async_alarm_trigger.opp, entity_id=entity_id)

    assert STATE_ALARM_TRIGGERED == opp.states.get(entity_id).state

    future = dt_util.utcnow() + timedelta(seconds=5)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    assert STATE_ALARM_ARMED_AWAY == opp.states.get(entity_id).state


async def test_disarm_while_pending_trigger.opp):
    """Test disarming while pending state."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "trigger_time": 5,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_trigger.opp)

    assert STATE_ALARM_PENDING == opp.states.get(entity_id).state

    await common.async_alarm_disarm.opp, entity_id=entity_id)

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    future = dt_util.utcnow() + timedelta(seconds=5)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state


async def test_disarm_during_trigger_with_invalid_code.opp):
    """Test disarming while code is invalid."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "delay_time": 5,
                "code": CODE + "2",
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_trigger.opp)

    assert STATE_ALARM_PENDING == opp.states.get(entity_id).state

    await common.async_alarm_disarm.opp, entity_id=entity_id)

    assert STATE_ALARM_PENDING == opp.states.get(entity_id).state

    future = dt_util.utcnow() + timedelta(seconds=5)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    assert STATE_ALARM_TRIGGERED == opp.states.get(entity_id).state


async def test_disarm_with_template_code.opp):
    """Attempt to disarm with a valid or invalid template-based code."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code_template": '{{ "" if from_state == "disarmed" else "abc" }}',
                "arming_time": 0,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_home.opp, "def")

    state = opp.states.get(entity_id)
    assert STATE_ALARM_ARMED_HOME == state.state

    await common.async_alarm_disarm.opp, "def")

    state = opp.states.get(entity_id)
    assert STATE_ALARM_ARMED_HOME == state.state

    await common.async_alarm_disarm.opp, "abc")

    state = opp.states.get(entity_id)
    assert STATE_ALARM_DISARMED == state.state


async def test_arm_custom_bypass_no_pending.opp):
    """Test arm custom bypass method."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code": CODE,
                "arming_time": 0,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_custom_bypass.opp, CODE)

    assert STATE_ALARM_ARMED_CUSTOM_BYPASS == opp.states.get(entity_id).state


async def test_arm_custom_bypass_no_pending_when_code_not_req.opp):
    """Test arm custom bypass method."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code": CODE,
                "code_arm_required": False,
                "arming_time": 0,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_custom_bypass.opp, 0)

    assert STATE_ALARM_ARMED_CUSTOM_BYPASS == opp.states.get(entity_id).state


async def test_arm_custom_bypass_with_pending.opp):
    """Test arm custom bypass method."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code": CODE,
                "arming_time": 1,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_custom_bypass.opp, CODE, entity_id)

    assert STATE_ALARM_ARMING == opp.states.get(entity_id).state

    state = opp.states.get(entity_id)
    assert state.attributes["next_state"] == STATE_ALARM_ARMED_CUSTOM_BYPASS

    future = dt_util.utcnow() + timedelta(seconds=1)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state.state == STATE_ALARM_ARMED_CUSTOM_BYPASS


async def test_arm_custom_bypass_with_invalid_code.opp):
    """Attempt to custom bypass without a valid code."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code": CODE,
                "arming_time": 1,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_custom_bypass.opp, CODE + "2")

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state


async def test_armed_custom_bypass_with_specific_pending.opp):
    """Test arm custom bypass method."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "arming_time": 10,
                "armed_custom_bypass": {"arming_time": 2},
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    await common.async_alarm_arm_custom_bypass.opp)

    assert STATE_ALARM_ARMING == opp.states.get(entity_id).state

    future = dt_util.utcnow() + timedelta(seconds=2)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    assert STATE_ALARM_ARMED_CUSTOM_BYPASS == opp.states.get(entity_id).state


async def test_arm_away_after_disabled_disarmed.opp, legacy_patchable_time):
    """Test pending state with and without zero trigger time."""
    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code": CODE,
                "arming_time": 0,
                "delay_time": 1,
                "armed_away": {"arming_time": 1},
                "disarmed": {"trigger_time": 0},
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert STATE_ALARM_DISARMED == opp.states.get(entity_id).state

    await common.async_alarm_arm_away.opp, CODE)

    state = opp.states.get(entity_id)
    assert STATE_ALARM_ARMING == state.state
    assert STATE_ALARM_DISARMED == state.attributes["previous_state"]
    assert STATE_ALARM_ARMED_AWAY == state.attributes["next_state"]

    await common.async_alarm_trigger.opp, entity_id=entity_id)

    state = opp.states.get(entity_id)
    assert STATE_ALARM_ARMING == state.state
    assert STATE_ALARM_DISARMED == state.attributes["previous_state"]
    assert STATE_ALARM_ARMED_AWAY == state.attributes["next_state"]

    future = dt_util.utcnow() + timedelta(seconds=1)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

        state = opp.states.get(entity_id)
        assert STATE_ALARM_ARMED_AWAY == state.state

        await common.async_alarm_trigger.opp, entity_id=entity_id)

        state = opp.states.get(entity_id)
        assert STATE_ALARM_PENDING == state.state
        assert STATE_ALARM_ARMED_AWAY == state.attributes["previous_state"]
        assert STATE_ALARM_TRIGGERED == state.attributes["next_state"]

    future += timedelta(seconds=1)
    with patch(
        ("openpeerpower.components.manual.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed.opp, future)
        await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert STATE_ALARM_TRIGGERED == state.state


async def test_restore_armed_state.opp):
    """Ensure armed state is restored on startup."""
    mock_restore_cache(
       .opp, (State("alarm_control_panel.test", STATE_ALARM_ARMED_AWAY),)
    )

   .opp.state = CoreState.starting
    mock_component.opp, "recorder")

    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "arming_time": 0,
                "trigger_time": 0,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    state = opp.states.get("alarm_control_panel.test")
    assert state
    assert state.state == STATE_ALARM_ARMED_AWAY


async def test_restore_disarmed_state.opp):
    """Ensure disarmed state is restored on startup."""
    mock_restore_cache.opp, (State("alarm_control_panel.test", STATE_ALARM_DISARMED),))

   .opp.state = CoreState.starting
    mock_component.opp, "recorder")

    assert await async_setup_component(
       .opp,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "arming_time": 0,
                "trigger_time": 0,
                "disarm_after_trigger": False,
            }
        },
    )
    await opp.async_block_till_done()

    state = opp.states.get("alarm_control_panel.test")
    assert state
    assert state.state == STATE_ALARM_DISARMED
