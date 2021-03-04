"""The ViCare integration."""
import enum
import logging

from PyViCare.PyViCareDevice import Device
from PyViCare.PyViCareGazBoiler import GazBoiler
from PyViCare.PyViCareHeatPump import HeatPump
import voluptuous as vol

from openpeerpower.const import (
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from openpeerpower.helpers import discovery
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.storage import STORAGE_DIR

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["climate", "sensor", "binary_sensor", "water_heater"]

DOMAIN = "vicare"
PYVICARE_ERROR = "error"
VICARE_API = "api"
VICARE_NAME = "name"
VICARE_HEATING_TYPE = "heating_type"

CONF_CIRCUIT = "circuit"
CONF_HEATING_TYPE = "heating_type"
DEFAULT_HEATING_TYPE = "generic"


class HeatingType(enum.Enum):
    # pylint: disable=invalid-name
    """Possible options for heating type."""

    generic = "generic"
    gas = "gas"
    heatpump = "heatpump"


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL, default=60): vol.All(
                    cv.time_period, lambda value: value.total_seconds()
                ),
                vol.Optional(CONF_CIRCUIT): int,
                vol.Optional(CONF_NAME, default="ViCare"): cv.string,
                vol.Optional(CONF_HEATING_TYPE, default=DEFAULT_HEATING_TYPE): cv.enum(
                    HeatingType
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(opp, config):
    """Create the ViCare component."""
    conf = config[DOMAIN]
    params = {"token_file": opp.config.path(STORAGE_DIR, "vicare_token.save")}
    if conf.get(CONF_CIRCUIT) is not None:
        params["circuit"] = conf[CONF_CIRCUIT]

    params["cacheDuration"] = conf.get(CONF_SCAN_INTERVAL)

    heating_type = conf[CONF_HEATING_TYPE]

    try:
        if heating_type == HeatingType.gas:
            vicare_api = GazBoiler(conf[CONF_USERNAME], conf[CONF_PASSWORD], **params)
        elif heating_type == HeatingType.heatpump:
            vicare_api = HeatPump(conf[CONF_USERNAME], conf[CONF_PASSWORD], **params)
        else:
            vicare_api = Device(conf[CONF_USERNAME], conf[CONF_PASSWORD], **params)
    except AttributeError:
        _LOGGER.error(
            "Failed to create PyViCare API client. Please check your credentials"
        )
        return False

    opp.data[DOMAIN] = {}
    opp.data[DOMAIN][VICARE_API] = vicare_api
    opp.data[DOMAIN][VICARE_NAME] = conf[CONF_NAME]
    opp.data[DOMAIN][VICARE_HEATING_TYPE] = heating_type

    for platform in PLATFORMS:
        discovery.load_platform(opp, platform, DOMAIN, {}, config)

    return True
