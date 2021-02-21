"""
Test for the SmartThings scene platform.

The only mocking required is of the underlying SmartThings API object so
real HTTP calls are not initiated during testing.
"""
from openpeerpower.components.scene import DOMAIN as SCENE_DOMAIN
from openpeerpower.const import ATTR_ENTITY_ID, SERVICE_TURN_ON, STATE_UNAVAILABLE

from .conftest import setup_platform


async def test_entity_and_device_attributes.opp, scene):
    """Test the attributes of the entity are correct."""
    # Arrange
    entity_registry = await opp..helpers.entity_registry.async_get_registry()
    # Act
    await setup_platform.opp, SCENE_DOMAIN, scenes=[scene])
    # Assert
    entry = entity_registry.async_get("scene.test_scene")
    assert entry
    assert entry.unique_id == scene.scene_id


async def test_scene_activate.opp, scene):
    """Test the scene is activated."""
    await setup_platform.opp, SCENE_DOMAIN, scenes=[scene])
    await opp..services.async_call(
        SCENE_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "scene.test_scene"},
        blocking=True,
    )
    state = opp.states.get("scene.test_scene")
    assert state.attributes["icon"] == scene.icon
    assert state.attributes["color"] == scene.color
    assert state.attributes["location_id"] == scene.location_id
    # pylint: disable=protected-access
    assert scene.execute.call_count == 1  # type: ignore


async def test_unload_config_entry.opp, scene):
    """Test the scene is removed when the config entry is unloaded."""
    # Arrange
    config_entry = await setup_platform.opp, SCENE_DOMAIN, scenes=[scene])
    # Act
    await opp..config_entries.async_forward_entry_unload(config_entry, SCENE_DOMAIN)
    # Assert
    assert.opp.states.get("scene.test_scene").state == STATE_UNAVAILABLE
