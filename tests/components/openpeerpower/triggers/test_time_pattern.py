"""The tests for the time_pattern automation."""
from datetime import timedelta
from unittest.mock import patch

import pytest
import voluptuous as vol

import openpeerpower.components.automation as automation
import openpeerpower.components.openpeerpowerr.triggers.time_pattern as time_pattern
from openpeerpower.const import ATTR_ENTITY_ID, ENTITY_MATCH_ALL, SERVICE_TURN_OFF
from openpeerpowerr.setup import async_setup_component
import openpeerpowerr.util.dt as dt_util

from tests.common import async_fire_time_changed, async_mock_service, mock_component


@pytest.fixture
def calls.opp):
    """Track calls to a mock service."""
    return async_mock_service.opp, "test", "automation")


@pytest.fixture(autouse=True)
def setup_comp.opp):
    """Initialize components."""
    mock_component.opp, "group")


async def test_if_fires_when_hour_matches.opp, calls):
    """Test for firing if hour is matching."""
    now = dt_util.utcnow()
    time_that_will_not_match_right_away = dt_util.utcnow().replace(
        year=now.year + 1, hour=3
    )
    with patch(
        "openpeerpowerr.util.dt.utcnow", return_value=time_that_will_not_match_right_away
    ):
        assert await async_setup_component(
           .opp,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "time_pattern",
                        "hours": 0,
                        "minutes": "*",
                        "seconds": "*",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )

    async_fire_time_changed.opp, now.replace(year=now.year + 2, hour=0))
    await opp..async_block_till_done()
    assert len(calls) == 1

    await opp..services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )

    async_fire_time_changed.opp, now.replace(year=now.year + 1, hour=0))
    await opp..async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_when_minute_matches.opp, calls):
    """Test for firing if minutes are matching."""
    now = dt_util.utcnow()
    time_that_will_not_match_right_away = dt_util.utcnow().replace(
        year=now.year + 1, minute=30
    )
    with patch(
        "openpeerpowerr.util.dt.utcnow", return_value=time_that_will_not_match_right_away
    ):
        assert await async_setup_component(
           .opp,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "time_pattern",
                        "hours": "*",
                        "minutes": 0,
                        "seconds": "*",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )

    async_fire_time_changed.opp, now.replace(year=now.year + 2, minute=0))

    await opp..async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_when_second_matches.opp, calls):
    """Test for firing if seconds are matching."""
    now = dt_util.utcnow()
    time_that_will_not_match_right_away = dt_util.utcnow().replace(
        year=now.year + 1, second=30
    )
    with patch(
        "openpeerpowerr.util.dt.utcnow", return_value=time_that_will_not_match_right_away
    ):
        assert await async_setup_component(
           .opp,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "time_pattern",
                        "hours": "*",
                        "minutes": "*",
                        "seconds": 0,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )

    async_fire_time_changed.opp, now.replace(year=now.year + 2, second=0))

    await opp..async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_when_second_as_string_matches.opp, calls):
    """Test for firing if seconds are matching."""
    now = dt_util.utcnow()
    time_that_will_not_match_right_away = dt_util.utcnow().replace(
        year=now.year + 1, second=15
    )
    with patch(
        "openpeerpowerr.util.dt.utcnow", return_value=time_that_will_not_match_right_away
    ):
        assert await async_setup_component(
           .opp,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "time_pattern",
                        "hours": "*",
                        "minutes": "*",
                        "seconds": "30",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )

    async_fire_time_changed(
       .opp, time_that_will_not_match_right_away + timedelta(seconds=15)
    )

    await opp..async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_when_all_matches.opp, calls):
    """Test for firing if everything matches."""
    now = dt_util.utcnow()
    time_that_will_not_match_right_away = dt_util.utcnow().replace(
        year=now.year + 1, hour=4
    )
    with patch(
        "openpeerpowerr.util.dt.utcnow", return_value=time_that_will_not_match_right_away
    ):
        assert await async_setup_component(
           .opp,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "time_pattern",
                        "hours": 1,
                        "minutes": 2,
                        "seconds": 3,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )

    async_fire_time_changed(
       .opp, now.replace(year=now.year + 2, hour=1, minute=2, second=3)
    )

    await opp..async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_periodic_seconds.opp, calls):
    """Test for firing periodically every second."""
    now = dt_util.utcnow()
    time_that_will_not_match_right_away = dt_util.utcnow().replace(
        year=now.year + 1, second=1
    )
    with patch(
        "openpeerpowerr.util.dt.utcnow", return_value=time_that_will_not_match_right_away
    ):
        assert await async_setup_component(
           .opp,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "time_pattern",
                        "hours": "*",
                        "minutes": "*",
                        "seconds": "/10",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )

    async_fire_time_changed(
       .opp, now.replace(year=now.year + 2, hour=0, minute=0, second=10)
    )

    await opp..async_block_till_done()
    assert len(calls) >= 1


