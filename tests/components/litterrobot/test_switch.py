"""Test the Litter-Robot switch entity."""
from datetime import timedelta

import pytest

from openpeerpower.components.litterrobot.entity import REFRESH_WAIT_TIME_SECONDS
from openpeerpower.components.switch import (
    DOMAIN as PLATFORM_DOMAIN,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from openpeerpower.const import ATTR_ENTITY_ID, STATE_ON
from openpeerpower.util.dt import utcnow

from .conftest import setup_integration

from tests.common import async_fire_time_changed

NIGHT_LIGHT_MODE_ENTITY_ID = "switch.test_night_light_mode"
PANEL_LOCKOUT_ENTITY_ID = "switch.test_panel_lockout"


async def test_switch(opp, mock_account):
    """Tests the switch entity was set up."""
    await setup_integration(opp, mock_account, PLATFORM_DOMAIN)

    switch = opp.states.get(NIGHT_LIGHT_MODE_ENTITY_ID)
    assert switch
    assert switch.state == STATE_ON


@pytest.mark.parametrize(
    "entity_id,robot_command",
    [
        (NIGHT_LIGHT_MODE_ENTITY_ID, "set_night_light"),
        (PANEL_LOCKOUT_ENTITY_ID, "set_panel_lockout"),
    ],
)
async def test_on_off_commands(opp, mock_account, entity_id, robot_command):
    """Test sending commands to the switch."""
    await setup_integration(opp, mock_account, PLATFORM_DOMAIN)

    switch = opp.states.get(entity_id)
    assert switch

    data = {ATTR_ENTITY_ID: entity_id}

    count = 0
    for service in [SERVICE_TURN_ON, SERVICE_TURN_OFF]:
        count += 1

        await opp.services.async_call(
            PLATFORM_DOMAIN,
            service,
            data,
            blocking=True,
        )

        future = utcnow() + timedelta(seconds=REFRESH_WAIT_TIME_SECONDS)
        async_fire_time_changed(opp, future)
        assert getattr(mock_account.robots[0], robot_command).call_count == count
