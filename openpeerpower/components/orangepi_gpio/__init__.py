"""Support for controlling GPIO pins of a Orange Pi."""

import logging

from OPi import GPIO

from openpeerpower.const import EVENT_OPENPEERPOWER_START, EVENT_OPENPEERPOWER_STOP

from .const import PIN_MODES

_LOGGER = logging.getLogger(__name__)

DOMAIN = "orangepi_gpio"


async def async_setup.opp, config):
    """Set up the Orange Pi GPIO component."""

    def cleanup_gpio(event):
        """Stuff to do before stopping."""
        GPIO.cleanup()

    def prepare_gpio(event):
        """Stuff to do when Open Peer Power starts."""
       .opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, cleanup_gpio)

   .opp.bus.async_listen_once(EVENT_OPENPEERPOWER_START, prepare_gpio)
    return True


def setup_mode(mode):
    """Set GPIO pin mode."""
    _LOGGER.debug("Setting GPIO pin mode as %s", PIN_MODES[mode])
    GPIO.setmode(PIN_MODES[mode])


def setup_input(port):
    """Set up a GPIO as input."""
    _LOGGER.debug("Setting up GPIO pin %i as input", port)
    GPIO.setup(port, GPIO.IN)


def read_input(port):
    """Read a value from a GPIO."""
    _LOGGER.debug("Reading GPIO pin %i", port)
    return GPIO.input(port)


def edge_detect(port, event_callback):
    """Add detection for RISING and FALLING events."""
    _LOGGER.debug("Add callback for GPIO pin %i", port)
    GPIO.add_event_detect(port, GPIO.BOTH, callback=event_callback)
