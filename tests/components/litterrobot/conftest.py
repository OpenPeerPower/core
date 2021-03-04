"""Configure pytest for Litter-Robot tests."""
from unittest.mock import AsyncMock, MagicMock, patch

from pylitterbot import Robot
import pytest

from openpeerpower.components import litterrobot
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator

from .common import CONFIG, ROBOT_DATA

from tests.common import MockConfigEntry


def create_mock_robot(opp):
    """Create a mock Litter-Robot device."""
    robot = Robot(data=ROBOT_DATA)
    robot.start_cleaning = AsyncMock()
    robot.set_power_status = AsyncMock()
    robot.reset_waste_drawer = AsyncMock()
    robot.set_sleep_mode = AsyncMock()
    robot.set_night_light = AsyncMock()
    robot.set_panel_lockout = AsyncMock()
    return robot


@pytest.fixture()
def mock_hub(opp):
    """Mock a Litter-Robot hub."""
    hub = MagicMock(
        opp=opp,
        account=MagicMock(),
        logged_in=True,
        coordinator=MagicMock(spec=DataUpdateCoordinator),
        spec=litterrobot.LitterRobotHub,
    )
    hub.coordinator.last_update_success = True
    hub.account.robots = [create_mock_robot(opp)]
    return hub


async def setup_hub(opp, mock_hub, platform_domain):
    """Load a Litter-Robot platform with the provided hub."""
    entry = MockConfigEntry(
        domain=litterrobot.DOMAIN,
        data=CONFIG[litterrobot.DOMAIN],
    )
    entry.add_to_opp(opp)

    with patch(
        "openpeerpower.components.litterrobot.LitterRobotHub",
        return_value=mock_hub,
    ):
        await opp.config_entries.async_forward_entry_setup(entry, platform_domain)
        await opp.async_block_till_done()
