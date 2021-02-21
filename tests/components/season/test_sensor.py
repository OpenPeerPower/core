"""The tests for the Season sensor platform."""
from datetime import datetime
from unittest.mock import patch

import pytest

from openpeerpower.components.season.sensor import (
    STATE_AUTUMN,
    STATE_SPRING,
    STATE_SUMMER,
    STATE_WINTER,
    TYPE_ASTRONOMICAL,
    TYPE_METEOROLOGICAL,
)
from openpeerpower.const import STATE_UNKNOWN
from openpeerpowerr.setup import async_setup_component

HEMISPHERE_NORTHERN = {
    "openpeerpowerr": {"latitude": "48.864716", "longitude": "2.349014"},
    "sensor": {"platform": "season", "type": "astronomical"},
}

HEMISPHERE_SOUTHERN = {
    "openpeerpowerr": {"latitude": "-33.918861", "longitude": "18.423300"},
    "sensor": {"platform": "season", "type": "astronomical"},
}

HEMISPHERE_EQUATOR = {
    "openpeerpowerr": {"latitude": "0", "longitude": "-51.065100"},
    "sensor": {"platform": "season", "type": "astronomical"},
}

HEMISPHERE_EMPTY = {
    "openpeerpowerr": {},
    "sensor": {"platform": "season", "type": "meteorological"},
}

NORTHERN_PARAMETERS = [
    (TYPE_ASTRONOMICAL, datetime(2017, 9, 3, 0, 0), STATE_SUMMER),
    (TYPE_METEOROLOGICAL, datetime(2017, 8, 13, 0, 0), STATE_SUMMER),
    (TYPE_ASTRONOMICAL, datetime(2017, 9, 23, 0, 0), STATE_AUTUMN),
    (TYPE_METEOROLOGICAL, datetime(2017, 9, 3, 0, 0), STATE_AUTUMN),
    (TYPE_ASTRONOMICAL, datetime(2017, 12, 25, 0, 0), STATE_WINTER),
    (TYPE_METEOROLOGICAL, datetime(2017, 12, 3, 0, 0), STATE_WINTER),
    (TYPE_ASTRONOMICAL, datetime(2017, 4, 1, 0, 0), STATE_SPRING),
    (TYPE_METEOROLOGICAL, datetime(2017, 3, 3, 0, 0), STATE_SPRING),
]

SOUTHERN_PARAMETERS = [
    (TYPE_ASTRONOMICAL, datetime(2017, 12, 25, 0, 0), STATE_SUMMER),
    (TYPE_METEOROLOGICAL, datetime(2017, 12, 3, 0, 0), STATE_SUMMER),
    (TYPE_ASTRONOMICAL, datetime(2017, 4, 1, 0, 0), STATE_AUTUMN),
    (TYPE_METEOROLOGICAL, datetime(2017, 3, 3, 0, 0), STATE_AUTUMN),
    (TYPE_ASTRONOMICAL, datetime(2017, 9, 3, 0, 0), STATE_WINTER),
    (TYPE_METEOROLOGICAL, datetime(2017, 8, 13, 0, 0), STATE_WINTER),
    (TYPE_ASTRONOMICAL, datetime(2017, 9, 23, 0, 0), STATE_SPRING),
    (TYPE_METEOROLOGICAL, datetime(2017, 9, 3, 0, 0), STATE_SPRING),
]


def idfn(val):
    """Provide IDs for pytest parametrize."""
    if isinstance(val, (datetime)):
        return val.strftime("%Y%m%d")


@pytest.mark.parametrize("type,day,expected", NORTHERN_PARAMETERS, ids=idfn)
async def test_season_northern_hemisphere.opp, type, day, expected):
    """Test that season should be summer."""
   .opp.config.latitude = HEMISPHERE_NORTHERN["openpeerpowerr"]["latitude"]

    config = {
        **HEMISPHERE_NORTHERN,
        "sensor": {"platform": "season", "type": type},
    }

    with patch("openpeerpower.components.season.sensor.utcnow", return_value=day):
        assert await async_setup_component.opp, "sensor", config)
        await.opp.async_block_till_done()

    state = opp.states.get("sensor.season")
    assert state
    assert state.state == expected


@pytest.mark.parametrize("type,day,expected", SOUTHERN_PARAMETERS, ids=idfn)
async def test_season_southern_hemisphere.opp, type, day, expected):
    """Test that season should be summer."""
   .opp.config.latitude = HEMISPHERE_SOUTHERN["openpeerpowerr"]["latitude"]

    config = {
        **HEMISPHERE_SOUTHERN,
        "sensor": {"platform": "season", "type": type},
    }

    with patch("openpeerpower.components.season.sensor.utcnow", return_value=day):
        assert await async_setup_component.opp, "sensor", config)
        await.opp.async_block_till_done()

    state = opp.states.get("sensor.season")
    assert state
    assert state.state == expected


async def test_season_equator.opp):
    """Test that season should be unknown for equator."""
   .opp.config.latitude = HEMISPHERE_EQUATOR["openpeerpowerr"]["latitude"]
    day = datetime(2017, 9, 3, 0, 0)

    with patch("openpeerpower.components.season.sensor.utcnow", return_value=day):
        assert await async_setup_component.opp, "sensor", HEMISPHERE_EQUATOR)
        await.opp.async_block_till_done()

    state = opp.states.get("sensor.season")
    assert state
    assert state.state == STATE_UNKNOWN


async def test_setup_hemisphere_empty.opp):
    """Test platform setup of missing latlong."""
   .opp.config.latitude = None
    assert await async_setup_component.opp, "sensor", HEMISPHERE_EMPTY)
    await.opp.async_block_till_done()
    assert.opp.config.as_dict()["latitude"] is None
