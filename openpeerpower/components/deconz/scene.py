"""Support for deCONZ scenes."""
from typing import Any

from openpeerpower.components.scene import Scene
from openpeerpower.core import callback
from openpeerpower.helpers.dispatcher import async_dispatcher_connect

from .const import NEW_SCENE
from .gateway import get_gateway_from_config_entry


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up scenes for deCONZ component."""
    gateway = get_gateway_from_config_entry(opp, config_entry)

    @callback
    def async_add_scene(scenes=gateway.api.scenes.values()):
        """Add scene from deCONZ."""
        entities = [DeconzScene(scene, gateway) for scene in scenes]

        if entities:
            async_add_entities(entities)

    gateway.listeners.append(
        async_dispatcher_connect(
            opp, gateway.async_signal_new_device(NEW_SCENE), async_add_scene
        )
    )

    async_add_scene()


class DeconzScene(Scene):
    """Representation of a deCONZ scene."""

    def __init__(self, scene, gateway):
        """Set up a scene."""
        self._scene = scene
        self.gateway = gateway

    async def async_added_to_opp(self):
        """Subscribe to sensors events."""
        self.gateway.deconz_ids[self.entity_id] = self._scene.deconz_id

    async def async_will_remove_from_opp(self) -> None:
        """Disconnect scene object when removed."""
        del self.gateway.deconz_ids[self.entity_id]
        self._scene = None

    async def async_activate(self, **kwargs: Any) -> None:
        """Activate the scene."""
        await self._scene.async_set_state({})

    @property
    def name(self):
        """Return the name of the scene."""
        return self._scene.full_name
