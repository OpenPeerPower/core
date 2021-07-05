"""Sensor that can display the current Open Peer Power versions."""
from datetime import timedelta
import logging

from pyopversion import OpVersion, OpVersionChannel, OpVersionSource
from pyopversion.exceptions import OpVersionFetchException, OpVersionParseException
import voluptuous as vol

from openpeerpower.components.sensor import PLATFORM_SCHEMA, SensorEntity
from openpeerpower.const import CONF_NAME, CONF_SOURCE
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
import openpeerpower.helpers.config_validation as cv
from openpeerpower.util import Throttle

ALL_IMAGES = [
    "default",
    "intel-nuc",
    "odroid-c2",
    "odroid-n2",
    "odroid-xu",
    "qemuarm-64",
    "qemuarm",
    "qemux86-64",
    "qemux86",
    "raspberrypi",
    "raspberrypi2",
    "raspberrypi3-64",
    "raspberrypi3",
    "raspberrypi4-64",
    "raspberrypi4",
    "tinker",
]
ALL_SOURCES = [
    "container",
    "opio",
    "local",
    "pypi",
    "supervisor",
    "oppio",  # Kept to not break existing configurations
    "docker",  # Kept to not break existing configurations
]

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

_LOGGER: logging.Logger = logging.getLogger(__name__)


async def async_setup_platform(opp, config, async_add_entities, discovery_info=None):
    """Set up the Version sensor platform."""

    beta = config.get(CONF_BETA)
    image = config.get(CONF_IMAGE)
    name = config.get(CONF_NAME)
    source = config.get(CONF_SOURCE)

    session = async_get_clientsession(opp)

    channel = OpVersionChannel.BETA if beta else OpVersionChannel.STABLE

    if source == "pypi":
        haversion = VersionData(
            OpVersion(session, source=OpVersionSource.PYPI, channel=channel)
        )
    elif source in ["oppio", "supervisor"]:
        haversion = VersionData(
            OpVersion(
                session,
                source=OpVersionSource.SUPERVISOR,
                channel=channel,
                image=image,
            )
        )
    elif source in ["docker", "container"]:
        if image is not None and image != DEFAULT_IMAGE:
            image = f"{image}-openpeerpower"
        haversion = VersionData(
            OpVersion(
                session, source=OpVersionSource.CONTAINER, channel=channel, image=image
            )
        )
    elif source == "opio":
        haversion = VersionData(OpVersion(session, source=OpVersionSource.OPIO))
    else:
        haversion = VersionData(OpVersion(session, source=OpVersionSource.LOCAL))

    if not name:
        if source == DEFAULT_SOURCE:
            name = DEFAULT_NAME_LOCAL
        else:
            name = DEFAULT_NAME_LATEST

    async_add_entities([VersionSensor(haversion, name)], True)


class VersionData:
    """Get the latest data and update the states."""

    def __init__(self, api: OpVersion) -> None:
        """Initialize the data object."""
        self.api = api

    @Throttle(TIME_BETWEEN_UPDATES)
    async def async_update(self):
        """Get the latest version information."""
        try:
            await self.api.get_version()
        except OpVersionFetchException as exception:
            _LOGGER.warning(exception)
        except OpVersionParseException as exception:
            _LOGGER.warning(
                "Could not parse data received for %s - %s", self.api.source, exception
            )


class VersionSensor(SensorEntity):
    """Representation of a Open Peer Power version sensor."""

    def __init__(self, data: VersionData, name: str) -> None:
        """Initialize the Version sensor."""
        self.data = data
        self._name = name
        self._state = None

    async def async_update(self):
        """Get the latest version information."""
        await self.data.async_update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.data.api.version

    @property
    def extra_state_attributes(self):
        """Return attributes for the sensor."""
        return self.data.api.version_data

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return ICON
