"""Support for Tahoma switches."""
import logging

from openpeerpower.components.switch import SwitchEntity
from openpeerpower.const import STATE_OFF, STATE_ON

from . import DOMAIN as TAHOMA_DOMAIN, TahomaDevice

_LOGGER = logging.getLogger(__name__)

ATTR_RSSI_LEVEL = "rssi_level"


def setup_platform(opp, config, add_entities, discovery_info=None):
    """Set up Tahoma switches."""
    if discovery_info is None:
        return
    controller = opp.data[TAHOMA_DOMAIN]["controller"]
    devices = []
    for switch in opp.data[TAHOMA_DOMAIN]["devices"]["switch"]:
        devices.append(TahomaSwitch(switch, controller))
    add_entities(devices, True)


class TahomaSwitch(TahomaDevice, SwitchEntity):
    """Representation a Tahoma Switch."""

    def __init__(self, tahoma_device, controller):
        """Initialize the switch."""
        super().__init__(tahoma_device, controller)
        self._state = STATE_OFF
        self._skip_update = False
        self._available = False

    def update(self):
        """Update method."""
        # Postpone the immediate state check for changes that take time.
        if self._skip_update:
            self._skip_update = False
            return

        self.controller.get_states([self.tahoma_device])

        if self.tahoma_device.type == "io:OnOffLightIOComponent":
            if self.tahoma_device.active_states.get("core:OnOffState") == "on":
                self._state = STATE_ON
            else:
                self._state = STATE_OFF

        if self.tahoma_device.type == "zwave:OnOffLightZWaveComponent":
            if self.tahoma_device.active_states.get("core:OnOffState") == "on":
                self._state = STATE_ON
            else:
                self._state = STATE_OFF

        # A RTS power socket doesn't have a feedback channel,
        # so we must assume the socket is available.
        if self.tahoma_device.type == "rts:OnOffRTSComponent":
            self._available = True
        elif self.tahoma_device.type == "zwave:OnOffLightZWaveComponent":
            self._available = True
        else:
            self._available = bool(
                self.tahoma_device.active_states.get("core:StatusState") == "available"
            )

        _LOGGER.debug("Update %s, state: %s", self._name, self._state)

    @property
    def device_class(self):
        """Return the class of the device."""
        if self.tahoma_device.type == "rts:GarageDoor4TRTSComponent":
            return "garage"
        return None

    def turn_on(self, **kwargs):
        """Send the on command."""
        _LOGGER.debug("Turn on: %s", self._name)
        if self.tahoma_device.type == "rts:GarageDoor4TRTSComponent":
            self.toggle()
        else:
            self.apply_action("on")
            self._skip_update = True
            self._state = STATE_ON

    def turn_off(self, **kwargs):
        """Send the off command."""
        _LOGGER.debug("Turn off: %s", self._name)
        if self.tahoma_device.type == "rts:GarageDoor4TRTSComponent":
            return

        self.apply_action("off")
        self._skip_update = True
        self._state = STATE_OFF

    def toggle(self, **kwargs):
        """Click the switch."""
        self.apply_action("cycle")

    @property
    def is_on(self):
        """Get whether the switch is in on state."""
        if self.tahoma_device.type == "rts:GarageDoor4TRTSComponent":
            return False
        return bool(self._state == STATE_ON)

    @property
    def extra_state_attributes(self):
        """Return the device state attributes."""
        attr = {}
        super_attr = super().extra_state_attributes
        if super_attr is not None:
            attr.update(super_attr)

        if "core:RSSILevelState" in self.tahoma_device.active_states:
            attr[ATTR_RSSI_LEVEL] = self.tahoma_device.active_states[
                "core:RSSILevelState"
            ]
        return attr

    @property
    def available(self):
        """Return True if entity is available."""
        return self._available
