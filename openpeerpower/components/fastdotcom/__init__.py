"""Support for testing internet speed via Fast.com."""
from datetime import timedelta
import logging

from fastdotcom import fast_com
import voluptuous as vol

from openpeerpower.const import CONF_SCAN_INTERVAL
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.discovery import async_load_platform
from openpeerpower.helpers.dispatcher import dispatcher_send
from openpeerpower.helpers.event import async_track_time_interval

DOMAIN = "fastdotcom"
DATA_UPDATED = f"{DOMAIN}_data_updated"

_LOGGER = logging.getLogger(__name__)

CONF_MANUAL = "manual"

DEFAULT_INTERVAL = timedelta(hours=1)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_INTERVAL): vol.All(
                    cv.time_period, cv.positive_timedelta
                ),
                vol.Optional(CONF_MANUAL, default=False): cv.boolean,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Set up the Fast.com component."""
    conf = config[DOMAIN]
    data = opp.data[DOMAIN] = SpeedtestData(opp)

    if not conf[CONF_MANUAL]:
        async_track_time_interval(opp, data.update, conf[CONF_SCAN_INTERVAL])

    def update(call=None):
        """Service call to manually update the data."""
        data.update()

    opp.services.async_register(DOMAIN, "speedtest", update)

    opp.async_create_task(async_load_platform(opp, "sensor", DOMAIN, {}, config))

    return True


class SpeedtestData:
    """Get the latest data from fast.com."""

    def __init__(self, opp):
        """Initialize the data object."""
        self.data = None
        self._opp = opp

    def update(self, now=None):
        """Get the latest data from fast.com."""

        _LOGGER.debug("Executing fast.com speedtest")
        self.data = {"download": fast_com()}
        dispatcher_send(self._opp, DATA_UPDATED)
