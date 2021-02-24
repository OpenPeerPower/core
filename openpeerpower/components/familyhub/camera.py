"""Family Hub camera for Samsung Refrigerators."""
from pyfamilyhublocal import FamilyHubCam
import voluptuous as vol

from openpeerpower.components.camera import PLATFORM_SCHEMA, Camera
from openpeerpower.const import CONF_IP_ADDRESS, CONF_NAME
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
import openpeerpower.helpers.config_validation as cv

DEFAULT_NAME = "FamilyHub Camera"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_IP_ADDRESS): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


async def async_setup_platform(opp, config, async_add_entities, discovery_info=None):
    """Set up the Family Hub Camera."""

    address = config.get(CONF_IP_ADDRESS)
    name = config.get(CONF_NAME)

    session = async_get_clientsession(opp)
    family_hub_cam = FamilyHubCam(address, opp.loop, session)

    async_add_entities([FamilyHubCamera(name, family_hub_cam)], True)


class FamilyHubCamera(Camera):
    """The representation of a Family Hub camera."""

    def __init__(self, name, family_hub_cam):
        """Initialize camera component."""
        super().__init__()
        self._name = name
        self.family_hub_cam = family_hub_cam

    async def async_camera_image(self):
        """Return a still image response."""
        return await self.family_hub_cam.async_get_cam_image()

    @property
    def name(self):
        """Return the name of this camera."""
        return self._name
