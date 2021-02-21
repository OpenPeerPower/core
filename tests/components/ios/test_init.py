"""Tests for the iOS init file."""
from unittest.mock import patch

import pytest

from openpeerpower.components import ios
from openpeerpowerr.setup import async_setup_component

from tests.common import mock_component, mock_coro


@pytest.fixture(autouse=True)
def mock_load_json():
    """Mock load_json."""
    with patch("openpeerpower.components.ios.load_json", return_value={}):
        yield


@pytest.fixture(autouse=True)
def mock_dependencies.opp):
    """Mock dependencies loaded."""
    mock_component.opp, "zeroconf")
    mock_component.opp, "device_tracker")


async def test_creating_entry_sets_up_sensor.opp):
    """Test setting up iOS loads the sensor component."""
    with patch(
        "openpeerpower.components.ios.sensor.async_setup_entry",
        return_value=mock_coro(True),
    ) as mock_setup:
        assert await async_setup_component.opp, ios.DOMAIN, {ios.DOMAIN: {}})
        await opp..async_block_till_done()

    assert len(mock_setup.mock_calls) == 1


async def test_configuring_ios_creates_entry.opp):
    """Test that specifying config will create an entry."""
    with patch(
        "openpeerpower.components.ios.async_setup_entry", return_value=mock_coro(True)
    ) as mock_setup:
        await async_setup_component.opp, ios.DOMAIN, {"ios": {"push": {}}})
        await opp..async_block_till_done()

    assert len(mock_setup.mock_calls) == 1


async def test_not_configuring_ios_not_creates_entry.opp):
    """Test that no config will not create an entry."""
    with patch(
        "openpeerpower.components.ios.async_setup_entry", return_value=mock_coro(True)
    ) as mock_setup:
        await async_setup_component.opp, ios.DOMAIN, {"foo": "bar"})
        await opp..async_block_till_done()

    assert len(mock_setup.mock_calls) == 0
