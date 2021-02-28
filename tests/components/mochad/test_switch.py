"""The tests for the mochad switch platform."""
import unittest.mock as mock

import pytest

from openpeerpower.components import switch
from openpeerpower.components.mochad import switch as mochad
from openpeerpower.setup import async_setup_component


@pytest.fixture(autouse=True)
def pymochad_mock():
    """Mock pymochad."""
    with mock.patch("openpeerpower.components.mochad.switch.device"), mock.patch(
        "openpeerpower.components.mochad.switch.MochadException"
    ):
        yield


@pytest.fixture
def switch_mock(opp):
    """Mock switch."""
    controller_mock = mock.MagicMock()
    dev_dict = {"address": "a1", "name": "fake_switch"}
    return mochad.MochadSwitch.opp, controller_mock, dev_dict)


async def test_setup_adds_proper_devices(opp):
    """Test if setup adds devices."""
    good_config = {
        "mochad": {},
        "switch": {
            "platform": "mochad",
            "devices": [{"name": "Switch1", "address": "a1"}],
        },
    }
    assert await async_setup_component(opp, switch.DOMAIN, good_config)


async def test_name(switch_mock):
    """Test the name."""
    assert "fake_switch" == switch_mock.name


async def test_turn_on(switch_mock):
    """Test turn_on."""
    switch_mock.turn_on()
    switch_mock.switch.send_cmd.assert_called_once_with("on")


async def test_turn_off(switch_mock):
    """Test turn_off."""
    switch_mock.turn_off()
    switch_mock.switch.send_cmd.assert_called_once_with("off")
