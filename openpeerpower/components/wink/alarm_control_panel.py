"""Support Wink alarm control panels."""
import pywink

import openpeerpower.components.alarm_control_panel as alarm
from openpeerpower.components.alarm_control_panel.const import (
    SUPPORT_ALARM_ARM_AWAY,
    SUPPORT_ALARM_ARM_HOME,
)
from openpeerpower.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_DISARMED,
)

from . import DOMAIN, WinkDevice

STATE_ALARM_PRIVACY = "Private"


def setup_platform(opp, config, add_entities, discovery_info=None):
    """Set up the Wink platform."""

    for camera in pywink.get_cameras():
        # get_cameras returns multiple device types.
        # Only add those that aren't sensors.
        try:
            camera.capability()
        except AttributeError:
            _id = camera.object_id() + camera.name()
            if _id not in opp.data[DOMAIN]["unique_ids"]:
                add_entities([WinkCameraDevice(camera, opp)])


class WinkCameraDevice(WinkDevice, alarm.AlarmControlPanelEntity):
    """Representation a Wink camera alarm."""

    async def async_added_to_opp(self):
        """Call when entity is added to opp."""
        self.opp.data[DOMAIN]["entities"]["alarm_control_panel"].append(self)

    @property
    def state(self):
        """Return the state of the device."""
        wink_state = self.wink.state()
        if wink_state == "away":
            state = STATE_ALARM_ARMED_AWAY
        elif wink_state == "home":
            state = STATE_ALARM_DISARMED
        elif wink_state == "night":
            state = STATE_ALARM_ARMED_HOME
        else:
            state = None
        return state

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return SUPPORT_ALARM_ARM_HOME | SUPPORT_ALARM_ARM_AWAY

    def alarm_disarm(self, code=None):
        """Send disarm command."""
        self.wink.set_mode("home")

    def alarm_arm_home(self, code=None):
        """Send arm home command."""
        self.wink.set_mode("night")

    def alarm_arm_away(self, code=None):
        """Send arm away command."""
        self.wink.set_mode("away")

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {"private": self.wink.private()}
