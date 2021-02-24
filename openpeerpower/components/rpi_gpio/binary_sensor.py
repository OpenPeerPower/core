"""Support for binary sensor using RPi GPIO."""
import voluptuous as vol

from openpeerpower.components import rpi_gpio
from openpeerpower.components.binary_sensor import PLATFORM_SCHEMA, BinarySensorEntity
from openpeerpower.const import DEVICE_DEFAULT_NAME
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.reload import setup_reload_service

from . import DOMAIN, PLATFORMS

CONF_BOUNCETIME = "bouncetime"
CONF_INVERT_LOGIC = "invert_logic"
CONF_PORTS = "ports"
CONF_PULL_MODE = "pull_mode"

DEFAULT_BOUNCETIME = 50
DEFAULT_INVERT_LOGIC = False
DEFAULT_PULL_MODE = "UP"

_SENSORS_SCHEMA = vol.Schema({cv.positive_int: cv.string})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_PORTS): _SENSORS_SCHEMA,
        vol.Optional(CONF_BOUNCETIME, default=DEFAULT_BOUNCETIME): cv.positive_int,
        vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
        vol.Optional(CONF_PULL_MODE, default=DEFAULT_PULL_MODE): cv.string,
    }
)


def setup_platform(opp, config, add_entities, discovery_info=None):
    """Set up the Raspberry PI GPIO devices."""
    setup_reload_service(opp, DOMAIN, PLATFORMS)

    pull_mode = config.get(CONF_PULL_MODE)
    bouncetime = config.get(CONF_BOUNCETIME)
    invert_logic = config.get(CONF_INVERT_LOGIC)

    binary_sensors = []
    ports = config.get("ports")
    for port_num, port_name in ports.items():
        binary_sensors.append(
            RPiGPIOBinarySensor(
                port_name, port_num, pull_mode, bouncetime, invert_logic
            )
        )
    add_entities(binary_sensors, True)


class RPiGPIOBinarySensor(BinarySensorEntity):
    """Represent a binary sensor that uses Raspberry Pi GPIO."""

    def __init__(self, name, port, pull_mode, bouncetime, invert_logic):
        """Initialize the RPi binary sensor."""
        self._name = name or DEVICE_DEFAULT_NAME
        self._port = port
        self._pull_mode = pull_mode
        self._bouncetime = bouncetime
        self._invert_logic = invert_logic
        self._state = None

        rpi_gpio.setup_input(self._port, self._pull_mode)

        def read_gpio(port):
            """Read state from GPIO."""
            self._state = rpi_gpio.read_input(self._port)
            self.schedule_update_op_state()

        rpi_gpio.edge_detect(self._port, read_gpio, self._bouncetime)

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return the state of the entity."""
        return self._state != self._invert_logic

    def update(self):
        """Update the GPIO state."""
        self._state = rpi_gpio.read_input(self._port)
