"""Vera tests."""
from unittest.mock import MagicMock

import pyvera as pv

from openpeerpowerr.core import OpenPeerPower

from .common import ComponentFactory, new_simple_controller_config


async def test_scene(
   .opp: OpenPeerPower, vera_component_factory: ComponentFactory
) -> None:
    """Test function."""
    vera_scene = MagicMock(spec=pv.VeraScene)  # type: pv.VeraScene
    vera_scene.scene_id = 1
    vera_scene.vera_scene_id = vera_scene.scene_id
    vera_scene.name = "dev1"
    entity_id = "scene.dev1_1"

    await vera_component_factory.configure_component(
       .opp.opp,
        controller_config=new_simple_controller_config(scenes=(vera_scene,)),
    )

    await.opp.services.async_call(
        "scene",
        "turn_on",
        {"entity_id": entity_id},
    )
    await opp.async_block_till_done()
