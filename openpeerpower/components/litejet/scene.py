"""Support for LiteJet scenes."""
from typing import Any

from openpeerpower.components import litejet
from openpeerpower.components.scene import Scene

ATTR_NUMBER = "number"


def setup_platform.opp, config, add_entities, discovery_info=None):
    """Set up scenes for the LiteJet platform."""
    litejet_ =.opp.data["litejet_system"]

    devices = []
    for i in litejet_.scenes():
        name = litejet_.get_scene_name(i)
        if not litejet.is_ignored.opp, name):
            devices.append(LiteJetScene(litejet_, i, name))
    add_entities(devices)


class LiteJetScene(Scene):
    """Representation of a single LiteJet scene."""

    def __init__(self, lj, i, name):
        """Initialize the scene."""
        self._lj = lj
        self._index = i
        self._name = name

    @property
    def name(self):
        """Return the name of the scene."""
        return self._name

    @property
    def device_state_attributes(self):
        """Return the device-specific state attributes."""
        return {ATTR_NUMBER: self._index}

    def activate(self, **kwargs: Any) -> None:
        """Activate the scene."""
        self._lj.activate_scene(self._index)
