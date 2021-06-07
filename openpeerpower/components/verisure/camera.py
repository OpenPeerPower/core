"""Support for Verisure cameras."""
from __future__ import annotations

import errno
import os

from verisure import Error as VerisureError

from openpeerpower.components.camera import Camera
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import EVENT_OPENPEERPOWER_STOP
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.entity import DeviceInfo
from openpeerpower.helpers.entity_platform import (
    AddEntitiesCallback,
    async_get_current_platform,
)
from openpeerpower.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_GIID, DOMAIN, LOGGER, SERVICE_CAPTURE_SMARTCAM
from .coordinator import VerisureDataUpdateCoordinator


async def async_setup_entry(
    opp: OpenPeerPower,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Verisure sensors based on a config entry."""
    coordinator: VerisureDataUpdateCoordinator = opp.data[DOMAIN][entry.entry_id]

    platform = async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_CAPTURE_SMARTCAM,
        {},
        VerisureSmartcam.capture_smartcam.__name__,
    )

    assert opp.config.config_dir
    async_add_entities(
        VerisureSmartcam(coordinator, serial_number, opp.config.config_dir)
        for serial_number in coordinator.data["cameras"]
    )


class VerisureSmartcam(CoordinatorEntity, Camera):
    """Representation of a Verisure camera."""

    coordinator = VerisureDataUpdateCoordinator

    def __init__(
        self,
        coordinator: VerisureDataUpdateCoordinator,
        serial_number: str,
        directory_path: str,
    ) -> None:
        """Initialize Verisure File Camera component."""
        super().__init__(coordinator)
        Camera.__init__(self)

        self._attr_name = coordinator.data["cameras"][serial_number]["area"]
        self._attr_unique_id = serial_number

        self.serial_number = serial_number
        self._directory_path = directory_path
        self._image = None
        self._image_id = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity."""
        area = self.coordinator.data["cameras"][self.serial_number]["area"]
        return {
            "name": area,
            "suggested_area": area,
            "manufacturer": "Verisure",
            "model": "SmartCam",
            "identifiers": {(DOMAIN, self.serial_number)},
            "via_device": (DOMAIN, self.coordinator.entry.data[CONF_GIID]),
        }

    def camera_image(self) -> bytes | None:
        """Return image response."""
        self.check_imagelist()
        if not self._image:
            LOGGER.debug("No image to display")
            return
        LOGGER.debug("Trying to open %s", self._image)
        with open(self._image, "rb") as file:
            return file.read()

    def check_imagelist(self) -> None:
        """Check the contents of the image list."""
        self.coordinator.update_smartcam_imageseries()

        images = self.coordinator.imageseries.get("imageSeries", [])
        new_image_id = None
        for image in images:
            if image["deviceLabel"] == self.serial_number:
                new_image_id = image["image"][0]["imageId"]
                break

        if not new_image_id:
            return

        if new_image_id in ("-1", self._image_id):
            LOGGER.debug("The image is the same, or loading image_id")
            return

        LOGGER.debug("Download new image %s", new_image_id)
        new_image_path = os.path.join(
            self._directory_path, "{}{}".format(new_image_id, ".jpg")
        )
        self.coordinator.verisure.download_image(
            self.serial_number, new_image_id, new_image_path
        )
        LOGGER.debug("Old image_id=%s", self._image_id)
        self.delete_image()

        self._image_id = new_image_id
        self._image = new_image_path

    def delete_image(self, _=None) -> None:
        """Delete an old image."""
        remove_image = os.path.join(
            self._directory_path, "{}{}".format(self._image_id, ".jpg")
        )
        try:
            os.remove(remove_image)
            LOGGER.debug("Deleting old image %s", remove_image)
        except OSError as error:
            if error.errno != errno.ENOENT:
                raise

    def capture_smartcam(self) -> None:
        """Capture a new picture from a smartcam."""
        try:
            self.coordinator.smartcam_capture(self.serial_number)
            LOGGER.debug("Capturing new image from %s", self.serial_number)
        except VerisureError as ex:
            LOGGER.error("Could not capture image, %s", ex)

    async def async_added_to_opp(self) -> None:
        """Entity added to Open Peer Power."""
        await super().async_added_to_opp()
        self.opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, self.delete_image)
