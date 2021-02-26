"""Support for Vanderbilt (formerly Siemens) SPC alarm systems."""
import logging

from pyspcwebgw import SpcWebGateway
from pyspcwebgw.area import Area
from pyspcwebgw.zone import Zone
import voluptuous as vol

from openpeerpower.helpers import aiohttp_client, discovery
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.dispatcher import async_dispatcher_send

_LOGGER = logging.getLogger(__name__)

CONF_WS_URL = "ws_url"
CONF_API_URL = "api_url"

DOMAIN = "spc"
DATA_API = "spc_api"

SIGNAL_UPDATE_ALARM = "spc_update_alarm_{}"
SIGNAL_UPDATE_SENSOR = "spc_update_sensor_{}"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_WS_URL): cv.string,
                vol.Required(CONF_API_URL): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Set up the SPC component."""

    async def async_upate_callback(spc_object):

        if isinstance(spc_object, Area):
            async_dispatcher_send(opp, SIGNAL_UPDATE_ALARM.format(spc_object.id))
        elif isinstance(spc_object, Zone):
            async_dispatcher_send(opp, SIGNAL_UPDATE_SENSOR.format(spc_object.id))

    session = aiohttp_client.async_get_clientsession(opp)

    spc = SpcWebGateway(
        loop=opp.loop,
        session=session,
        api_url=config[DOMAIN].get(CONF_API_URL),
        ws_url=config[DOMAIN].get(CONF_WS_URL),
        async_callback=async_upate_callback,
    )

    opp.data[DATA_API] = spc

    if not await spc.async_load_parameters():
        _LOGGER.error("Failed to load area/zone information from SPC")
        return False

    # add sensor devices for each zone (typically motion/fire/door sensors)
    opp.async_create_task(
        discovery.async_load_platform(opp, "binary_sensor", DOMAIN, {}, config)
    )

    # create a separate alarm panel for each area
    opp.async_create_task(
        discovery.async_load_platform(opp, "alarm_control_panel", DOMAIN, {}, config)
    )

    # start listening for incoming events over websocket
    spc.start()

    return True
