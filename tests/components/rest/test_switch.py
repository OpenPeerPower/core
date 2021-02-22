"""The tests for the REST switch platform."""
import asyncio

import aiohttp

from openpeerpower.components.rest import DOMAIN
import openpeerpower.components.rest.switch as rest
from openpeerpower.components.switch import DOMAIN as SWITCH_DOMAIN
from openpeerpower.const import (
    CONF_HEADERS,
    CONF_NAME,
    CONF_PARAMS,
    CONF_PLATFORM,
    CONF_RESOURCE,
    CONTENT_TYPE_JSON,
    HTTP_INTERNAL_SERVER_ERROR,
    HTTP_NOT_FOUND,
    HTTP_OK,
)
from openpeerpower.helpers.template import Template
from openpeerpower.setup import async_setup_component

from tests.common import assert_setup_component

"""Tests for setting up the REST switch platform."""

NAME = "foo"
METHOD = "post"
RESOURCE = "http://localhost/"
STATE_RESOURCE = RESOURCE
HEADERS = {"Content-type": CONTENT_TYPE_JSON}
AUTH = None
PARAMS = None


async def test_setup_missing_config.opp):
    """Test setup with configuration missing required entries."""
    assert not await rest.async_setup_platform.opp, {CONF_PLATFORM: DOMAIN}, None)


async def test_setup_missing_schema.opp):
    """Test setup with resource missing schema."""
    assert not await rest.async_setup_platform(
       .opp,
        {CONF_PLATFORM: DOMAIN, CONF_RESOURCE: "localhost"},
        None,
    )


async def test_setup_failed_connect.opp, aioclient_mock):
    """Test setup when connection error occurs."""
    aioclient_mock.get("http://localhost", exc=aiohttp.ClientError)
    assert not await rest.async_setup_platform(
       .opp,
        {CONF_PLATFORM: DOMAIN, CONF_RESOURCE: "http://localhost"},
        None,
    )


async def test_setup_timeout.opp, aioclient_mock):
    """Test setup when connection timeout occurs."""
    aioclient_mock.get("http://localhost", exc=asyncio.TimeoutError())
    assert not await rest.async_setup_platform(
       .opp,
        {CONF_PLATFORM: DOMAIN, CONF_RESOURCE: "http://localhost"},
        None,
    )


async def test_setup_minimum.opp, aioclient_mock):
    """Test setup with minimum configuration."""
    aioclient_mock.get("http://localhost", status=HTTP_OK)
    with assert_setup_component(1, SWITCH_DOMAIN):
        assert await async_setup_component(
           .opp,
            SWITCH_DOMAIN,
            {
                SWITCH_DOMAIN: {
                    CONF_PLATFORM: DOMAIN,
                    CONF_RESOURCE: "http://localhost",
                }
            },
        )
        await.opp.async_block_till_done()
    assert aioclient_mock.call_count == 1


async def test_setup_query_params.opp, aioclient_mock):
    """Test setup with query params."""
    aioclient_mock.get("http://localhost/?search=something", status=HTTP_OK)
    with assert_setup_component(1, SWITCH_DOMAIN):
        assert await async_setup_component(
           .opp,
            SWITCH_DOMAIN,
            {
                SWITCH_DOMAIN: {
                    CONF_PLATFORM: DOMAIN,
                    CONF_RESOURCE: "http://localhost",
                    CONF_PARAMS: {"search": "something"},
                }
            },
        )
        await.opp.async_block_till_done()

    print(aioclient_mock)
    assert aioclient_mock.call_count == 1


async def test_setup_opp, aioclient_mock):
    """Test setup with valid configuration."""
    aioclient_mock.get("http://localhost", status=HTTP_OK)
    assert await async_setup_component(
       .opp,
        SWITCH_DOMAIN,
        {
            SWITCH_DOMAIN: {
                CONF_PLATFORM: DOMAIN,
                CONF_NAME: "foo",
                CONF_RESOURCE: "http://localhost",
                CONF_HEADERS: {"Content-type": CONTENT_TYPE_JSON},
                rest.CONF_BODY_ON: "custom on text",
                rest.CONF_BODY_OFF: "custom off text",
            }
        },
    )
    await.opp.async_block_till_done()
    assert aioclient_mock.call_count == 1
    assert_setup_component(1, SWITCH_DOMAIN)


