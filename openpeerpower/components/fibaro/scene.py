"""Support for Fibaro scenes."""
from typing import Any

from openpeerpower.components.scene import Scene

from . import FIBARO_DEVICES, FibaroDevice


async def async_setup_platform(opp, config, async_add_entities, discovery_info=None):
    """Perform the setup for Fibaro scenes."""
    if discovery_info is None:
        return

    async_add_entities(
        [FibaroScene(scene) for scene in opp.data[FIBARO_DEVICES]["scene"]], True
    )


class FibaroScene(FibaroDevice, Scene):
    """Representation of a Fibaro scene entity."""

    def activate(self, **kwargs: Any) -> None:
        """Activate the scene."""
        self.fibaro_device.start()
