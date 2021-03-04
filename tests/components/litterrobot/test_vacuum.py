"""Test the Litter-Robot vacuum entity."""
from datetime import timedelta

import pytest

from openpeerpower.components.litterrobot.hub import REFRESH_WAIT_TIME
from openpeerpower.components.vacuum import (
    ATTR_PARAMS,
    DOMAIN as PLATFORM_DOMAIN,
    SERVICE_SEND_COMMAND,
    SERVICE_START,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_DOCKED,
)
from openpeerpower.const import ATTR_COMMAND, ATTR_ENTITY_ID
from openpeerpower.util.dt import utcnow

from .conftest import setup_hub

from tests.common import async_fire_time_changed

ENTITY_ID = "vacuum.test_litter_box"


async def test_vacuum(opp, mock_hub):
    """Tests the vacuum entity was set up."""
    await setup_hub(opp, mock_hub, PLATFORM_DOMAIN)

    vacuum = opp.states.get(ENTITY_ID)
    assert vacuum
    assert vacuum.state == STATE_DOCKED
    assert vacuum.attributes["is_sleeping"] is False


@pytest.mark.parametrize(
    "service,command,extra",
    [
        (SERVICE_START, "start_cleaning", None),
        (SERVICE_TURN_OFF, "set_power_status", None),
        (SERVICE_TURN_ON, "set_power_status", None),
        (
            SERVICE_SEND_COMMAND,
            "reset_waste_drawer",
            {ATTR_COMMAND: "reset_waste_drawer"},
        ),
        (
            SERVICE_SEND_COMMAND,
            "set_sleep_mode",
            {
                ATTR_COMMAND: "set_sleep_mode",
                ATTR_PARAMS: {"enabled": True, "sleep_time": "22:30"},
            },
        ),
    ],
)
async def test_commands(opp, mock_hub, service, command, extra):
    """Test sending commands to the vacuum."""
    await setup_hub(opp, mock_hub, PLATFORM_DOMAIN)

    vacuum = opp.states.get(ENTITY_ID)
    assert vacuum is not None
    assert vacuum.state == STATE_DOCKED

    data = {ATTR_ENTITY_ID: ENTITY_ID}
    if extra:
        data.update(extra)

    await opp.services.async_call(
        PLATFORM_DOMAIN,
        service,
        data,
        blocking=True,
    )
    future = utcnow() + timedelta(seconds=REFRESH_WAIT_TIME)
    async_fire_time_changed(opp, future)
    getattr(mock_hub.account.robots[0], command).assert_called_once()
