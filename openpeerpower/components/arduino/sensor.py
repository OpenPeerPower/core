"""Support for getting information from Arduino pins."""
import voluptuous as vol

from openpeerpower.components.sensor import PLATFORM_SCHEMA
from openpeerpower.const import CONF_NAME
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.entity import Entity

from . import DOMAIN

CONF_PINS = "pins"
CONF_TYPE = "analog"

PIN_SCHEMA = vol.Schema({vol.Required(CONF_NAME): cv.string})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_PINS): vol.Schema({cv.positive_int: PIN_SCHEMA})}
)


def setup_platform(opp, config, add_entities, discovery_info=None):
    """Set up the Arduino platform."""
    board = opp.data[DOMAIN]

    pins = config[CONF_PINS]

    sensors = []
    for pinnum, pin in pins.items():
        sensors.append(ArduinoSensor(pin.get(CONF_NAME), pinnum, CONF_TYPE, board))
    add_entities(sensors)


class ArduinoSensor(Entity):
    """Representation of an Arduino Sensor."""

    def __init__(self, name, pin, pin_type, board):
        """Initialize the sensor."""
        self._pin = pin
        self._name = name
        self.pin_type = pin_type
        self.direction = "in"
        self._value = None

        board.set_mode(self._pin, self.direction, self.pin_type)
        self._board = board

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._value

    @property
    def name(self):
        """Get the name of the sensor."""
        return self._name

    def update(self):
        """Get the latest value from the pin."""
        self._value = self._board.get_analog_inputs()[self._pin][1]
