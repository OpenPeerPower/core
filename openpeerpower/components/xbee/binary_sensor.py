"""Support for Zigbee binary sensors."""
import voluptuous as vol

from openpeerpower.components.binary_sensor import BinarySensorEntity

from . import PLATFORM_SCHEMA, XBeeDigitalIn, XBeeDigitalInConfig
from .const import CONF_ON_STATE, DOMAIN, STATES

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({vol.Optional(CONF_ON_STATE): vol.In(STATES)})


def setup_platform(opp, config, add_entities, discovery_info=None):
    """Set up the XBee Zigbee binary sensor platform."""
    zigbee_device = opp.data[DOMAIN]
    add_entities([XBeeBinarySensor(XBeeDigitalInConfig(config), zigbee_device)], True)


class XBeeBinarySensor(XBeeDigitalIn, BinarySensorEntity):
    """Use XBeeDigitalIn as binary sensor."""
