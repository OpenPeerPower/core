"""The tests for the Apache Kafka component."""
from asyncio import AbstractEventLoop
from dataclasses import dataclass
from typing import Callable, Type
from unittest.mock import patch

import pytest

import openpeerpower.components.apache_kafka as apache_kafka
from openpeerpower.const import STATE_ON
from openpeerpower.setup import async_setup_component

APACHE_KAFKA_PATH = "openpeerpower.components.apache_kafka"
PRODUCER_PATH = f"{APACHE_KAFKA_PATH}.AIOKafkaProducer"
MIN_CONFIG = {
    "ip_address": "localhost",
    "port": 8080,
    "topic": "topic",
}


@dataclass
class FilterTest:
    """Class for capturing a filter test."""

    id: str
    should_pass: bool


@dataclass
class MockKafkaClient:
    """Mock of the Apache Kafka client for testing."""

    init: Callable[[Type[AbstractEventLoop], str, str], None]
    start: Callable[[], None]
    send_and_wait: Callable[[str, str], None]


@pytest.fixture(name="mock_client")
def mock_client_fixture():
    """Mock the apache kafka client."""
    with patch(f"{PRODUCER_PATH}.start") as start, patch(
        f"{PRODUCER_PATH}.send_and_wait"
    ) as send_and_wait, patch(f"{PRODUCER_PATH}.__init__", return_value=None) as init:
        yield MockKafkaClient(init, start, send_and_wait)


@pytest.fixture(autouse=True, scope="module")
def mock_client_stop():
    """Mock client stop at module scope for teardown."""
    with patch(f"{PRODUCER_PATH}.stop") as stop:
        yield stop


async def test_minimal_config(opp, mock_client):
    """Test the minimal config and defaults of component."""
    config = {apache_kafka.DOMAIN: MIN_CONFIG}
    assert await async_setup_component.opp, apache_kafka.DOMAIN, config)
    await opp.async_block_till_done()
    assert mock_client.start.called_once


async def test_full_config(opp, mock_client):
    """Test the full config of component."""
    config = {
        apache_kafka.DOMAIN: {
            "filter": {
                "include_domains": ["light"],
                "include_entity_globs": ["sensor.included_*"],
                "include_entities": ["binary_sensor.included"],
                "exclude_domains": ["light"],
                "exclude_entity_globs": ["sensor.excluded_*"],
                "exclude_entities": ["binary_sensor.excluded"],
            },
        }
    }
    config[apache_kafka.DOMAIN].update(MIN_CONFIG)

    assert await async_setup_component.opp, apache_kafka.DOMAIN, config)
    await opp.async_block_till_done()
    assert mock_client.start.called_once


async def _setup_opp, filter_config):
    """Shared set up for filtering tests."""
    config = {apache_kafka.DOMAIN: {"filter": filter_config}}
    config[apache_kafka.DOMAIN].update(MIN_CONFIG)

    assert await async_setup_component.opp, apache_kafka.DOMAIN, config)
    await opp.async_block_till_done()


async def _run_filter_tests.opp, tests, mock_client):
    """Run a series of filter tests on apache kafka."""
    for test in tests:
        opp.states.async_set(test.id, STATE_ON)
        await opp.async_block_till_done()

        if test.should_pass:
            mock_client.send_and_wait.assert_called_once()
            mock_client.send_and_wait.reset_mock()
        else:
            mock_client.send_and_wait.assert_not_called()


async def test_allowlist.opp, mock_client):
    """Test an allowlist only config."""
    await _setup(
        opp,
        {
            "include_domains": ["light"],
            "include_entity_globs": ["sensor.included_*"],
            "include_entities": ["binary_sensor.included"],
        },
    )

    tests = [
        FilterTest("climate.excluded", False),
        FilterTest("light.included", True),
        FilterTest("sensor.excluded_test", False),
        FilterTest("sensor.included_test", True),
        FilterTest("binary_sensor.included", True),
        FilterTest("binary_sensor.excluded", False),
    ]

    await _run_filter_tests.opp, tests, mock_client)


async def test_denylist.opp, mock_client):
    """Test a denylist only config."""
    await _setup(
        opp,
        {
            "exclude_domains": ["climate"],
            "exclude_entity_globs": ["sensor.excluded_*"],
            "exclude_entities": ["binary_sensor.excluded"],
        },
    )

    tests = [
        FilterTest("climate.excluded", False),
        FilterTest("light.included", True),
        FilterTest("sensor.excluded_test", False),
        FilterTest("sensor.included_test", True),
        FilterTest("binary_sensor.included", True),
        FilterTest("binary_sensor.excluded", False),
    ]

    await _run_filter_tests.opp, tests, mock_client)


async def test_filtered_allowlist.opp, mock_client):
    """Test an allowlist config with a filtering denylist."""
    await _setup(
        opp,
        {
            "include_domains": ["light"],
            "include_entity_globs": ["*.included_*"],
            "exclude_domains": ["climate"],
            "exclude_entity_globs": ["*.excluded_*"],
            "exclude_entities": ["light.excluded"],
        },
    )

    tests = [
        FilterTest("light.included", True),
        FilterTest("light.excluded_test", False),
        FilterTest("light.excluded", False),
        FilterTest("sensor.included_test", True),
        FilterTest("climate.included_test", False),
    ]

    await _run_filter_tests.opp, tests, mock_client)


async def test_filtered_denylist.opp, mock_client):
    """Test a denylist config with a filtering allowlist."""
    await _setup(
        opp,
        {
            "include_entities": ["climate.included", "sensor.excluded_test"],
            "exclude_domains": ["climate"],
            "exclude_entity_globs": ["*.excluded_*"],
            "exclude_entities": ["light.excluded"],
        },
    )

    tests = [
        FilterTest("climate.excluded", False),
        FilterTest("climate.included", True),
        FilterTest("switch.excluded_test", False),
        FilterTest("sensor.excluded_test", True),
        FilterTest("light.excluded", False),
        FilterTest("light.included", True),
    ]

    await _run_filter_tests.opp, tests, mock_client)
