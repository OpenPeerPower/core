"""Support for Blink system camera."""
import logging

import voluptuous as vol

from openpeerpower.components.camera import Camera
from openpeerpower.const import ATTR_ENTITY_ID
from openpeerpower.helpers import entity_platform
import openpeerpower.helpers.config_validation as cv

from .const import DEFAULT_BRAND, DOMAIN, SERVICE_TRIGGER

_LOGGER = logging.getLogger(__name__)

ATTR_VIDEO_CLIP = "video"
ATTR_IMAGE = "image"

SERVICE_TRIGGER_SCHEMA = vol.Schema({vol.Optional(ATTR_ENTITY_ID): cv.comp_entity_ids})


async def async_setup_entry(opp, config, async_add_entities):
    """Set up a Blink Camera."""
    data = opp.data[DOMAIN][config.entry_id]
    entities = []
    for name, camera in data.cameras.items():
        entities.append(BlinkCamera(data, name, camera))

    async_add_entities(entities)

    platform = entity_platform.current_platform.get()

    platform.async_register_entity_service(
        SERVICE_TRIGGER, SERVICE_TRIGGER_SCHEMA, "trigger_camera"
    )


class BlinkCamera(Camera):
    """An implementation of a Blink Camera."""

    def __init__(self, data, name, camera):
        """Initialize a camera."""
        super().__init__()
        self.data = data
        self._name = f"{DOMAIN} {name}"
        self._camera = camera
        self._unique_id = f"{camera.serial}-camera"
        self.response = None
        self.current_image = None
        self.last_image = None
        _LOGGER.debug("Initialized blink camera %s", self._name)

    @property
    def name(self):
        """Return the camera name."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique camera id."""
        return self._unique_id

    @property
    def device_state_attributes(self):
        """Return the camera attributes."""
        return self._camera.attributes

    def enable_motion_detection(self):
        """Enable motion detection for the camera."""
        self._camera.set_motion_detect(True)

    def disable_motion_detection(self):
        """Disable motion detection for the camera."""
        self._camera.set_motion_detect(False)

    @property
    def motion_detection_enabled(self):
        """Return the state of the camera."""
        return self._camera.motion_enabled

    @property
    def brand(self):
        """Return the camera brand."""
        return DEFAULT_BRAND

    def trigger_camera(self):
        """Trigger camera to take a snapshot."""
        self._camera.snap_picture()
        self.data.refresh()

    def camera_image(self):
        """Return a still image response from the camera."""
        return self._camera.image_from_cache.content
