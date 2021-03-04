"""Support for MyChevy."""
from datetime import timedelta
import logging
import threading
import time

import mychevy.mychevy as mc
import voluptuous as vol

from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME
from openpeerpower.helpers import config_validation as cv, discovery
from openpeerpower.util import Throttle

DOMAIN = "mychevy"
UPDATE_TOPIC = DOMAIN
ERROR_TOPIC = f"{DOMAIN}_error"

MYCHEVY_SUCCESS = "success"
MYCHEVY_ERROR = "error"

NOTIFICATION_ID = "mychevy_website_notification"
NOTIFICATION_TITLE = "MyChevy website status"

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=30)
ERROR_SLEEP_TIME = timedelta(minutes=30)

CONF_COUNTRY = "country"
DEFAULT_COUNTRY = "us"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_COUNTRY, default=DEFAULT_COUNTRY): vol.All(
                    cv.string, vol.In(["us", "ca"])
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


class EVSensorConfig:
    """The EV sensor configuration."""

    def __init__(
        self, name, attr, unit_of_measurement=None, icon=None, extra_attrs=None
    ):
        """Create new sensor configuration."""
        self.name = name
        self.attr = attr
        self.extra_attrs = extra_attrs or []
        self.unit_of_measurement = unit_of_measurement
        self.icon = icon


class EVBinarySensorConfig:
    """The EV binary sensor configuration."""

    def __init__(self, name, attr, device_class=None):
        """Create new binary sensor configuration."""
        self.name = name
        self.attr = attr
        self.device_class = device_class


def setup(opp, base_config):
    """Set up the mychevy component."""
    config = base_config.get(DOMAIN)

    email = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    country = config.get(CONF_COUNTRY)
    opp.data[DOMAIN] = MyChevyHub(
        mc.MyChevy(email, password, country), opp, base_config
    )
    opp.data[DOMAIN].start()

    return True


class MyChevyHub(threading.Thread):
    """MyChevy Hub.

    Connecting to the mychevy website is done through a selenium
    webscraping process. That can only run synchronously. In order to
    prevent blocking of other parts of Open Peer Power the architecture
    launches a polling loop in a thread.

    When new data is received, sensors are updated, and opp is
    signaled that there are updates. Sensors are not created until the
    first update, which will be 60 - 120 seconds after the platform
    starts.
    """

    def __init__(self, client, opp, opp_config):
        """Initialize MyChevy Hub."""
        super().__init__()
        self._client = client
        self.opp = opp
        self.opp_config = opp_config
        self.cars = []
        self.status = None
        self.ready = False

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update sensors from mychevy website.

        This is a synchronous polling call that takes a very long time
        (like 2 to 3 minutes long time)

        """
        self._client.login()
        self._client.get_cars()
        self.cars = self._client.cars
        if self.ready is not True:
            discovery.load_platform(self.opp, "sensor", DOMAIN, {}, self.opp_config)
            discovery.load_platform(
                self.opp, "binary_sensor", DOMAIN, {}, self.opp_config
            )
            self.ready = True
        self.cars = self._client.update_cars()

    def get_car(self, vid):
        """Compatibility to work with one car."""
        if self.cars:
            for car in self.cars:
                if car.vid == vid:
                    return car
        return None

    def run(self):
        """Thread run loop."""
        # We add the status device first outside of the loop

        # And then busy wait on threads
        while True:
            try:
                _LOGGER.info("Starting mychevy loop")
                self.update()
                self.opp.helpers.dispatcher.dispatcher_send(UPDATE_TOPIC)
                time.sleep(MIN_TIME_BETWEEN_UPDATES.seconds)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception(
                    "Error updating mychevy data. "
                    "This probably means the OnStar link is down again"
                )
                self.opp.helpers.dispatcher.dispatcher_send(ERROR_TOPIC)
                time.sleep(ERROR_SLEEP_TIME.seconds)
