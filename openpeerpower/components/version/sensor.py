"""Sensor that can display the current Open Peer Power versions."""
from datetime import timedelta

from pyoppversion import (
    DockerVersion,
    LocalVersion,
    OpIoVersion,
    OppioVersion,
    PyPiVersion,
)
import voluptuous as vol

from openpeerpower.components.sensor import PLATFORM_SCHEMA
from openpeerpower.const import CONF_NAME, CONF_SOURCE
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.entity import Entity
from openpeerpower.util import Throttle

ALL_IMAGES = [
    "default",
    "intel-nuc",
    "qemux86",
    "qemux86-64",
    "qemuarm",
    "qemuarm-64",
    "raspberrypi",
    "raspberrypi2",
    "raspberrypi3",
    "raspberrypi3-64",
    "raspberrypi4",
    "raspberrypi4-64",
    "tinker",
    "odroid-c2",
    "odroid-n2",
    "odroid-xu",
]
ALL_SOURCES = ["local", "pypi", "oppio", "docker", "haio"]

CONF_BETA = "beta"
CONF_IMAGE = "image"

DEFAULT_IMAGE = "default"
DEFAULT_NAME_LATEST = "Latest Version"
DEFAULT_NAME_LOCAL = "Current Version"
DEFAULT_SOURCE = "local"

ICON = "mdi:package-up"

TIME_BETWEEN_UPDATES = timedelta(minutes=5)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_BETA, default=False): cv.boolean,
        vol.Optional(CONF_IMAGE, default=DEFAULT_IMAGE): vol.In(ALL_IMAGES),
        vol.Optional(CONF_NAME, default=""): cv.string,
        vol.Optional(CONF_SOURCE, default=DEFAULT_SOURCE): vol.In(ALL_SOURCES),
    }
)


async def async_setup_platform(opp, config, async_add_entities, discovery_info=None):
    """Set up the Version sensor platform."""

    beta = config.get(CONF_BETA)
    image = config.get(CONF_IMAGE)
    name = config.get(CONF_NAME)
    source = config.get(CONF_SOURCE)

    session = async_get_clientsession(opp)

    if beta:
        branch = "beta"
    else:
        branch = "stable"

    if source == "pypi":
        opversion = VersionData(PyPiVersion(opp.loop, session, branch))
    elif source == "oppio":
        opversion = VersionData(OppioVersion(opp.loop, session, branch, image))
    elif source == "docker":
        opversion = VersionData(DockerVersion(opp.loop, session, branch, image))
    elif source == "haio":
        opversion = VersionData(OpIoVersion(opp.loop, session))
    else:
        opversion = VersionData(LocalVersion(opp.loop, session))

    if not name:
        if source == DEFAULT_SOURCE:
            name = DEFAULT_NAME_LOCAL
        else:
            name = DEFAULT_NAME_LATEST

    async_add_entities([VersionSensor(opversion, name)], True)


class VersionSensor(Entity):
    """Representation of a Open Peer Power version sensor."""

    def __init__(self, opversion, name):
        """Initialize the Version sensor."""
        self.opversion = opversion
        self._name = name
        self._state = None

    async def async_update(self):
        """Get the latest version information."""
        await self.opversion.async_update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.opversion.api.version

    @property
    def device_state_attributes(self):
        """Return attributes for the sensor."""
        return self.opversion.api.version_data

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return ICON


class VersionData:
    """Get the latest data and update the states."""

    def __init__(self, api):
        """Initialize the data object."""
        self.api = api

    @Throttle(TIME_BETWEEN_UPDATES)
    async def async_update(self):
        """Get the latest version information."""
        await self.api.get_version()
