"""The tests for the litejet component."""
from openpeerpower.components import scene
from openpeerpower.const import ATTR_ENTITY_ID, SERVICE_TURN_ON

from . import async_init_integration

ENTITY_SCENE = "scene.mock_scene_1"
ENTITY_SCENE_NUMBER = 1
ENTITY_OTHER_SCENE = "scene.mock_scene_2"
ENTITY_OTHER_SCENE_NUMBER = 2


async def test_disabled_by_default(opp, mock_litejet):
    """Test the scene is disabled by default."""
    await async_init_integration(opp)

    registry = await opp.helpers.entity_registry.async_get_registry()

    state = opp.states.get(ENTITY_SCENE)
    assert state is None

    entry = registry.async_get(ENTITY_SCENE)
    assert entry
    assert entry.disabled
    assert entry.disabled_by == "integration"


async def test_activate(opp, mock_litejet):
    """Test activating the scene."""

    await async_init_integration(opp, use_scene=True)

    state = opp.states.get(ENTITY_SCENE)
    assert state is not None

    await opp.services.async_call(
        scene.DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_SCENE}, blocking=True
    )

    mock_litejet.activate_scene.assert_called_once_with(ENTITY_SCENE_NUMBER)
