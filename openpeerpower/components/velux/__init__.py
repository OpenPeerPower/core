"""Support for VELUX KLF 200 devices."""
import logging

from pyvlx import PyVLX, PyVLXException
import voluptuous as vol

from openpeerpower.const import CONF_HOST, CONF_PASSWORD, EVENT_OPENPEERPOWER_STOP
from openpeerpower.helpers import discovery
import openpeerpower.helpers.config_validation as cv

DOMAIN = "velux"
DATA_VELUX = "data_velux"
PLATFORMS = ["cover", "scene"]
_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {vol.Required(CONF_HOST): cv.string, vol.Required(CONF_PASSWORD): cv.string}
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Set up the velux component."""
    try:
        opp.data[DATA_VELUX] = VeluxModule(opp, config[DOMAIN])
        opp.data[DATA_VELUX].setup()
        await opp.data[DATA_VELUX].async_start()

    except PyVLXException as ex:
        _LOGGER.exception("Can't connect to velux interface: %s", ex)
        return False

    for platform in PLATFORMS:
        opp.async_create_task(
            discovery.async_load_platform(opp, platform, DOMAIN, {}, config)
        )
    return True


class VeluxModule:
    """Abstraction for velux component."""

    def __init__(self, opp, domain_config):
        """Initialize for velux component."""
        self.pyvlx = None
        self._opp = opp
        self._domain_config = domain_config

    def setup(self):
        """Velux component setup."""

        async def on_opp_stop(event):
            """Close connection when opp stops."""
            _LOGGER.debug("Velux interface terminated")
            await self.pyvlx.disconnect()

        async def async_reboot_gateway(service_call):
            await self.pyvlx.reboot_gateway()

        self._opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, on_opp_stop)
        host = self._domain_config.get(CONF_HOST)
        password = self._domain_config.get(CONF_PASSWORD)
        self.pyvlx = PyVLX(host=host, password=password)

        self._opp.services.async_register(
            DOMAIN, "reboot_gateway", async_reboot_gateway
        )

    async def async_start(self):
        """Start velux component."""
        _LOGGER.debug("Velux interface started")
        await self.pyvlx.load_scenes()
        await self.pyvlx.load_nodes()
