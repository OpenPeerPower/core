"""Tests for color_extractor component service calls."""
import base64
import io
from unittest.mock import Mock, mock_open, patch

import aiohttp
import pytest
from voluptuous.error import MultipleInvalid

from openpeerpower.components.color_extractor import (
    ATTR_PATH,
    ATTR_URL,
    DOMAIN,
    SERVICE_TURN_ON,
)
from openpeerpower.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_BRIGHTNESS_PCT,
    ATTR_RGB_COLOR,
    DOMAIN as LIGHT_DOMAIN,
    SERVICE_TURN_OFF as LIGHT_SERVICE_TURN_OFF,
)
from openpeerpower.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON
from openpeerpower.setup import async_setup_component
import openpeerpower.util.color as color_util

from tests.common import load_fixture

LIGHT_ENTITY = "light.kitchen_lights"
CLOSE_THRESHOLD = 10


def _close_enough(actual_rgb, testing_rgb):
    """Validate the given RGB value is in acceptable tolerance."""
    # Convert the given RGB values to hue / saturation and then back again
    # as it wasn't reading the same RGB value set against it.
    actual_hs = color_util.color_RGB_to_hs(*actual_rgb)
    actual_rgb = color_util.color_hs_to_RGB(*actual_hs)

    testing_hs = color_util.color_RGB_to_hs(*testing_rgb)
    testing_rgb = color_util.color_hs_to_RGB(*testing_hs)

    actual_red, actual_green, actual_blue = actual_rgb
    testing_red, testing_green, testing_blue = testing_rgb

    r_diff = abs(actual_red - testing_red)
    g_diff = abs(actual_green - testing_green)
    b_diff = abs(actual_blue - testing_blue)

    return (
        r_diff <= CLOSE_THRESHOLD
        and g_diff <= CLOSE_THRESHOLD
        and b_diff <= CLOSE_THRESHOLD
    )


@pytest.fixture(autouse=True)
async def setup_light(opp):
    """Configure our light component to work against for testing."""
    assert await async_setup_component(
        opp, LIGHT_DOMAIN, {LIGHT_DOMAIN: {"platform": "demo"}}
    )
    await opp.async_block_till_done()

    state = opp.states.get(LIGHT_ENTITY)
    assert state

    # Validate starting values
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_BRIGHTNESS) == 180
    assert state.attributes.get(ATTR_RGB_COLOR) == (255, 63, 111)

    await opp.services.async_call(
        LIGHT_DOMAIN,
        LIGHT_SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: LIGHT_ENTITY},
        blocking=True,
    )
    await opp.async_block_till_done()

    state = opp.states.get(LIGHT_ENTITY)

    assert state
    assert state.state == STATE_OFF


async def test_missing_url_and_path(opp):
    """Test that nothing happens when url and path are missing."""
    # Load our color_extractor component
    await async_setup_component(
        opp,
        DOMAIN,
        {},
    )
    await opp.async_block_till_done()

    # Validate pre service call
    state = opp.states.get(LIGHT_ENTITY)
    assert state
    assert state.state == STATE_OFF

    # Missing url and path attributes, should cause error log
    service_data = {
        ATTR_ENTITY_ID: LIGHT_ENTITY,
    }

    with pytest.raises(MultipleInvalid):
        await opp.services.async_call(
            DOMAIN, SERVICE_TURN_ON, service_data, blocking=True
        )
        await opp.async_block_till_done()

    # check light is still off, unchanged due to bad parameters on service call
    state = opp.states.get(LIGHT_ENTITY)
    assert state
    assert state.state == STATE_OFF


async def _async_load_color_extractor_url(opp, service_data):
    # Load our color_extractor component
    await async_setup_component(
        opp,
        DOMAIN,
        {},
    )
    await opp.async_block_till_done()

    # Validate pre service call
    state = opp.states.get(LIGHT_ENTITY)
    assert state
    assert state.state == STATE_OFF

    # Call the shared service, our above mock should return the base64 decoded fixture 1x1 pixel
    assert await opp.services.async_call(
        DOMAIN, SERVICE_TURN_ON, service_data, blocking=True
    )

    await opp.async_block_till_done()


async def test_url_success(opp, aioclient_mock):
    """Test that a successful image GET translate to light RGB."""
    service_data = {
        ATTR_URL: "http://example.com/images/logo.png",
        ATTR_ENTITY_ID: LIGHT_ENTITY,
        # Standard light service data which we pass
        ATTR_BRIGHTNESS_PCT: 50,
    }

    # Mock the HTTP Response with a base64 encoded 1x1 pixel
    aioclient_mock.get(
        url=service_data[ATTR_URL],
        content=base64.b64decode(load_fixture("color_extractor_url.txt")),
    )

    # Allow access to this URL using the proper mechanism
    opp.config.allowlist_external_urls.add("http://example.com/images/")

    await _async_load_color_extractor_url(opp, service_data)

    state = opp.states.get(LIGHT_ENTITY)
    assert state

    # Ensure we turned it on
    assert state.state == STATE_ON

    # Brightness has changed, optional service call field
    assert state.attributes[ATTR_BRIGHTNESS] == 128

    # Ensure the RGB values are correct
    assert _close_enough(state.attributes[ATTR_RGB_COLOR], (50, 100, 150))


