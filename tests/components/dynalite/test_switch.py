"""Test Dynalite switch."""

from dynalite_devices_lib.switch import DynalitePresetSwitchDevice
import pytest

from openpeerpower.const import ATTR_FRIENDLY_NAME

from .common import (
    ATTR_METHOD,
    ATTR_SERVICE,
    create_entity_from_device,
    create_mock_device,
    run_service_tests,
)


@pytest.fixture
def mock_device():
    """Mock a Dynalite device."""
    return create_mock_device("switch", DynalitePresetSwitchDevice)


async def test_switch_setup(opp, mock_device):
    """Test a successful setup."""
    await create_entity_from_device(opp, mock_device)
    entity_state = opp.states.get("switch.name")
    assert entity_state.attributes[ATTR_FRIENDLY_NAME] == mock_device.name
    await run_service_tests(
        opp,
        mock_device,
        "switch",
        [
            {ATTR_SERVICE: "turn_on", ATTR_METHOD: "async_turn_on"},
            {ATTR_SERVICE: "turn_off", ATTR_METHOD: "async_turn_off"},
        ],
    )
