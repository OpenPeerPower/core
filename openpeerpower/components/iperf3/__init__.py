"""Support for Iperf3 network measurement tool."""
from datetime import timedelta
import logging

import iperf3
import voluptuous as vol

from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.const import (
    CONF_HOST,
    CONF_HOSTS,
    CONF_MONITORED_CONDITIONS,
    CONF_PORT,
    CONF_PROTOCOL,
    CONF_SCAN_INTERVAL,
    DATA_RATE_MEGABITS_PER_SECOND,
)
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.discovery import async_load_platform
from openpeerpower.helpers.dispatcher import dispatcher_send
from openpeerpower.helpers.event import async_track_time_interval

DOMAIN = "iperf3"
DATA_UPDATED = f"{DOMAIN}_data_updated"

_LOGGER = logging.getLogger(__name__)

CONF_DURATION = "duration"
CONF_PARALLEL = "parallel"
CONF_MANUAL = "manual"

DEFAULT_DURATION = 10
DEFAULT_PORT = 5201
DEFAULT_PARALLEL = 1
DEFAULT_PROTOCOL = "tcp"
DEFAULT_INTERVAL = timedelta(minutes=60)

ATTR_DOWNLOAD = "download"
ATTR_UPLOAD = "upload"
ATTR_VERSION = "Version"
ATTR_HOST = "host"

SENSOR_TYPES = {
    ATTR_DOWNLOAD: [ATTR_DOWNLOAD.capitalize(), DATA_RATE_MEGABITS_PER_SECOND],
    ATTR_UPLOAD: [ATTR_UPLOAD.capitalize(), DATA_RATE_MEGABITS_PER_SECOND],
}

PROTOCOLS = ["tcp", "udp"]

HOST_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_DURATION, default=DEFAULT_DURATION): vol.Range(5, 10),
        vol.Optional(CONF_PARALLEL, default=DEFAULT_PARALLEL): vol.Range(1, 20),
        vol.Optional(CONF_PROTOCOL, default=DEFAULT_PROTOCOL): vol.In(PROTOCOLS),
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOSTS): vol.All(cv.ensure_list, [HOST_CONFIG_SCHEMA]),
                vol.Optional(
                    CONF_MONITORED_CONDITIONS, default=list(SENSOR_TYPES)
                ): vol.All(cv.ensure_list, [vol.In(list(SENSOR_TYPES))]),
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_INTERVAL): vol.All(
                    cv.time_period, cv.positive_timedelta
                ),
                vol.Optional(CONF_MANUAL, default=False): cv.boolean,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

SERVICE_SCHEMA = vol.Schema({vol.Optional(ATTR_HOST, default=None): cv.string})


async def async_setup(opp, config):
    """Set up the iperf3 component."""
    opp.data[DOMAIN] = {}

    conf = config[DOMAIN]
    for host in conf[CONF_HOSTS]:
        data = opp.data[DOMAIN][host[CONF_HOST]] = Iperf3Data(opp, host)

        if not conf[CONF_MANUAL]:
            async_track_time_interval(opp, data.update, conf[CONF_SCAN_INTERVAL])

    def update(call):
        """Service call to manually update the data."""
        called_host = call.data[ATTR_HOST]
        if called_host in opp.data[DOMAIN]:
            opp.data[DOMAIN][called_host].update()
        else:
            for iperf3_host in opp.data[DOMAIN].values():
                iperf3_host.update()

    opp.services.async_register(DOMAIN, "speedtest", update, schema=SERVICE_SCHEMA)

    opp.async_create_task(
        async_load_platform(
            opp, SENSOR_DOMAIN, DOMAIN, conf[CONF_MONITORED_CONDITIONS], config
        )
    )

    return True


class Iperf3Data:
    """Get the latest data from iperf3."""

    def __init__(self, opp, host):
        """Initialize the data object."""
        self._opp = opp
        self._host = host
        self.data = {ATTR_DOWNLOAD: None, ATTR_UPLOAD: None, ATTR_VERSION: None}

    def create_client(self):
        """Create a new iperf3 client to use for measurement."""
        client = iperf3.Client()
        client.duration = self._host[CONF_DURATION]
        client.server_hostname = self._host[CONF_HOST]
        client.port = self._host[CONF_PORT]
        client.num_streams = self._host[CONF_PARALLEL]
        client.protocol = self._host[CONF_PROTOCOL]
        client.verbose = False
        return client

    @property
    def protocol(self):
        """Return the protocol used for this connection."""
        return self._host[CONF_PROTOCOL]

    @property
    def host(self):
        """Return the host connected to."""
        return self._host[CONF_HOST]

    @property
    def port(self):
        """Return the port on the host connected to."""
        return self._host[CONF_PORT]

    def update(self, now=None):
        """Get the latest data from iperf3."""
        if self.protocol == "udp":
            # UDP only have 1 way attribute
            result = self._run_test(ATTR_DOWNLOAD)
            self.data[ATTR_DOWNLOAD] = self.data[ATTR_UPLOAD] = getattr(
                result, "Mbps", None
            )
            self.data[ATTR_VERSION] = getattr(result, "version", None)
        else:
            result = self._run_test(ATTR_DOWNLOAD)
            self.data[ATTR_DOWNLOAD] = getattr(result, "received_Mbps", None)
            self.data[ATTR_VERSION] = getattr(result, "version", None)
            self.data[ATTR_UPLOAD] = getattr(
                self._run_test(ATTR_UPLOAD), "sent_Mbps", None
            )

        dispatcher_send(self._opp, DATA_UPDATED, self.host)

    def _run_test(self, test_type):
        """Run and return the iperf3 data."""
        client = self.create_client()
        client.reverse = test_type == ATTR_DOWNLOAD
        try:
            result = client.run()
        except (AttributeError, OSError, ValueError) as error:
            _LOGGER.error("Iperf3 error: %s", error)
            return None

        if result is not None and hasattr(result, "error") and result.error is not None:
            _LOGGER.error("Iperf3 error: %s", result.error)
            return None

        return result
