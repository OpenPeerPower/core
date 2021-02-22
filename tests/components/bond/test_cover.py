"""Tests for the Bond cover device."""
from datetime import timedelta

from bond_api import Action, DeviceType

from openpeerpower import core
from openpeerpower.components.cover import DOMAIN as COVER_DOMAIN
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    SERVICE_CLOSE_COVER,
    SERVICE_OPEN_COVER,
    SERVICE_STOP_COVER,
)
from openpeerpower.helpers.entity_registry import EntityRegistry
from openpeerpower.util import utcnow

from .common import (
    help_test_entity_available,
    patch_bond_action,
    patch_bond_device_state,
    setup_platform,
)

from tests.common import async_fire_time_changed


def shades(name: str):
    """Create motorized shades with given name."""
    return {"name": name, "type": DeviceType.MOTORIZED_SHADES}


async def test_entity_registry.opp: core.OpenPeerPower):
    """Tests that the devices are registered in the entity registry."""
    await setup_platform(
        opp,
        COVER_DOMAIN,
        shades("name-1"),
        bond_version={"bondid": "test-hub-id"},
        bond_device_id="test-device-id",
    )

    registry: EntityRegistry = await opp.helpers.entity_registry.async_get_registry()
    entity = registry.entities["cover.name_1"]
    assert entity.unique_id == "test-hub-id_test-device-id"


async def test_open_cover.opp: core.OpenPeerPower):
    """Tests that open cover command delegates to API."""
    await setup_platform(
        opp, COVER_DOMAIN, shades("name-1"), bond_device_id="test-device-id"
    )

    with patch_bond_action() as mock_open, patch_bond_device_state():
        await opp.services.async_call(
            COVER_DOMAIN,
            SERVICE_OPEN_COVER,
            {ATTR_ENTITY_ID: "cover.name_1"},
            blocking=True,
        )
        await opp.async_block_till_done()

    mock_open.assert_called_once_with("test-device-id", Action.open())


async def test_close_cover.opp: core.OpenPeerPower):
    """Tests that close cover command delegates to API."""
    await setup_platform(
        opp, COVER_DOMAIN, shades("name-1"), bond_device_id="test-device-id"
    )

    with patch_bond_action() as mock_close, patch_bond_device_state():
        await opp.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER,
            {ATTR_ENTITY_ID: "cover.name_1"},
            blocking=True,
        )
        await opp.async_block_till_done()

    mock_close.assert_called_once_with("test-device-id", Action.close())


async def test_stop_cover.opp: core.OpenPeerPower):
    """Tests that stop cover command delegates to API."""
    await setup_platform(
        opp, COVER_DOMAIN, shades("name-1"), bond_device_id="test-device-id"
    )

    with patch_bond_action() as mock_hold, patch_bond_device_state():
        await opp.services.async_call(
            COVER_DOMAIN,
            SERVICE_STOP_COVER,
            {ATTR_ENTITY_ID: "cover.name_1"},
            blocking=True,
        )
        await opp.async_block_till_done()

    mock_hold.assert_called_once_with("test-device-id", Action.hold())


async def test_update_reports_open_cover.opp: core.OpenPeerPower):
    """Tests that update command sets correct state when Bond API reports cover is open."""
    await setup_platform.opp, COVER_DOMAIN, shades("name-1"))

    with patch_bond_device_state(return_value={"open": 1}):
        async_fire_time_changed.opp, utcnow() + timedelta(seconds=30))
        await opp.async_block_till_done()

    assert.opp.states.get("cover.name_1").state == "open"


async def test_update_reports_closed_cover.opp: core.OpenPeerPower):
    """Tests that update command sets correct state when Bond API reports cover is closed."""
    await setup_platform.opp, COVER_DOMAIN, shades("name-1"))

    with patch_bond_device_state(return_value={"open": 0}):
        async_fire_time_changed.opp, utcnow() + timedelta(seconds=30))
        await opp.async_block_till_done()

    assert.opp.states.get("cover.name_1").state == "closed"


async def test_cover_available.opp: core.OpenPeerPower):
    """Tests that available state is updated based on API errors."""
    await help_test_entity_available(
        opp, COVER_DOMAIN, shades("name-1"), "cover.name_1"
    )
