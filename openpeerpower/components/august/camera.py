"""Support for August doorbell camera."""

from yalexs.activity import ActivityType
from yalexs.util import update_doorbell_image_from_activity

from openpeerpower.components.camera import Camera
from openpeerpower.core import callback
from openpeerpower.helpers import aiohttp_client

from .const import DATA_AUGUST, DEFAULT_NAME, DEFAULT_TIMEOUT, DOMAIN
from .entity import AugustEntityMixin


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up August cameras."""
    data = opp.data[DOMAIN][config_entry.entry_id][DATA_AUGUST]
    session = aiohttp_client.async_get_clientsession(opp)
    async_add_entities(
        [
            AugustCamera(data, doorbell, session, DEFAULT_TIMEOUT)
            for doorbell in data.doorbells
        ]
    )


class AugustCamera(AugustEntityMixin, Camera):
    """An implementation of a August security camera."""

    def __init__(self, data, device, session, timeout):
        """Initialize a August security camera."""
        super().__init__(data, device)
        self._data = data
        self._device = device
        self._timeout = timeout
        self._session = session
        self._image_url = None
        self._image_content = None

    @property
    def name(self):
        """Return the name of this device."""
        return f"{self._device.device_name} Camera"

    @property
    def is_recording(self):
        """Return true if the device is recording."""
        return self._device.has_subscription

    @property
    def motion_detection_enabled(self):
        """Return the camera motion detection status."""
        return True

    @property
    def brand(self):
        """Return the camera brand."""
        return DEFAULT_NAME

    @property
    def model(self):
        """Return the camera model."""
        return self._detail.model

    @callback
    def _update_from_data(self):
        """Get the latest state of the sensor."""
        doorbell_activity = self._data.activity_stream.get_latest_device_activity(
            self._device_id, {ActivityType.DOORBELL_MOTION}
        )

        if doorbell_activity is not None:
            update_doorbell_image_from_activity(self._detail, doorbell_activity)

    async def async_camera_image(self):
        """Return bytes of camera image."""
        self._update_from_data()

        if self._image_url is not self._detail.image_url:
            self._image_url = self._detail.image_url
            self._image_content = await self._detail.async_get_doorbell_image(
                self._session, timeout=self._timeout
            )
        return self._image_content

    @property
    def unique_id(self) -> str:
        """Get the unique id of the camera."""
        return f"{self._device_id:s}_camera"
