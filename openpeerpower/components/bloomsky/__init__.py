"""Support for BloomSky weather station."""
from datetime import timedelta
import logging

from aiohttp.hdrs import AUTHORIZATION
import requests
import voluptuous as vol

from openpeerpower.const import (
    CONF_API_KEY,
    HTTP_METHOD_NOT_ALLOWED,
    HTTP_OK,
    HTTP_UNAUTHORIZED,
)
from openpeerpower.helpers import discovery
import openpeerpower.helpers.config_validation as cv
from openpeerpower.util import Throttle

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["camera", "binary_sensor", "sensor"]

DOMAIN = "bloomsky"

# The BloomSky only updates every 5-8 minutes as per the API spec so there's
# no point in polling the API more frequently
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=300)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_API_KEY): cv.string})}, extra=vol.ALLOW_EXTRA
)


def setup(opp, config):
    """Set up the BloomSky integration."""
    api_key = config[DOMAIN][CONF_API_KEY]

    try:
        bloomsky = BloomSky(api_key, opp.config.units.is_metric)
    except RuntimeError:
        return False

    opp.data[DOMAIN] = bloomsky

    for platform in PLATFORMS:
        discovery.load_platform(opp, platform, DOMAIN, {}, config)

    return True


class BloomSky:
    """Handle all communication with the BloomSky API."""

    # API documentation at http://weatherlution.com/bloomsky-api/
    API_URL = "http://api.bloomsky.com/api/skydata"

    def __init__(self, api_key, is_metric):
        """Initialize the BookSky."""
        self._api_key = api_key
        self._endpoint_argument = "unit=intl" if is_metric else ""
        self.devices = {}
        self.is_metric = is_metric
        _LOGGER.debug("Initial BloomSky device load")
        self.refresh_devices()

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def refresh_devices(self):
        """Use the API to retrieve a list of devices."""
        _LOGGER.debug("Fetching BloomSky update")
        response = requests.get(
            f"{self.API_URL}?{self._endpoint_argument}",
            headers={AUTHORIZATION: self._api_key},
            timeout=10,
        )
        if response.status_code == HTTP_UNAUTHORIZED:
            raise RuntimeError("Invalid API_KEY")
        if response.status_code == HTTP_METHOD_NOT_ALLOWED:
            _LOGGER.error("You have no bloomsky devices configured")
            return
        if response.status_code != HTTP_OK:
            _LOGGER.error("Invalid HTTP response: %s", response.status_code)
            return
        # Create dictionary keyed off of the device unique id
        self.devices.update({device["DeviceID"]: device for device in response.json()})
