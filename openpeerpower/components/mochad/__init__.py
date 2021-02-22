"""Support for CM15A/CM19A X10 Controller using mochad daemon."""
import logging
import threading

from pymochad import controller, exceptions
import voluptuous as vol

from openpeerpower.const import (
    CONF_HOST,
    CONF_PORT,
    EVENT_OPENPEERPOWER_START,
    EVENT_OPENPEERPOWER_STOP,
)
import openpeerpower.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

CONF_COMM_TYPE = "comm_type"

DOMAIN = "mochad"

REQ_LOCK = threading.Lock()

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_HOST, default="localhost"): cv.string,
                vol.Optional(CONF_PORT, default=1099): cv.port,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(opp, config):
    """Set up the mochad component."""
    conf = config[DOMAIN]
    host = conf.get(CONF_HOST)
    port = conf.get(CONF_PORT)

    try:
        mochad_controller = MochadCtrl(host, port)
    except exceptions.ConfigurationError:
        _LOGGER.exception()
        return False

    def stop_mochad(event):
        """Stop the Mochad service."""
        mochad_controller.disconnect()

    def start_mochad(event):
        """Start the Mochad service."""
        opp.bus.listen_once(EVENT_OPENPEERPOWER_STOP, stop_mochad)

    opp.bus.listen_once(EVENT_OPENPEERPOWER_START, start_mochad)
    opp.data[DOMAIN] = mochad_controller

    return True


class MochadCtrl:
    """Mochad controller."""

    def __init__(self, host, port):
        """Initialize a PyMochad controller."""
        super().__init__()
        self._host = host
        self._port = port

        self.ctrl = controller.PyMochad(server=self._host, port=self._port)

    @property
    def host(self):
        """Return the server where mochad is running."""
        return self._host

    @property
    def port(self):
        """Return the port mochad is running on."""
        return self._port

    def disconnect(self):
        """Close the connection to the mochad socket."""
        self.ctrl.socket.close()
