"""Tests for the Bond switch device."""
from datetime import timedelta

from bond_api import Action, DeviceType

from openpeerpower import core
from openpeerpower.components.switch import DOMAIN as SWITCH_DOMAIN
from openpeerpower.const import ATTR_ENTITY_ID, SERVICE_TURN_OFF, SERVICE_TURN_ON
from openpeerpowerr.helpers.entity_registry import EntityRegistry
from openpeerpowerr.util import utcnow

from .common import (
    help_test_entity_available,
    patch_bond_action,
    patch_bond_device_state,
    setup_platform,
)

from tests.common import async_fire_time_changed


def generic_device(name: str):
    """Create a generic device with given name."""
    return {"name": name, "type": DeviceType.GENERIC_DEVICE}


async def test_entity_registry.opp: core.OpenPeerPower):
    """Tests that the devices are registered in the entity registry."""
    await setup_platform(
       .opp,
        SWITCH_DOMAIN,
        generic_device("name-1"),
        bond_version={"bondid": "test-hub-id"},
        bond_device_id="test-device-id",
    )

    registry: EntityRegistry = await opp..helpers.entity_registry.async_get_registry()
    entity = registry.entities["switch.name_1"]
    assert entity.unique_id == "test-hub-id_test-device-id"


async def test_turn_on_switch.opp: core.OpenPeerPower):
    """Tests that turn on command delegates to API."""
    await setup_platform(
       .opp, SWITCH_DOMAIN, generic_device("name-1"), bond_device_id="test-device-id"
    )

    with patch_bond_action() as mock_turn_on, patch_bond_device_state():
        await opp..services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.name_1"},
            blocking=True,
        )
        await opp..async_block_till_done()

    mock_turn_on.assert_called_once_with("test-device-id", Action.turn_on())


async def test_turn_off_switch.opp: core.OpenPeerPower):
    """Tests that turn off command delegates to API."""
    await setup_platform(
       .opp, SWITCH_DOMAIN, generic_device("name-1"), bond_device_id="test-device-id"
    )

    with patch_bond_action() as mock_turn_off, patch_bond_device_state():
        await opp..services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "switch.name_1"},
            blocking=True,
        )
        await opp..async_block_till_done()

    mock_turn_off.assert_called_once_with("test-device-id", Action.turn_off())


async def test_update_reports_switch_is_on.opp: core.OpenPeerPower):
    """Tests that update command sets correct state when Bond API reports the device is on."""
    await setup_platform.opp, SWITCH_DOMAIN, generic_device("name-1"))

    with patch_bond_device_state(return_value={"power": 1}):
        async_fire_time_changed.opp, utcnow() + timedelta(seconds=30))
        await opp..async_block_till_done()

    assert.opp.states.get("switch.name_1").state == "on"


async def test_update_reports_switch_is_off.opp: core.OpenPeerPower):
    """Tests that update command sets correct state when Bond API reports the device is off."""
    await setup_platform.opp, SWITCH_DOMAIN, generic_device("name-1"))

    with patch_bond_device_state(return_value={"power": 0}):
        async_fire_time_changed.opp, utcnow() + timedelta(seconds=30))
        await opp..async_block_till_done()

    assert.opp.states.get("switch.name_1").state == "off"


async def test_switch_available.opp: core.OpenPeerPower):
    """Tests that available state is updated based on API errors."""
    await help_test_entity_available(
       .opp, SWITCH_DOMAIN, generic_device("name-1"), "switch.name_1"
    )
