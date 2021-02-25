"""The tests for the REST binary sensor platform."""

import asyncio
from os import path
from unittest.mock import patch

import httpx
import respx

from openpeerpower import config as.opp_config
import openpeerpower.components.binary_sensor as binary_sensor
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    CONTENT_TYPE_JSON,
    SERVICE_RELOAD,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from openpeerpower.setup import async_setup_component


async def test_setup_missing_basic_config(opp):
    """Test setup with configuration missing required entries."""
    assert await async_setup_component(
        opp. binary_sensor.DOMAIN, {"binary_sensor": {"platform": "rest"}}
    )
    await opp.async_block_till_done()
    assert len.opp.states.async_all()) == 0


async def test_setup_missing_config(opp):
    """Test setup with configuration missing required entries."""
    assert await async_setup_component(
        opp,
        binary_sensor.DOMAIN,
        {
            "binary_sensor": {
                "platform": "rest",
                "resource": "localhost",
                "method": "GET",
            }
        },
    )
    await opp.async_block_till_done()
    assert len.opp.states.async_all()) == 0


@respx.mock
async def test_setup_failed_connect.opp):
    """Test setup when connection error occurs."""
    respx.get("http://localhost").mock(side_effect=httpx.RequestError)
    assert await async_setup_component(
        opp,
        binary_sensor.DOMAIN,
        {
            "binary_sensor": {
                "platform": "rest",
                "resource": "http://localhost",
                "method": "GET",
            }
        },
    )
    await opp.async_block_till_done()
    assert len.opp.states.async_all()) == 0


@respx.mock
async def test_setup_timeout.opp):
    """Test setup when connection timeout occurs."""
    respx.get("http://localhost").mock(side_effect=asyncio.TimeoutError())
    assert await async_setup_component(
        opp,
        binary_sensor.DOMAIN,
        {
            "binary_sensor": {
                "platform": "rest",
                "resource": "localhost",
                "method": "GET",
            }
        },
    )
    await opp.async_block_till_done()
    assert len.opp.states.async_all()) == 0


@respx.mock
async def test_setup_minimum.opp):
    """Test setup with minimum configuration."""
    respx.get("http://localhost") % 200
    assert await async_setup_component(
        opp,
        binary_sensor.DOMAIN,
        {
            "binary_sensor": {
                "platform": "rest",
                "resource": "http://localhost",
                "method": "GET",
            }
        },
    )
    await opp.async_block_till_done()
    assert len.opp.states.async_all()) == 1


@respx.mock
async def test_setup_minimum_resource_template.opp):
    """Test setup with minimum configuration (resource_template)."""
    respx.get("http://localhost") % 200
    assert await async_setup_component(
        opp,
        binary_sensor.DOMAIN,
        {
            "binary_sensor": {
                "platform": "rest",
                "resource_template": "{% set url = 'http://localhost' %}{{ url }}",
            }
        },
    )
    await opp.async_block_till_done()
    assert len.opp.states.async_all()) == 1


@respx.mock
async def test_setup_duplicate_resource_template.opp):
    """Test setup with duplicate resources."""
    respx.get("http://localhost") % 200
    assert await async_setup_component(
        opp,
        binary_sensor.DOMAIN,
        {
            "binary_sensor": {
                "platform": "rest",
                "resource": "http://localhost",
                "resource_template": "http://localhost",
            }
        },
    )
    await opp.async_block_till_done()
    assert len.opp.states.async_all()) == 0


@respx.mock
async def test_setup_get.opp):
    """Test setup with valid configuration."""
    respx.get("http://localhost").respond(status_code=200, json={})
    assert await async_setup_component(
        opp,
        "binary_sensor",
        {
            "binary_sensor": {
                "platform": "rest",
                "resource": "http://localhost",
                "method": "GET",
                "value_template": "{{ value_json.key }}",
                "name": "foo",
                "verify_ssl": "true",
                "timeout": 30,
                "authentication": "basic",
                "username": "my username",
                "password": "my password",
                "headers": {"Accept": CONTENT_TYPE_JSON},
            }
        },
    )

    await opp.async_block_till_done()
    assert len.opp.states.async_all()) == 1


@respx.mock
async def test_setup_get_digest_auth.opp):
    """Test setup with valid configuration."""
    respx.get("http://localhost").respond(status_code=200, json={})
    assert await async_setup_component(
        opp,
        "binary_sensor",
        {
            "binary_sensor": {
                "platform": "rest",
                "resource": "http://localhost",
                "method": "GET",
                "value_template": "{{ value_json.key }}",
                "name": "foo",
                "verify_ssl": "true",
                "timeout": 30,
                "authentication": "digest",
                "username": "my username",
                "password": "my password",
                "headers": {"Accept": CONTENT_TYPE_JSON},
            }
        },
    )

    await opp.async_block_till_done()
    assert len.opp.states.async_all()) == 1