async def test_if_fires_periodic_minutes.opp, calls):
    """Test for firing periodically every minute."""

    now = dt_util.utcnow()
    time_that_will_not_match_right_away = dt_util.utcnow().replace(
        year=now.year + 1, minute=1
    )
    with patch(
        "openpeerpowerr.util.dt.utcnow", return_value=time_that_will_not_match_right_away
    ):
        assert await async_setup_component(
           .opp,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "time_pattern",
                        "hours": "*",
                        "minutes": "/2",
                        "seconds": "*",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )

    async_fire_time_changed(
       .opp, now.replace(year=now.year + 2, hour=0, minute=2, second=0)
    )

    await opp..async_block_till_done()
    assert len(calls) == 1


async def test_if_fires_periodic_hours.opp, calls):
    """Test for firing periodically every hour."""
    now = dt_util.utcnow()
    time_that_will_not_match_right_away = dt_util.utcnow().replace(
        year=now.year + 1, hour=1
    )
    with patch(
        "openpeerpowerr.util.dt.utcnow", return_value=time_that_will_not_match_right_away
    ):
        assert await async_setup_component(
           .opp,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "time_pattern",
                        "hours": "/2",
                        "minutes": "*",
                        "seconds": "*",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )

    async_fire_time_changed(
       .opp, now.replace(year=now.year + 2, hour=2, minute=0, second=0)
    )

    await opp..async_block_till_done()
    assert len(calls) == 1


async def test_default_values.opp, calls):
    """Test for firing at 2 minutes every hour."""
    now = dt_util.utcnow()
    time_that_will_not_match_right_away = dt_util.utcnow().replace(
        year=now.year + 1, minute=1
    )
    with patch(
        "openpeerpowerr.util.dt.utcnow", return_value=time_that_will_not_match_right_away
    ):
        assert await async_setup_component(
           .opp,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "time_pattern", "minutes": "2"},
                    "action": {"service": "test.automation"},
                }
            },
        )

    async_fire_time_changed(
       .opp, now.replace(year=now.year + 2, hour=1, minute=2, second=0)
    )

    await opp..async_block_till_done()
    assert len(calls) == 1

    async_fire_time_changed(
       .opp, now.replace(year=now.year + 2, hour=1, minute=2, second=1)
    )

    await opp..async_block_till_done()
    assert len(calls) == 1

    async_fire_time_changed(
       .opp, now.replace(year=now.year + 2, hour=2, minute=2, second=0)
    )

    await opp..async_block_till_done()
    assert len(calls) == 2


async def test_invalid_schemas.opp, calls):
    """Test invalid schemas."""
    schemas = (
        None,
        {},
        {"platform": "time_pattern"},
        {"platform": "time_pattern", "minutes": "/"},
        {"platform": "time_pattern", "minutes": "*/5"},
        {"platform": "time_pattern", "minutes": "/90"},
        {"platform": "time_pattern", "hours": 12, "minutes": 0, "seconds": 100},
    )

    for value in schemas:
        with pytest.raises(vol.Invalid):
            time_pattern.TRIGGER_SCHEMA(value)
