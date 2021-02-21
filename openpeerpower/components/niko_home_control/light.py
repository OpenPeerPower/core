"""Support for Niko Home Control."""
from datetime import timedelta
import logging

import nikohomecontrol
import voluptuous as vol

# Import the device class from the component that you want to support
from openpeerpower.components.light import ATTR_BRIGHTNESS, PLATFORM_SCHEMA, LightEntity
from openpeerpower.const import CONF_HOST
from openpeerpower.exceptions import PlatformNotReady
import openpeerpower.helpers.config_validation as cv
from openpeerpower.util import Throttle

_LOGGER = logging.getLogger(__name__)
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=1)
SCAN_INTERVAL = timedelta(seconds=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({vol.Required(CONF_HOST): cv.string})


async def async_setup_platform.opp, config, async_add_entities, discovery_info=None):
    """Set up the Niko Home Control light platform."""
    host = config[CONF_HOST]

    try:
        nhc = nikohomecontrol.NikoHomeControl(
            {"ip": host, "port": 8000, "timeout": 20000}
        )
        niko_data = NikoHomeControlData.opp, nhc)
        await niko_data.async_update()
    except OSError as err:
        _LOGGER.error("Unable to access %s (%s)", host, err)
        raise PlatformNotReady from err

    async_add_entities(
        [NikoHomeControlLight(light, niko_data) for light in nhc.list_actions()], True
    )


class NikoHomeControlLight(LightEntity):
    """Representation of an Niko Light."""

    def __init__(self, light, data):
        """Set up the Niko Home Control light platform."""
        self._data = data
        self._light = light
        self._unique_id = f"light-{light.id}"
        self._name = light.name
        self._state = light.is_on
        self._brightness = None

    @property
    def unique_id(self):
        """Return unique ID for light."""
        return self._unique_id

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return self._brightness

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state

    def turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        self._light.brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        _LOGGER.debug("Turn on: %s", self.name)
        self._light.turn_on()

    def turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        _LOGGER.debug("Turn off: %s", self.name)
        self._light.turn_off()

    async def async_update(self):
        """Get the latest data from NikoHomeControl API."""
        await self._data.async_update()
        self._state = self._data.get_state(self._light.id)


class NikoHomeControlData:
    """The class for handling data retrieval."""

    def __init__(self,.opp, nhc):
        """Set up Niko Home Control Data object."""
        self._nhc = nhc
        self.opp = opp
        self.available = True
        self.data = {}
        self._system_info = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        """Get the latest data from the NikoHomeControl API."""
        _LOGGER.debug("Fetching async state in bulk")
        try:
            self.data = await self.opp.async_add_executor_job(
                self._nhc.list_actions_raw
            )
            self.available = True
        except OSError as ex:
            _LOGGER.error("Unable to retrieve data from Niko, %s", str(ex))
            self.available = False

    def get_state(self, aid):
        """Find and filter state based on action id."""
        for state in self.data:
            if state["id"] == aid:
                return state["value1"] != 0
        _LOGGER.error("Failed to retrieve state off unknown light")
