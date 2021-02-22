"""Support for the MAX! Cube LAN Gateway."""
import logging
from socket import timeout
from threading import Lock
import time

from maxcube.connection import MaxCubeConnection
from maxcube.cube import MaxCube
import voluptuous as vol

from openpeerpower.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.discovery import load_platform

_LOGGER = logging.getLogger(__name__)

DEFAULT_PORT = 62910
DOMAIN = "maxcube"

DATA_KEY = "maxcube"

NOTIFICATION_ID = "maxcube_notification"
NOTIFICATION_TITLE = "Max!Cube gateway setup"

CONF_GATEWAYS = "gateways"

CONFIG_GATEWAY = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_SCAN_INTERVAL, default=300): cv.time_period,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_GATEWAYS, default={}): vol.All(
                    cv.ensure_list, [CONFIG_GATEWAY]
                )
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(opp, config):
    """Establish connection to MAX! Cube."""

    if DATA_KEY not in.opp.data:
        opp.data[DATA_KEY] = {}

    connection_failed = 0
    gateways = config[DOMAIN][CONF_GATEWAYS]
    for gateway in gateways:
        host = gateway[CONF_HOST]
        port = gateway[CONF_PORT]
        scan_interval = gateway[CONF_SCAN_INTERVAL].total_seconds()

        try:
            cube = MaxCube(MaxCubeConnection(host, port))
            opp.data[DATA_KEY][host] = MaxCubeHandle(cube, scan_interval)
        except timeout as ex:
            _LOGGER.error("Unable to connect to Max!Cube gateway: %s", str(ex))
            opp.components.persistent_notification.create(
                f"Error: {ex}<br />You will need to restart Open Peer Power after fixing.",
                title=NOTIFICATION_TITLE,
                notification_id=NOTIFICATION_ID,
            )
            connection_failed += 1

    if connection_failed >= len(gateways):
        return False

    load_platform.opp, "climate", DOMAIN, {}, config)
    load_platform.opp, "binary_sensor", DOMAIN, {}, config)

    return True


class MaxCubeHandle:
    """Keep the cube instance in one place and centralize the update."""

    def __init__(self, cube, scan_interval):
        """Initialize the Cube Handle."""
        self.cube = cube
        self.scan_interval = scan_interval
        self.mutex = Lock()
        self._updatets = time.monotonic()

    def update(self):
        """Pull the latest data from the MAX! Cube."""
        # Acquire mutex to prevent simultaneous update from multiple threads
        with self.mutex:
            # Only update every update_interval
            if (time.monotonic() - self._updatets) >= self.scan_interval:
                _LOGGER.debug("Updating")

                try:
                    self.cube.update()
                except timeout:
                    _LOGGER.error("Max!Cube connection failed")
                    return False

                self._updatets = time.monotonic()
            else:
                _LOGGER.debug("Skipping update")
