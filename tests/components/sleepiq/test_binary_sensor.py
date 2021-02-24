"""The tests for SleepIQ binary sensor platform."""
from unittest.mock import MagicMock

from openpeerpower.components.sleepiq import binary_sensor as sleepiq
from openpeerpower.setup import async_setup_component

from tests.components.sleepiq.test_init import mock_responses

CONFIG = {"username": "foo", "password": "bar"}


async def test_sensor_setup_opp, requests_mock):
    """Test for successfully setting up the SleepIQ platform."""
    mock_responses(requests_mock)

    await async_setup_component(opp, "sleepiq", {"sleepiq": CONFIG})

    device_mock = MagicMock()
    sleepiq.setup_platform(opp, CONFIG, device_mock, MagicMock())
    devices = device_mock.call_args[0][0]
    assert 2 == len(devices)

    left_side = devices[1]
    assert "SleepNumber ILE Test1 Is In Bed" == left_side.name
    assert "on" == left_side.state

    right_side = devices[0]
    assert "SleepNumber ILE Test2 Is In Bed" == right_side.name
    assert "off" == right_side.state


async def test_setup_single(opp, requests_mock):
    """Test for successfully setting up the SleepIQ platform."""
    mock_responses(requests_mock, single=True)

    await async_setup_component(opp, "sleepiq", {"sleepiq": CONFIG})

    device_mock = MagicMock()
    sleepiq.setup_platform(opp, CONFIG, device_mock, MagicMock())
    devices = device_mock.call_args[0][0]
    assert 1 == len(devices)

    right_side = devices[0]
    assert "SleepNumber ILE Test1 Is In Bed" == right_side.name
    assert "on" == right_side.state
