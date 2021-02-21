"""Test Dynalite light."""

from dynalite_devices_lib.light import DynaliteChannelLightDevice
import pytest

from openpeerpower.components.light import SUPPORT_BRIGHTNESS
from openpeerpower.const import (
    ATTR_FRIENDLY_NAME,
    ATTR_SUPPORTED_FEATURES,
    STATE_UNAVAILABLE,
)

from .common import (
    ATTR_METHOD,
    ATTR_SERVICE,
    create_entity_from_device,
    create_mock_device,
    get_entry_id_from_opp,
    run_service_tests,
)


@pytest.fixture
def mock_device():
    """Mock a Dynalite device."""
    return create_mock_device("light", DynaliteChannelLightDevice)


async def test_light_setup.opp, mock_device):
    """Test a successful setup."""
    await create_entity_from_device.opp, mock_device)
    entity_state = opp.states.get("light.name")
    assert entity_state.attributes[ATTR_FRIENDLY_NAME] == mock_device.name
    assert entity_state.attributes["brightness"] == mock_device.brightness
    assert entity_state.attributes[ATTR_SUPPORTED_FEATURES] == SUPPORT_BRIGHTNESS
    await run_service_tests(
       .opp,
        mock_device,
        "light",
        [
            {ATTR_SERVICE: "turn_on", ATTR_METHOD: "async_turn_on"},
            {ATTR_SERVICE: "turn_off", ATTR_METHOD: "async_turn_off"},
        ],
    )


async def test_unload_config_entry.opp, mock_device):
    """Test when a config entry is unloaded from HA."""
    await create_entity_from_device.opp, mock_device)
    assert.opp.states.get("light.name")
    entry_id = await get_entry_id_from_opp.opp)
    assert await opp.config_entries.async_unload(entry_id)
    await opp.async_block_till_done()
    assert.opp.states.get("light.name").state == STATE_UNAVAILABLE


async def test_remove_config_entry.opp, mock_device):
    """Test when a config entry is removed from HA."""
    await create_entity_from_device.opp, mock_device)
    assert.opp.states.get("light.name")
    entry_id = await get_entry_id_from_opp.opp)
    assert await opp.config_entries.async_remove(entry_id)
    await opp.async_block_till_done()
    assert not.opp.states.get("light.name")
