"""Support for monitoring an AVM Fritz!Box router."""
from datetime import timedelta
import logging

from fritzconnection.core.exceptions import FritzConnectionException
from fritzconnection.lib.fritzstatus import FritzStatus
from requests.exceptions import RequestException
import voluptuous as vol

from openpeerpower.components.sensor import PLATFORM_SCHEMA
from openpeerpower.const import CONF_HOST, CONF_NAME, STATE_UNAVAILABLE
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.entity import Entity
from openpeerpower.util import Throttle

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "fritz_netmonitor"
DEFAULT_HOST = "169.254.1.1"  # This IP is valid for all FRITZ!Box routers.

ATTR_BYTES_RECEIVED = "bytes_received"
ATTR_BYTES_SENT = "bytes_sent"
ATTR_TRANSMISSION_RATE_UP = "transmission_rate_up"
ATTR_TRANSMISSION_RATE_DOWN = "transmission_rate_down"
ATTR_EXTERNAL_IP = "external_ip"
ATTR_IS_CONNECTED = "is_connected"
ATTR_IS_LINKED = "is_linked"
ATTR_MAX_BYTE_RATE_DOWN = "max_byte_rate_down"
ATTR_MAX_BYTE_RATE_UP = "max_byte_rate_up"
ATTR_UPTIME = "uptime"

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=5)

STATE_ONLINE = "online"
STATE_OFFLINE = "offline"

ICON = "mdi:web"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_HOST, default=DEFAULT_HOST): cv.string,
    }
)


def setup_platform(opp, config, add_entities, discovery_info=None):
    """Set up the FRITZ!Box monitor sensors."""
    name = config[CONF_NAME]
    host = config[CONF_HOST]

    try:
        fstatus = FritzStatus(address=host)
    except (ValueError, TypeError, FritzConnectionException):
        fstatus = None

    if fstatus is None:
        _LOGGER.error("Failed to establish connection to FRITZ!Box: %s", host)
        return 1
    _LOGGER.info("Successfully connected to FRITZ!Box")

    add_entities([FritzboxMonitorSensor(name, fstatus)], True)


class FritzboxMonitorSensor(Entity):
    """Implementation of a fritzbox monitor sensor."""

    def __init__(self, name, fstatus):
        """Initialize the sensor."""
        self._name = name
        self._fstatus = fstatus
        self._state = STATE_UNAVAILABLE
        self._is_linked = self._is_connected = None
        self._external_ip = self._uptime = None
        self._bytes_sent = self._bytes_received = None
        self._transmission_rate_up = None
        self._transmission_rate_down = None
        self._max_byte_rate_up = self._max_byte_rate_down = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name.rstrip()

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return ICON

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def state_attributes(self):
        """Return the device state attributes."""
        # Don't return attributes if FritzBox is unreachable
        if self._state == STATE_UNAVAILABLE:
            return {}
        return {
            ATTR_IS_LINKED: self._is_linked,
            ATTR_IS_CONNECTED: self._is_connected,
            ATTR_EXTERNAL_IP: self._external_ip,
            ATTR_UPTIME: self._uptime,
            ATTR_BYTES_SENT: self._bytes_sent,
            ATTR_BYTES_RECEIVED: self._bytes_received,
            ATTR_TRANSMISSION_RATE_UP: self._transmission_rate_up,
            ATTR_TRANSMISSION_RATE_DOWN: self._transmission_rate_down,
            ATTR_MAX_BYTE_RATE_UP: self._max_byte_rate_up,
            ATTR_MAX_BYTE_RATE_DOWN: self._max_byte_rate_down,
        }

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Retrieve information from the FritzBox."""
        try:
            self._is_linked = self._fstatus.is_linked
            self._is_connected = self._fstatus.is_connected
            self._external_ip = self._fstatus.external_ip
            self._uptime = self._fstatus.uptime
            self._bytes_sent = self._fstatus.bytes_sent
            self._bytes_received = self._fstatus.bytes_received
            transmission_rate = self._fstatus.transmission_rate
            self._transmission_rate_up = transmission_rate[0]
            self._transmission_rate_down = transmission_rate[1]
            self._max_byte_rate_up = self._fstatus.max_byte_rate[0]
            self._max_byte_rate_down = self._fstatus.max_byte_rate[1]
            self._state = STATE_ONLINE if self._is_connected else STATE_OFFLINE
        except RequestException as err:
            self._state = STATE_UNAVAILABLE
            _LOGGER.warning("Could not reach FRITZ!Box: %s", err)
