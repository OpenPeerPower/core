"""Support for a camera of a BloomSky weather station."""
import logging

import requests

from openpeerpower.components.camera import Camera

from . import DOMAIN


def setup_platform(opp, config, add_entities, discovery_info=None):
    """Set up access to BloomSky cameras."""
    if discovery_info is not None:
        return

    bloomsky = opp.data[DOMAIN]

    for device in bloomsky.devices.values():
        add_entities([BloomSkyCamera(bloomsky, device)])


class BloomSkyCamera(Camera):
    """Representation of the images published from the BloomSky's camera."""

    def __init__(self, bs, device):
        """Initialize access to the BloomSky camera images."""
        super().__init__()
        self._name = device["DeviceName"]
        self._id = device["DeviceID"]
        self._bloomsky = bs
        self._url = ""
        self._last_url = ""
        # last_image will store images as they are downloaded so that the
        # frequent updates in openpeerpower don't keep poking the server
        # to download the same image over and over.
        self._last_image = ""
        self._logger = logging.getLogger(__name__)

    def camera_image(self):
        """Update the camera's image if it has changed."""
        try:
            self._url = self._bloomsky.devices[self._id]["Data"]["ImageURL"]
            self._bloomsky.refresh_devices()
            # If the URL hasn't changed then the image hasn't changed.
            if self._url != self._last_url:
                response = requests.get(self._url, timeout=10)
                self._last_url = self._url
                self._last_image = response.content
        except requests.exceptions.RequestException as error:
            self._logger.error("Error getting bloomsky image: %s", error)
            return None

        return self._last_image

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._id

    @property
    def name(self):
        """Return the name of this BloomSky device."""
        return self._name
