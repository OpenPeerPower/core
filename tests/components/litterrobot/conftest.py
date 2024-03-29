"""Configure pytest for Litter-Robot tests."""
from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from pylitterbot import Account, Robot
from pylitterbot.exceptions import InvalidCommandException
import pytest

from openpeerpower.components import litterrobot
from openpeerpower.core import OpenPeerPower

from .common import CONFIG, ROBOT_DATA

from tests.common import MockConfigEntry


def create_mock_robot(
    robot_data: Optional[dict] = None, side_effect: Optional[Any] = None
) -> Robot:
    """Create a mock Litter-Robot device."""
    if not robot_data:
        robot_data = {}

    robot = Robot(data={**ROBOT_DATA, **robot_data})
    robot.start_cleaning = AsyncMock(side_effect=side_effect)
    robot.set_power_status = AsyncMock(side_effect=side_effect)
    robot.reset_waste_drawer = AsyncMock(side_effect=side_effect)
    robot.set_sleep_mode = AsyncMock(side_effect=side_effect)
    robot.set_night_light = AsyncMock(side_effect=side_effect)
    robot.set_panel_lockout = AsyncMock(side_effect=side_effect)
    robot.set_wait_time = AsyncMock(side_effect=side_effect)
    return robot


def create_mock_account(
    robot_data: Optional[dict] = None,
    side_effect: Optional[Any] = None,
    skip_robots: bool = False,
) -> MagicMock:
    """Create a mock Litter-Robot account."""
    account = MagicMock(spec=Account)
    account.connect = AsyncMock()
    account.refresh_robots = AsyncMock()
    account.robots = [] if skip_robots else [create_mock_robot(robot_data, side_effect)]
    return account


@pytest.fixture
def mock_account() -> MagicMock:
    """Mock a Litter-Robot account."""
    return create_mock_account()


@pytest.fixture
def mock_account_with_no_robots() -> MagicMock:
    """Mock a Litter-Robot account."""
    return create_mock_account(skip_robots=True)


@pytest.fixture
def mock_account_with_error() -> MagicMock:
    """Mock a Litter-Robot account with error."""
    return create_mock_account({"unitStatus": "BR"})


@pytest.fixture
def mock_account_with_side_effects() -> MagicMock:
    """Mock a Litter-Robot account with side effects."""
    return create_mock_account(
        side_effect=InvalidCommandException("Invalid command: oops")
    )


async def setup_integration(
    opp: OpenPeerPower, mock_account: MagicMock, platform_domain: Optional[str] = None
) -> MockConfigEntry:
    """Load a Litter-Robot platform with the provided hub."""
    entry = MockConfigEntry(
        domain=litterrobot.DOMAIN,
        data=CONFIG[litterrobot.DOMAIN],
    )
    entry.add_to_opp(opp)

    with patch(
        "openpeerpower.components.litterrobot.hub.Account", return_value=mock_account
    ), patch(
        "openpeerpower.components.litterrobot.PLATFORMS",
        [platform_domain] if platform_domain else [],
    ):
        await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()

    return entry
