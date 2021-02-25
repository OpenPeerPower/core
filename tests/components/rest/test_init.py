"""Tests for rest component."""

import asyncio
from datetime import timedelta
from os import path
from unittest.mock import patch

import respx

from openpeerpower import config as.opp_config
from openpeerpower.components.rest.const import DOMAIN
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    DATA_MEGABYTES,
    SERVICE_RELOAD,
    STATE_UNAVAILABLE,
)
from openpeerpower.setup import async_setup_component
from openpeerpower.util.dt import utcnow

from tests.common import async_fire_time_changed


@respx.mock
async def test_setup_with_endpoint_timeout_with_recovery.opp):
    """Test setup with an endpoint that times out that recovers."""
    await async_setup_component(opp, "openpeerpower", {})

    respx.get("http://localhost").mock(side_effect=asyncio.TimeoutError())
    assert await async_setup_component(
        opp,
        DOMAIN,
        {
            DOMAIN: [
                {
                    "resource": "http://localhost",
                    "method": "GET",
                    "verify_ssl": "false",
                    "timeout": 30,
                    "sensor": [
                        {
                            "unit_of_measurement": DATA_MEGABYTES,
                            "name": "sensor1",
                            "value_template": "{{ value_json.sensor1 }}",
                        },
                        {
                            "unit_of_measurement": DATA_MEGABYTES,
                            "name": "sensor2",
                            "value_template": "{{ value_json.sensor2 }}",
                        },
                    ],
                    "binary_sensor": [
                        {
                            "name": "binary_sensor1",
                            "value_template": "{{ value_json.binary_sensor1 }}",
                        },
                        {
                            "name": "binary_sensor2",
                            "value_template": "{{ value_json.binary_sensor2 }}",
                        },
                    ],
                }
            ]
        },
    )
    await opp.async_block_till_done()
    assert len.opp.states.async_all()) == 0

    respx.get("http://localhost").respond(
        status_code=200,
        json={
            "sensor1": "1",
            "sensor2": "2",
            "binary_sensor1": "on",
            "binary_sensor2": "off",
        },
    )

    # Refresh the coordinator
    async_fire_time_changed(opp, utcnow() + timedelta(seconds=31))
    await opp.async_block_till_done()

    # Wait for platform setup retry
    async_fire_time_changed(opp, utcnow() + timedelta(seconds=61))
    await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 4

    assert opp.states.get("sensor.sensor1").state == "1"
    assert opp.states.get("sensor.sensor2").state == "2"
    assert opp.states.get("binary_sensor.binary_sensor1").state == "on"
    assert opp.states.get("binary_sensor.binary_sensor2").state == "off"

    # Now the end point flakes out again
    respx.get("http://localhost").mock(side_effect=asyncio.TimeoutError())

    # Refresh the coordinator
    async_fire_time_changed(opp, utcnow() + timedelta(seconds=31))
    await opp.async_block_till_done()

    assert opp.states.get("sensor.sensor1").state == STATE_UNAVAILABLE
    assert opp.states.get("sensor.sensor2").state == STATE_UNAVAILABLE
    assert opp.states.get("binary_sensor.binary_sensor1").state == STATE_UNAVAILABLE
    assert opp.states.get("binary_sensor.binary_sensor2").state == STATE_UNAVAILABLE

    # We request a manual refresh when the
    # endpoint is working again

    respx.get("http://localhost").respond(
        status_code=200,
        json={
            "sensor1": "1",
            "sensor2": "2",
            "binary_sensor1": "on",
            "binary_sensor2": "off",
        },
    )

    await opp.services.async_call(
        "openpeerpower",
        "update_entity",
        {ATTR_ENTITY_ID: ["sensor.sensor1"]},
        blocking=True,
    )
    assert opp.states.get("sensor.sensor1").state == "1"
    assert opp.states.get("sensor.sensor2").state == "2"
    assert opp.states.get("binary_sensor.binary_sensor1").state == "on"
    assert opp.states.get("binary_sensor.binary_sensor2").state == "off"


