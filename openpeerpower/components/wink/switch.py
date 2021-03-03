"""Support for Wink switches."""
import pywink

from openpeerpower.helpers.entity import ToggleEntity

from . import DOMAIN, WinkDevice


def setup_platform(opp, config, add_entities, discovery_info=None):
    """Set up the Wink platform."""

    for switch in pywink.get_switches():
        _id = switch.object_id() + switch.name()
        if _id not in opp.data[DOMAIN]["unique_ids"]:
            add_entities([WinkToggleDevice(switch, opp)])
    for switch in pywink.get_powerstrips():
        _id = switch.object_id() + switch.name()
        if _id not in opp.data[DOMAIN]["unique_ids"]:
            add_entities([WinkToggleDevice(switch, opp)])
    for sprinkler in pywink.get_sprinklers():
        _id = sprinkler.object_id() + sprinkler.name()
        if _id not in opp.data[DOMAIN]["unique_ids"]:
            add_entities([WinkToggleDevice(sprinkler, opp)])
    for switch in pywink.get_binary_switch_groups():
        _id = switch.object_id() + switch.name()
        if _id not in opp.data[DOMAIN]["unique_ids"]:
            add_entities([WinkToggleDevice(switch, opp)])


class WinkToggleDevice(WinkDevice, ToggleEntity):
    """Representation of a Wink toggle device."""

    async def async_added_to_opp(self):
        """Call when entity is added to opp."""
        self.opp.data[DOMAIN]["entities"]["switch"].append(self)

    @property
    def is_on(self):
        """Return true if device is on."""
        return self.wink.state()

    def turn_on(self, **kwargs):
        """Turn the device on."""
        self.wink.set_state(True)

    def turn_off(self, **kwargs):
        """Turn the device off."""
        self.wink.set_state(False)

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        attributes = super().device_state_attributes
        try:
            event = self.wink.last_event()
            if event is not None:
                attributes["last_event"] = event
        except AttributeError:
            pass
        return attributes
