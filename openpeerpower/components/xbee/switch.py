"""Support for XBee Zigbee switches."""
import voluptuous as vol

from openpeerpower.components.switch import SwitchEntity

from . import PLATFORM_SCHEMA, XBeeDigitalOut, XBeeDigitalOutConfig
from .const import CONF_ON_STATE, DOMAIN, STATES

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({vol.Optional(CONF_ON_STATE): vol.In(STATES)})


def setup_platform(opp, config, add_entities, discovery_info=None):
    """Set up the XBee Zigbee switch platform."""
    zigbee_device = opp.data[DOMAIN]
    add_entities([XBeeSwitch(XBeeDigitalOutConfig(config), zigbee_device)])


class XBeeSwitch(XBeeDigitalOut, SwitchEntity):
    """Representation of a XBee Zigbee Digital Out device."""
