"""The tests for the Google Calendar component."""
from unittest.mock import patch

import pytest

import openpeerpower.components.google as google
from openpeerpower.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from openpeerpower.setup import async_setup_component


@pytest.fixture(name="google_setup")
def mock_google_setup_opp):
    """Mock the google set up functions."""
    p_auth = patch(
        "openpeerpower.components.google.do_authentication", side_effect=google.do_setup
    )
    p_service = patch("openpeerpower.components.google.GoogleCalendarService.get")
    p_discovery = patch("openpeerpower.components.google.discovery.load_platform")
    p_load = patch("openpeerpower.components.google.load_config", return_value={})
    p_save = patch("openpeerpower.components.google.update_config")

    with p_auth, p_load, p_service, p_discovery, p_save:
        yield


async def test_setup_component.opp, google_setup):
    """Test setup component."""
    config = {"google": {CONF_CLIENT_ID: "id", CONF_CLIENT_SECRET: "secret"}}

    assert await async_setup_component.opp, "google", config)


async def test_get_calendar_info.opp, test_calendar):
    """Test getting the calendar info."""
    calendar_info = await.opp.async_add_executor_job(
        google.get_calendar_info,.opp, test_calendar
    )
    assert calendar_info == {
        "cal_id": "qwertyuiopasdfghjklzxcvbnm@import.calendar.google.com",
        "entities": [
            {
                "device_id": "we_are_we_are_a_test_calendar",
                "name": "We are, we are, a... Test Calendar",
                "track": True,
                "ignore_availability": True,
            }
        ],
    }


async def test_found_calendar.opp, google_setup, mock_next_event, test_calendar):
    """Test when a calendar is found."""
    config = {
        "google": {
            CONF_CLIENT_ID: "id",
            CONF_CLIENT_SECRET: "secret",
            "track_new_calendar": True,
        }
    }
    assert await async_setup_component.opp, "google", config)
    assert.opp.data[google.DATA_INDEX] == {}

    await.opp.services.async_call(
        "google", google.SERVICE_FOUND_CALENDARS, test_calendar, blocking=True
    )

    assert.opp.data[google.DATA_INDEX].get(test_calendar["id"]) is not None