@respx.mock
async def test_setup_minimum_resource_template.opp):
    """Test setup with minimum configuration (resource_template)."""

    respx.get("http://localhost").respond(
        status_code=200,
        json={
            "sensor1": "1",
            "sensor2": "2",
            "binary_sensor1": "on",
            "binary_sensor2": "off",
        },
    )
    assert await async_setup_component(
        opp,
        DOMAIN,
        {
            DOMAIN: [
                {
                    "resource_template": "{% set url = 'http://localhost' %}{{ url }}",
                    "method": "GET",
                    "verify_ssl": "false",
                    "timeout": 30,
                    "sensor": [
                        {
                            "unit_of_measurement": DATA_MEGABYTES,
                            "name": "sensor1",
                            "value_template": "{{ value_json.sensor1 }}",
                        },
                        {
                            "unit_of_measurement": DATA_MEGABYTES,
                            "name": "sensor2",
                            "value_template": "{{ value_json.sensor2 }}",
                        },
                    ],
                    "binary_sensor": [
                        {
                            "name": "binary_sensor1",
                            "value_template": "{{ value_json.binary_sensor1 }}",
                        },
                        {
                            "name": "binary_sensor2",
                            "value_template": "{{ value_json.binary_sensor2 }}",
                        },
                    ],
                }
            ]
        },
    )
    await opp.async_block_till_done()
    assert len.opp.states.async_all()) == 4

    assert opp.states.get("sensor.sensor1").state == "1"
    assert opp.states.get("sensor.sensor2").state == "2"
    assert opp.states.get("binary_sensor.binary_sensor1").state == "on"
    assert opp.states.get("binary_sensor.binary_sensor2").state == "off"


@respx.mock
async def test_reload.opp):
    """Verify we can reload."""

    respx.get("http://localhost") % 200

    assert await async_setup_component(
        opp,
        DOMAIN,
        {
            DOMAIN: [
                {
                    "resource": "http://localhost",
                    "method": "GET",
                    "verify_ssl": "false",
                    "timeout": 30,
                    "sensor": [
                        {
                            "name": "mockrest",
                        },
                    ],
                }
            ]
        },
    )
    await opp.async_block_till_done()
    await opp.async_start()
    await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 1

    assert opp.states.get("sensor.mockrest")

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "rest/configuration_top_level.yaml",
    )
    with patch.object.opp_config, "YAML_CONFIG_FILE", yaml_path):
        await opp.services.async_call(
            "rest",
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await opp.async_block_till_done()

    assert opp.states.get("sensor.mockreset") is None
    assert opp.states.get("sensor.rollout")
    assert opp.states.get("sensor.fallover")


@respx.mock
async def test_reload_and_remove_all.opp):
    """Verify we can reload and remove all."""

    respx.get("http://localhost") % 200

    assert await async_setup_component(
        opp,
        DOMAIN,
        {
            DOMAIN: [
                {
                    "resource": "http://localhost",
                    "method": "GET",
                    "verify_ssl": "false",
                    "timeout": 30,
                    "sensor": [
                        {
                            "name": "mockrest",
                        },
                    ],
                }
            ]
        },
    )
    await opp.async_block_till_done()
    await opp.async_start()
    await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 1

    assert opp.states.get("sensor.mockrest")

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "rest/configuration_empty.yaml",
    )
    with patch.object.opp_config, "YAML_CONFIG_FILE", yaml_path):
        await opp.services.async_call(
            "rest",
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await opp.async_block_till_done()

    assert opp.states.get("sensor.mockreset") is None


@respx.mock
async def test_reload_fails_to_read_configuration.opp):
    """Verify reload when configuration is missing or broken."""

    respx.get("http://localhost") % 200

    assert await async_setup_component(
        opp,
        DOMAIN,
        {
            DOMAIN: [
                {
                    "resource": "http://localhost",
                    "method": "GET",
                    "verify_ssl": "false",
                    "timeout": 30,
                    "sensor": [
                        {
                            "name": "mockrest",
                        },
                    ],
                }
            ]
        },
    )
    await opp.async_block_till_done()
    await opp.async_start()
    await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 1

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "rest/configuration_invalid.notyaml",
    )
    with patch.object.opp_config, "YAML_CONFIG_FILE", yaml_path):
        await opp.services.async_call(
            "rest",
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 1


def _get_fixtures_base_path():
    return path.dirname(path.dirname(path.dirname(__file__)))
