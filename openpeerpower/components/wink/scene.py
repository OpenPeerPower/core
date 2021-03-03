"""Support for Wink scenes."""
from typing import Any

import pywink

from openpeerpower.components.scene import Scene

from . import DOMAIN, WinkDevice


def setup_platform(opp, config, add_entities, discovery_info=None):
    """Set up the Wink platform."""

    for scene in pywink.get_scenes():
        _id = scene.object_id() + scene.name()
        if _id not in opp.data[DOMAIN]["unique_ids"]:
            add_entities([WinkScene(scene, opp)])


class WinkScene(WinkDevice, Scene):
    """Representation of a Wink shortcut/scene."""

    def __init__(self, wink, opp):
        """Initialize the Wink device."""
        super().__init__(wink, opp)
        opp.data[DOMAIN]["entities"]["scene"].append(self)

    async def async_added_to_opp(self):
        """Call when entity is added to opp."""
        self.opp.data[DOMAIN]["entities"]["scene"].append(self)

    def activate(self, **kwargs: Any) -> None:
        """Activate the scene."""
        self.wink.activate()