async def test_url_not_allowed(opp, aioclient_mock):
    """Test that a not allowed external URL fails to turn light on."""
    service_data = {
        ATTR_URL: "http://denied.com/images/logo.png",
        ATTR_ENTITY_ID: LIGHT_ENTITY,
    }

    await _async_load_color_extractor_url(opp, service_data)

    # Light has not been modified due to failure
    state = opp.states.get(LIGHT_ENTITY)
    assert state
    assert state.state == STATE_OFF


async def test_url_exception(opp, aioclient_mock):
    """Test that a HTTPError fails to turn light on."""
    service_data = {
        ATTR_URL: "http://example.com/images/logo.png",
        ATTR_ENTITY_ID: LIGHT_ENTITY,
    }

    # Don't let the URL not being allowed sway our exception test
    opp.config.allowlist_external_urls.add("http://example.com/images/")

    # Mock the HTTP Response with an HTTPError
    aioclient_mock.get(url=service_data[ATTR_URL], exc=aiohttp.ClientError)

    await _async_load_color_extractor_url(opp, service_data)

    # Light has not been modified due to failure
    state = opp.states.get(LIGHT_ENTITY)
    assert state
    assert state.state == STATE_OFF


async def test_url_error(opp, aioclient_mock):
    """Test that a HTTP Error (non 200) doesn't turn light on."""
    service_data = {
        ATTR_URL: "http://example.com/images/logo.png",
        ATTR_ENTITY_ID: LIGHT_ENTITY,
    }

    # Don't let the URL not being allowed sway our exception test
    opp.config.allowlist_external_urls.add("http://example.com/images/")

    # Mock the HTTP Response with a 400 Bad Request error
    aioclient_mock.get(url=service_data[ATTR_URL], status=400)

    await _async_load_color_extractor_url(opp, service_data)

    # Light has not been modified due to failure
    state = opp.states.get(LIGHT_ENTITY)
    assert state
    assert state.state == STATE_OFF


@patch(
    "builtins.open",
    mock_open(read_data=base64.b64decode(load_fixture("color_extractor_file.txt"))),
    create=True,
)
def _get_file_mock(file_path):
    """Convert file to BytesIO for testing due to PIL UnidentifiedImageError."""
    _file = None

    with open(file_path) as file_handler:
        _file = io.BytesIO(file_handler.read())

    _file.name = "color_extractor.jpg"
    _file.seek(0)

    return _file


@patch("os.path.isfile", Mock(return_value=True))
@patch("os.access", Mock(return_value=True))
async def test_file(opp):
    """Test that the file only service reads a file and translates to light RGB."""
    service_data = {
        ATTR_PATH: "/opt/image.png",
        ATTR_ENTITY_ID: LIGHT_ENTITY,
        # Standard light service data which we pass
        ATTR_BRIGHTNESS_PCT: 100,
    }

    # Add our /opt/ path to the allowed list of paths
    opp.config.allowlist_external_dirs.add("/opt/")

    await async_setup_component(opp, DOMAIN, {})
    await opp.async_block_till_done()

    # Verify pre service check
    state = opp.states.get(LIGHT_ENTITY)
    assert state
    assert state.state == STATE_OFF

    # Mock the file handler read with our 1x1 base64 encoded fixture image
    with patch("openpeerpower.components.color_extractor._get_file", _get_file_mock):
        await opp.services.async_call(DOMAIN, SERVICE_TURN_ON, service_data)
        await opp.async_block_till_done()

    state = opp.states.get(LIGHT_ENTITY)

    assert state

    # Ensure we turned it on
    assert state.state == STATE_ON

    # And set the brightness
    assert state.attributes[ATTR_BRIGHTNESS] == 255

    # Ensure the RGB values are correct
    assert _close_enough(state.attributes[ATTR_RGB_COLOR], (25, 75, 125))


@patch("os.path.isfile", Mock(return_value=True))
@patch("os.access", Mock(return_value=True))
async def test_file_denied_dir(opp):
    """Test that the file only service fails to read an image in a dir not explicitly allowed."""
    service_data = {
        ATTR_PATH: "/path/to/a/dir/not/allowed/image.png",
        ATTR_ENTITY_ID: LIGHT_ENTITY,
        # Standard light service data which we pass
        ATTR_BRIGHTNESS_PCT: 100,
    }

    await async_setup_component(opp, DOMAIN, {})
    await opp.async_block_till_done()

    # Verify pre service check
    state = opp.states.get(LIGHT_ENTITY)
    assert state
    assert state.state == STATE_OFF

    # Mock the file handler read with our 1x1 base64 encoded fixture image
    with patch("openpeerpower.components.color_extractor._get_file", _get_file_mock):
        await opp.services.async_call(DOMAIN, SERVICE_TURN_ON, service_data)
        await opp.async_block_till_done()

    state = opp.states.get(LIGHT_ENTITY)

    assert state

    # Ensure it's still off due to access error (dir not explicitly allowed)
    assert state.state == STATE_OFF
