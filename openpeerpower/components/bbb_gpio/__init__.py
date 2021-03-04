"""Support for controlling GPIO pins of a Beaglebone Black."""
from Adafruit_BBIO import GPIO  # pylint: disable=import-error

from openpeerpower.const import EVENT_OPENPEERPOWER_START, EVENT_OPENPEERPOWER_STOP

DOMAIN = "bbb_gpio"


def setup(opp, config):
    """Set up the BeagleBone Black GPIO component."""

    def cleanup_gpio(event):
        """Stuff to do before stopping."""
        GPIO.cleanup()

    def prepare_gpio(event):
        """Stuff to do when Open Peer Power starts."""
        opp.bus.listen_once(EVENT_OPENPEERPOWER_STOP, cleanup_gpio)

    opp.bus.listen_once(EVENT_OPENPEERPOWER_START, prepare_gpio)
    return True


def setup_output(pin):
    """Set up a GPIO as output."""

    GPIO.setup(pin, GPIO.OUT)


def setup_input(pin, pull_mode):
    """Set up a GPIO as input."""

    GPIO.setup(pin, GPIO.IN, GPIO.PUD_DOWN if pull_mode == "DOWN" else GPIO.PUD_UP)


def write_output(pin, value):
    """Write a value to a GPIO."""

    GPIO.output(pin, value)


def read_input(pin):
    """Read a value from a GPIO."""

    return GPIO.input(pin) is GPIO.HIGH


def edge_detect(pin, event_callback, bounce):
    """Add detection for RISING and FALLING events."""

    GPIO.add_event_detect(pin, GPIO.BOTH, callback=event_callback, bouncetime=bounce)
