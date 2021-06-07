"""Test the SmartTub binary sensor platform."""
from datetime import datetime
from unittest.mock import create_autospec

import pytest
import smarttub

from openpeerpower.components.binary_sensor import STATE_OFF, STATE_ON


async def test_binary_sensors(spa, setup_entry, opp):
    """Test simple binary sensors."""

    entity_id = f"binary_sensor.{spa.brand}_{spa.model}_online"
    state = opp.states.get(entity_id)
    # disabled by default
    assert state is None

    entity_id = f"binary_sensor.{spa.brand}_{spa.model}_error"
    state = opp.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_OFF


async def test_reminders(spa, setup_entry, opp):
    """Test the reminder sensor."""

    entity_id = f"binary_sensor.{spa.brand}_{spa.model}_myfilter_reminder"
    state = opp.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_OFF
    assert state.attributes["snoozed"] is False


@pytest.fixture
def mock_error(spa):
    """Mock error."""
    error = create_autospec(smarttub.SpaError, instance=True)
    error.code = 11
    error.title = "Flow Switch Stuck Open"
    error.description = None
    error.active = True
    error.created_at = datetime.now()
    error.updated_at = datetime.now()
    error.error_type = "TUB_ERROR"
    return error


async def test_error(spa, opp, config_entry, mock_error):
    """Test the error sensor."""

    spa.get_errors.return_value = [mock_error]

    config_entry.add_to_opp(opp)
    await opp.config_entries.async_setup(config_entry.entry_id)
    await opp.async_block_till_done()

    entity_id = f"binary_sensor.{spa.brand}_{spa.model}_error"
    state = opp.states.get(entity_id)
    assert state is not None

    assert state.state == STATE_ON
    assert state.attributes["error_code"] == 11


async def test_snooze(spa, setup_entry, opp):
    """Test snoozing a reminder."""

    entity_id = f"binary_sensor.{spa.brand}_{spa.model}_myfilter_reminder"
    reminder = spa.get_reminders.return_value[0]
    days = 30

    await opp.services.async_call(
        "smarttub",
        "snooze_reminder",
        {
            "entity_id": entity_id,
            "days": 30,
        },
        blocking=True,
    )

    reminder.snooze.assert_called_with(days)
