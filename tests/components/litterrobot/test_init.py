"""Test Litter-Robot setup process."""
from unittest.mock import patch

from pylitterbot.exceptions import LitterRobotException, LitterRobotLoginException
import pytest

from openpeerpower.components import litterrobot
from openpeerpower.components.vacuum import (
    DOMAIN as VACUUM_DOMAIN,
    SERVICE_START,
    STATE_DOCKED,
)
from openpeerpower.config_entries import ConfigEntryState
from openpeerpower.const import ATTR_ENTITY_ID

from .common import CONFIG, VACUUM_ENTITY_ID
from .conftest import setup_integration

from tests.common import MockConfigEntry


async def test_unload_entry(opp, mock_account):
    """Test being able to unload an entry."""
    entry = await setup_integration(opp, mock_account, VACUUM_DOMAIN)

    vacuum = opp.states.get(VACUUM_ENTITY_ID)
    assert vacuum
    assert vacuum.state == STATE_DOCKED

    await opp.services.async_call(
        VACUUM_DOMAIN,
        SERVICE_START,
        {ATTR_ENTITY_ID: VACUUM_ENTITY_ID},
        blocking=True,
    )
    getattr(mock_account.robots[0], "start_cleaning").assert_called_once()

    assert await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()
    assert opp.data[litterrobot.DOMAIN] == {}


@pytest.mark.parametrize(
    "side_effect,expected_state",
    (
        (LitterRobotLoginException, ConfigEntryState.SETUP_ERROR),
        (LitterRobotException, ConfigEntryState.SETUP_RETRY),
    ),
)
async def test_entry_not_setup(opp, side_effect, expected_state):
    """Test being able to handle config entry not setup."""
    entry = MockConfigEntry(
        domain=litterrobot.DOMAIN,
        data=CONFIG[litterrobot.DOMAIN],
    )
    entry.add_to_opp(opp)

    with patch(
        "pylitterbot.Account.connect",
        side_effect=side_effect,
    ):
        await opp.config_entries.async_setup(entry.entry_id)
        assert entry.state is expected_state