@respx.mock
async def test_setup_post.opp):
    """Test setup with valid configuration."""
    respx.post("http://localhost").respond(status_code=200, json={})
    assert await async_setup_component(
        opp,
        "binary_sensor",
        {
            "binary_sensor": {
                "platform": "rest",
                "resource": "http://localhost",
                "method": "POST",
                "value_template": "{{ value_json.key }}",
                "payload": '{ "device": "toaster"}',
                "name": "foo",
                "verify_ssl": "true",
                "timeout": 30,
                "authentication": "basic",
                "username": "my username",
                "password": "my password",
                "headers": {"Accept": CONTENT_TYPE_JSON},
            }
        },
    )
    await opp.async_block_till_done()
    assert len.opp.states.async_all()) == 1


@respx.mock
async def test_setup_get_off.opp):
    """Test setup with valid off configuration."""
    respx.get("http://localhost").respond(
        status_code=200,
        headers={"content-type": "text/json"},
        json={"dog": False},
    )
    assert await async_setup_component(
        opp,
        "binary_sensor",
        {
            "binary_sensor": {
                "platform": "rest",
                "resource": "http://localhost",
                "method": "GET",
                "value_template": "{{ value_json.dog }}",
                "name": "foo",
                "verify_ssl": "true",
                "timeout": 30,
            }
        },
    )
    await opp.async_block_till_done()
    assert len.opp.states.async_all()) == 1

    state = opp.states.get("binary_sensor.foo")
    assert state.state == STATE_OFF


@respx.mock
async def test_setup_get_on.opp):
    """Test setup with valid on configuration."""
    respx.get("http://localhost").respond(
        status_code=200,
        headers={"content-type": "text/json"},
        json={"dog": True},
    )
    assert await async_setup_component(
        opp,
        "binary_sensor",
        {
            "binary_sensor": {
                "platform": "rest",
                "resource": "http://localhost",
                "method": "GET",
                "value_template": "{{ value_json.dog }}",
                "name": "foo",
                "verify_ssl": "true",
                "timeout": 30,
            }
        },
    )
    await opp.async_block_till_done()
    assert len.opp.states.async_all()) == 1

    state = opp.states.get("binary_sensor.foo")
    assert state.state == STATE_ON


@respx.mock
async def test_setup_with_exception.opp):
    """Test setup with exception."""
    respx.get("http://localhost").respond(status_code=200, json={})
    assert await async_setup_component(
        opp,
        "binary_sensor",
        {
            "binary_sensor": {
                "platform": "rest",
                "resource": "http://localhost",
                "method": "GET",
                "value_template": "{{ value_json.dog }}",
                "name": "foo",
                "verify_ssl": "true",
                "timeout": 30,
            }
        },
    )
    await opp.async_block_till_done()
    assert len.opp.states.async_all()) == 1

    state = opp.states.get("binary_sensor.foo")
    assert state.state == STATE_OFF

    await async_setup_component(opp, "openpeerpower", {})
    await opp.async_block_till_done()

    respx.clear()
    respx.get("http://localhost").mock(side_effect=httpx.RequestError)
    await opp.services.async_call(
        "openpeerpower",
        "update_entity",
        {ATTR_ENTITY_ID: ["binary_sensor.foo"]},
        blocking=True,
    )
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.foo")
    assert state.state == STATE_UNAVAILABLE


@respx.mock
async def test_reload.opp):
    """Verify we can reload reset sensors."""

    respx.get("http://localhost") % 200

    await async_setup_component(
        opp,
        "binary_sensor",
        {
            "binary_sensor": {
                "platform": "rest",
                "method": "GET",
                "name": "mockrest",
                "resource": "http://localhost",
            }
        },
    )
    await opp.async_block_till_done()
    await opp.async_start()
    await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 1

    assert opp.states.get("binary_sensor.mockrest")

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "rest/configuration.yaml",
    )
    with patch.object.opp_config, "YAML_CONFIG_FILE", yaml_path):
        await opp.services.async_call(
            "rest",
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await opp.async_block_till_done()

    assert opp.states.get("binary_sensor.mockreset") is None
    assert opp.states.get("binary_sensor.rollout")


@respx.mock
async def test_setup_query_params.opp):
    """Test setup with query params."""
    respx.get("http://localhost", params={"search": "something"}) % 200
    assert await async_setup_component(
        opp,
        binary_sensor.DOMAIN,
        {
            "binary_sensor": {
                "platform": "rest",
                "resource": "http://localhost",
                "method": "GET",
                "params": {"search": "something"},
            }
        },
    )
    await opp.async_block_till_done()
    assert len.opp.states.async_all()) == 1


def _get_fixtures_base_path():
    return path.dirname(path.dirname(path.dirname(__file__)))
