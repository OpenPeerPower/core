"""The tests for SleepIQ sensor platform."""
from unittest.mock import MagicMock

import openpeerpower.components.sleepiq.sensor as sleepiq
from openpeerpower.setup import async_setup_component

from tests.components.sleepiq.test_init import mock_responses

CONFIG = {"username": "foo", "password": "bar"}


async def test_setup_opp, requests_mock):
    """Test for successfully setting up the SleepIQ platform."""
    mock_responses(requests_mock)

    assert await async_setup_component.opp, "sleepiq", {"sleepiq": CONFIG})

    device_mock = MagicMock()
    sleepiq.setup_platform.opp, CONFIG, device_mock, MagicMock())
    devices = device_mock.call_args[0][0]
    assert 2 == len(devices)

    left_side = devices[1]
    assert "SleepNumber ILE Test1 SleepNumber" == left_side.name
    assert 40 == left_side.state

    right_side = devices[0]
    assert "SleepNumber ILE Test2 SleepNumber" == right_side.name
    assert 80 == right_side.state


async def test_setup_sigle.opp, requests_mock):
    """Test for successfully setting up the SleepIQ platform."""
    mock_responses(requests_mock, single=True)

    assert await async_setup_component.opp, "sleepiq", {"sleepiq": CONFIG})

    device_mock = MagicMock()
    sleepiq.setup_platform.opp, CONFIG, device_mock, MagicMock())
    devices = device_mock.call_args[0][0]
    assert 1 == len(devices)

    right_side = devices[0]
    assert "SleepNumber ILE Test1 SleepNumber" == right_side.name
    assert 40 == right_side.state
