"""Test the Litter-Robot vacuum entity."""
from datetime import timedelta

import pytest
from voluptuous.error import MultipleInvalid

from openpeerpower.components.litterrobot import DOMAIN
from openpeerpower.components.litterrobot.entity import REFRESH_WAIT_TIME_SECONDS
from openpeerpower.components.litterrobot.vacuum import (
    SERVICE_RESET_WASTE_DRAWER,
    SERVICE_SET_SLEEP_MODE,
    SERVICE_SET_WAIT_TIME,
)
from openpeerpower.components.vacuum import (
    DOMAIN as PLATFORM_DOMAIN,
    SERVICE_START,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_DOCKED,
    STATE_ERROR,
)
from openpeerpower.const import ATTR_ENTITY_ID
from openpeerpower.core import OpenPeerPower
from openpeerpower.util.dt import utcnow

from .common import VACUUM_ENTITY_ID
from .conftest import setup_integration

from tests.common import async_fire_time_changed

COMPONENT_SERVICE_DOMAIN = {
    SERVICE_RESET_WASTE_DRAWER: DOMAIN,
    SERVICE_SET_SLEEP_MODE: DOMAIN,
    SERVICE_SET_WAIT_TIME: DOMAIN,
}


async def test_vacuum(opp: OpenPeerPower, mock_account):
    """Tests the vacuum entity was set up."""
    await setup_integration(opp, mock_account, PLATFORM_DOMAIN)
    assert opp.services.has_service(DOMAIN, SERVICE_RESET_WASTE_DRAWER)

    vacuum = opp.states.get(VACUUM_ENTITY_ID)
    assert vacuum
    assert vacuum.state == STATE_DOCKED
    assert vacuum.attributes["is_sleeping"] is False


async def test_no_robots(opp: OpenPeerPower, mock_account_with_no_robots):
    """Tests the vacuum entity was set up."""
    await setup_integration(opp, mock_account_with_no_robots, PLATFORM_DOMAIN)

    assert not opp.services.has_service(DOMAIN, SERVICE_RESET_WASTE_DRAWER)


async def test_vacuum_with_error(opp: OpenPeerPower, mock_account_with_error):
    """Tests a vacuum entity with an error."""
    await setup_integration(opp, mock_account_with_error, PLATFORM_DOMAIN)

    vacuum = opp.states.get(VACUUM_ENTITY_ID)
    assert vacuum
    assert vacuum.state == STATE_ERROR


@pytest.mark.parametrize(
    "service,command,extra",
    [
        (SERVICE_START, "start_cleaning", None),
        (SERVICE_TURN_OFF, "set_power_status", None),
        (SERVICE_TURN_ON, "set_power_status", None),
        (
            SERVICE_RESET_WASTE_DRAWER,
            "reset_waste_drawer",
            None,
        ),
        (
            SERVICE_SET_SLEEP_MODE,
            "set_sleep_mode",
            {"enabled": True, "start_time": "22:30"},
        ),
        (
            SERVICE_SET_SLEEP_MODE,
            "set_sleep_mode",
            {"enabled": True},
        ),
        (
            SERVICE_SET_SLEEP_MODE,
            "set_sleep_mode",
            {"enabled": False},
        ),
        (
            SERVICE_SET_WAIT_TIME,
            "set_wait_time",
            {"minutes": 3},
        ),
        (
            SERVICE_SET_WAIT_TIME,
            "set_wait_time",
            {"minutes": "15"},
        ),
    ],
)
async def test_commands(opp: OpenPeerPower, mock_account, service, command, extra):
    """Test sending commands to the vacuum."""
    await setup_integration(opp, mock_account, PLATFORM_DOMAIN)

    vacuum = opp.states.get(VACUUM_ENTITY_ID)
    assert vacuum
    assert vacuum.state == STATE_DOCKED

    data = {ATTR_ENTITY_ID: VACUUM_ENTITY_ID}
    if extra:
        data.update(extra)

    await opp.services.async_call(
        COMPONENT_SERVICE_DOMAIN.get(service, PLATFORM_DOMAIN),
        service,
        data,
        blocking=True,
    )
    future = utcnow() + timedelta(seconds=REFRESH_WAIT_TIME_SECONDS)
    async_fire_time_changed(opp, future)
    getattr(mock_account.robots[0], command).assert_called_once()


async def test_invalid_wait_time(opp: OpenPeerPower, mock_account):
    """Test an attempt to send an invalid wait time to the vacuum."""
    await setup_integration(opp, mock_account, PLATFORM_DOMAIN)

    vacuum = opp.states.get(VACUUM_ENTITY_ID)
    assert vacuum
    assert vacuum.state == STATE_DOCKED

    with pytest.raises(MultipleInvalid):
        await opp.services.async_call(
            DOMAIN,
            SERVICE_SET_WAIT_TIME,
            {ATTR_ENTITY_ID: VACUUM_ENTITY_ID, "minutes": 10},
            blocking=True,
        )
    assert not mock_account.robots[0].set_wait_time.called
