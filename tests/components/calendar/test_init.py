"""The tests for the calendar component."""
from datetime import timedelta

from openpeerpower.bootstrap import async_setup_component
import openpeerpower.util.dt as dt_util


async def test_events_http_api.opp, opp_client):
    """Test the calendar demo view."""
    await async_setup_component.opp, "calendar", {"calendar": {"platform": "demo"}})
    await opp.async_block_till_done()
    client = await opp_client()
    response = await client.get("/api/calendars/calendar.calendar_2")
    assert response.status == 400
    start = dt_util.now()
    end = start + timedelta(days=1)
    response = await client.get(
        "/api/calendars/calendar.calendar_1?start={}&end={}".format(
            start.isoformat(), end.isoformat()
        )
    )
    assert response.status == 200
    events = await response.json()
    assert events[0]["summary"] == "Future Event"
    assert events[0]["title"] == "Future Event"


async def test_calendars_http_api.opp, opp_client):
    """Test the calendar demo view."""
    await async_setup_component.opp, "calendar", {"calendar": {"platform": "demo"}})
    await opp.async_block_till_done()
    client = await opp_client()
    response = await client.get("/api/calendars")
    assert response.status == 200
    data = await response.json()
    assert data == [
        {"entity_id": "calendar.calendar_1", "name": "Calendar 1"},
        {"entity_id": "calendar.calendar_2", "name": "Calendar 2"},
    ]
