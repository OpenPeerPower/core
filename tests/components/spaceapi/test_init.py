"""The tests for the Open Peer Power SpaceAPI component."""
# pylint: disable=protected-access
from unittest.mock import patch

import pytest

from openpeerpower.components.spaceapi import DOMAIN, SPACEAPI_VERSION, URL_API_SPACEAPI
from openpeerpower.const import ATTR_UNIT_OF_MEASUREMENT, PERCENTAGE, TEMP_CELSIUS
from openpeerpower.setup import async_setup_component

from tests.common import mock_coro

CONFIG = {
    DOMAIN: {
        "space": "Home",
        "logo": "https://open-peer-power.io/logo.png",
        "url": "https://open-peer-power.io",
        "location": {"address": "In your Home"},
        "contact": {"email": "hello@open-peer-power.io"},
        "issue_report_channels": ["email"],
        "state": {
            "entity_id": "test.test_door",
            "icon_open": "https://open-peer-power.io/open.png",
            "icon_closed": "https://open-peer-power.io/close.png",
        },
        "sensors": {
            "temperature": ["test.temp1", "test.temp2"],
            "humidity": ["test.hum1"],
        },
        "spacefed": {"spacenet": True, "spacesaml": False, "spacephone": True},
        "cam": ["https://open-peer-power.io/cam1", "https://open-peer-power.io/cam2"],
        "stream": {
            "m4": "https://open-peer-power.io/m4",
            "mjpeg": "https://open-peer-power.io/mjpeg",
            "ustream": "https://open-peer-power.io/ustream",
        },
        "feeds": {
            "blog": {"url": "https://open-peer-power.io/blog"},
            "wiki": {"type": "mediawiki", "url": "https://open-peer-power.io/wiki"},
            "calendar": {"type": "ical", "url": "https://open-peer-power.io/calendar"},
            "flicker": {"url": "https://www.flickr.com/photos/open-peer-power"},
        },
        "cache": {"schedule": "m.02"},
        "projects": [
            "https://open-peer-power.io/projects/1",
            "https://open-peer-power.io/projects/2",
            "https://open-peer-power.io/projects/3",
        ],
        "radio_show": [
            {
                "name": "Radioshow",
                "url": "https://open-peer-power.io/radio",
                "type": "ogg",
                "start": "2019-09-02T10:00Z",
                "end": "2019-09-02T12:00Z",
            }
        ],
    }
}

SENSOR_OUTPUT = {
    "temperature": [
        {"location": "Home", "name": "temp1", "unit": TEMP_CELSIUS, "value": "25"},
        {"location": "Home", "name": "temp2", "unit": TEMP_CELSIUS, "value": "23"},
    ],
    "humidity": [
        {"location": "Home", "name": "hum1", "unit": PERCENTAGE, "value": "88"}
    ],
}


@pytest.fixture
def mock_client(opp, opp_client):
    """Start the Open Peer Power HTTP component."""
    with patch("openpeerpower.components.spaceapi", return_value=mock_coro(True)):
        opp.loop.run_until_complete(async_setup_component(opp, "spaceapi", CONFIG))

    opp.states.async_set(
        "test.temp1", 25, attributes={ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS}
    )
    opp.states.async_set(
        "test.temp2", 23, attributes={ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS}
    )
    opp.states.async_set(
        "test.hum1", 88, attributes={ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE}
    )

    return opp.loop.run_until_complete.opp_client())


async def test_spaceapi_get(opp, mock_client):
    """Test response after start-up Open Peer Power."""
    resp = await mock_client.get(URL_API_SPACEAPI)
    assert resp.status == 200

    data = await resp.json()

    assert data["api"] == SPACEAPI_VERSION
    assert data["space"] == "Home"
    assert data["contact"]["email"] == "hello@open-peer-power.io"
    assert data["location"]["address"] == "In your Home"
    assert data["location"]["lat"] == 32.87336
    assert data["location"]["lon"] == -117.22743
    assert data["state"]["open"] == "null"
    assert data["state"]["icon"]["open"] == "https://open-peer-power.io/open.png"
    assert data["state"]["icon"]["close"] == "https://open-peer-power.io/close.png"
    assert data["spacefed"]["spacenet"] == bool(1)
    assert data["spacefed"]["spacesaml"] == bool(0)
    assert data["spacefed"]["spacephone"] == bool(1)
    assert data["cam"][0] == "https://open-peer-power.io/cam1"
    assert data["cam"][1] == "https://open-peer-power.io/cam2"
    assert data["stream"]["m4"] == "https://open-peer-power.io/m4"
    assert data["stream"]["mjpeg"] == "https://open-peer-power.io/mjpeg"
    assert data["stream"]["ustream"] == "https://open-peer-power.io/ustream"
    assert data["feeds"]["blog"]["url"] == "https://open-peer-power.io/blog"
    assert data["feeds"]["wiki"]["type"] == "mediawiki"
    assert data["feeds"]["wiki"]["url"] == "https://open-peer-power.io/wiki"
    assert data["feeds"]["calendar"]["type"] == "ical"
    assert data["feeds"]["calendar"]["url"] == "https://open-peer-power.io/calendar"
    assert (
        data["feeds"]["flicker"]["url"]
        == "https://www.flickr.com/photos/open-peer-power"
    )
    assert data["cache"]["schedule"] == "m.02"
    assert data["projects"][0] == "https://open-peer-power.io/projects/1"
    assert data["projects"][1] == "https://open-peer-power.io/projects/2"
    assert data["projects"][2] == "https://open-peer-power.io/projects/3"
    assert data["radio_show"][0]["name"] == "Radioshow"
    assert data["radio_show"][0]["url"] == "https://open-peer-power.io/radio"
    assert data["radio_show"][0]["type"] == "ogg"
    assert data["radio_show"][0]["start"] == "2019-09-02T10:00Z"
    assert data["radio_show"][0]["end"] == "2019-09-02T12:00Z"


async def test_spaceapi_state_get(opp, mock_client):
    """Test response if the state entity was set."""
    opp.states.async_set("test.test_door", True)

    resp = await mock_client.get(URL_API_SPACEAPI)
    assert resp.status == 200

    data = await resp.json()
    assert data["state"]["open"] == bool(1)


async def test_spaceapi_sensors_get(opp, mock_client):
    """Test the response for the sensors."""
    resp = await mock_client.get(URL_API_SPACEAPI)
    assert resp.status == 200

    data = await resp.json()
    assert data["sensors"] == SENSOR_OUTPUT
