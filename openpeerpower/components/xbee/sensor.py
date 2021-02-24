"""Support for XBee Zigbee sensors."""
from binascii import hexlify
import logging

import voluptuous as vol
from xbee_helper.exceptions import ZigBeeException, ZigBeeTxFailure

from openpeerpower.const import CONF_TYPE, TEMP_CELSIUS
from openpeerpower.helpers.entity import Entity

from . import DOMAIN, PLATFORM_SCHEMA, XBeeAnalogIn, XBeeAnalogInConfig, XBeeConfig

_LOGGER = logging.getLogger(__name__)

CONF_MAX_VOLTS = "max_volts"

DEFAULT_VOLTS = 1.2
TYPES = ["analog", "temperature"]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(TYPES),
        vol.Optional(CONF_MAX_VOLTS, default=DEFAULT_VOLTS): vol.Coerce(float),
    }
)


def setup_platform(opp, config, add_entities, discovery_info=None):
    """Set up the XBee Zigbee platform.

    Uses the 'type' config value to work out which type of Zigbee sensor we're
    dealing with and instantiates the relevant classes to handle it.
    """
    zigbee_device = opp.data[DOMAIN]
    typ = config.get(CONF_TYPE)

    try:
        sensor_class, config_class = TYPE_CLASSES[typ]
    except KeyError:
        _LOGGER.exception("Unknown XBee Zigbee sensor type: %s", typ)
        return

    add_entities([sensor_class(config_class(config), zigbee_device)], True)


class XBeeTemperatureSensor(Entity):
    """Representation of XBee Pro temperature sensor."""

    def __init__(self, config, device):
        """Initialize the sensor."""
        self._config = config
        self._device = device
        self._temp = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._config.name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._temp

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement the value is expressed in."""
        return TEMP_CELSIUS

    def update(self):
        """Get the latest data."""
        try:
            self._temp = self._device.get_temperature(self._config.address)
        except ZigBeeTxFailure:
            _LOGGER.warning(
                "Transmission failure when attempting to get sample from "
                "Zigbee device at address: %s",
                hexlify(self._config.address),
            )
        except ZigBeeException as exc:
            _LOGGER.exception("Unable to get sample from Zigbee device: %s", exc)


# This must be below the classes to which it refers.
TYPE_CLASSES = {
    "temperature": (XBeeTemperatureSensor, XBeeConfig),
    "analog": (XBeeAnalogIn, XBeeAnalogInConfig),
}