async def test_setup_with_state_resource.opp, aioclient_mock):
    """Test setup with valid configuration."""
    aioclient_mock.get("http://localhost", status=HTTP_NOT_FOUND)
    aioclient_mock.get("http://localhost/state", status=HTTP_OK)
    assert await async_setup_component(
       .opp,
        SWITCH_DOMAIN,
        {
            SWITCH_DOMAIN: {
                CONF_PLATFORM: DOMAIN,
                CONF_NAME: "foo",
                CONF_RESOURCE: "http://localhost",
                rest.CONF_STATE_RESOURCE: "http://localhost/state",
                CONF_HEADERS: {"Content-type": CONTENT_TYPE_JSON},
                rest.CONF_BODY_ON: "custom on text",
                rest.CONF_BODY_OFF: "custom off text",
            }
        },
    )
    await.opp.async_block_till_done()
    assert aioclient_mock.call_count == 1
    assert_setup_component(1, SWITCH_DOMAIN)


"""Tests for REST switch platform."""


def _setup_test_switch.opp):
    body_on = Template("on",.opp)
    body_off = Template("off",.opp)
    switch = rest.RestSwitch(
        NAME,
        RESOURCE,
        STATE_RESOURCE,
        METHOD,
        HEADERS,
        PARAMS,
        AUTH,
        body_on,
        body_off,
        None,
        10,
        True,
    )
    switch.opp =.opp
    return switch, body_on, body_off


def test_name.opp):
    """Test the name."""
    switch, body_on, body_off = _setup_test_switch.opp)
    assert NAME == switch.name


def test_is_on_before_update.opp):
    """Test is_on in initial state."""
    switch, body_on, body_off = _setup_test_switch.opp)
    assert switch.is_on is None


async def test_turn_on_success.opp, aioclient_mock):
    """Test turn_on."""
    aioclient_mock.post(RESOURCE, status=HTTP_OK)
    switch, body_on, body_off = _setup_test_switch.opp)
    await switch.async_turn_on()

    assert body_on.template == aioclient_mock.mock_calls[-1][2].decode()
    assert switch.is_on


async def test_turn_on_status_not_ok.opp, aioclient_mock):
    """Test turn_on when error status returned."""
    aioclient_mock.post(RESOURCE, status=HTTP_INTERNAL_SERVER_ERROR)
    switch, body_on, body_off = _setup_test_switch.opp)
    await switch.async_turn_on()

    assert body_on.template == aioclient_mock.mock_calls[-1][2].decode()
    assert switch.is_on is None


async def test_turn_on_timeout.opp, aioclient_mock):
    """Test turn_on when timeout occurs."""
    aioclient_mock.post(RESOURCE, status=HTTP_INTERNAL_SERVER_ERROR)
    switch, body_on, body_off = _setup_test_switch.opp)
    await switch.async_turn_on()

    assert switch.is_on is None


async def test_turn_off_success.opp, aioclient_mock):
    """Test turn_off."""
    aioclient_mock.post(RESOURCE, status=HTTP_OK)
    switch, body_on, body_off = _setup_test_switch.opp)
    await switch.async_turn_off()

    assert body_off.template == aioclient_mock.mock_calls[-1][2].decode()
    assert not switch.is_on


async def test_turn_off_status_not_ok.opp, aioclient_mock):
    """Test turn_off when error status returned."""
    aioclient_mock.post(RESOURCE, status=HTTP_INTERNAL_SERVER_ERROR)
    switch, body_on, body_off = _setup_test_switch.opp)
    await switch.async_turn_off()

    assert body_off.template == aioclient_mock.mock_calls[-1][2].decode()
    assert switch.is_on is None


async def test_turn_off_timeout.opp, aioclient_mock):
    """Test turn_off when timeout occurs."""
    aioclient_mock.post(RESOURCE, exc=asyncio.TimeoutError())
    switch, body_on, body_off = _setup_test_switch.opp)
    await switch.async_turn_on()

    assert switch.is_on is None


async def test_update_when_on.opp, aioclient_mock):
    """Test update when switch is on."""
    switch, body_on, body_off = _setup_test_switch.opp)
    aioclient_mock.get(RESOURCE, text=body_on.template)
    await switch.async_update()

    assert switch.is_on


async def test_update_when_off.opp, aioclient_mock):
    """Test update when switch is off."""
    switch, body_on, body_off = _setup_test_switch.opp)
    aioclient_mock.get(RESOURCE, text=body_off.template)
    await switch.async_update()

    assert not switch.is_on


async def test_update_when_unknown.opp, aioclient_mock):
    """Test update when unknown status returned."""
    aioclient_mock.get(RESOURCE, text="unknown status")
    switch, body_on, body_off = _setup_test_switch.opp)
    await switch.async_update()

    assert switch.is_on is None


async def test_update_timeout.opp, aioclient_mock):
    """Test update when timeout occurs."""
    aioclient_mock.get(RESOURCE, exc=asyncio.TimeoutError())
    switch, body_on, body_off = _setup_test_switch.opp)
    await switch.async_update()

    assert switch.is_on is None
