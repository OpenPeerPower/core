"""Support for Synology DSM cameras."""
import logging
from typing import Dict

from synology_dsm.api.surveillance_station import SynoSurveillanceStation
from synology_dsm.exceptions import (
    SynologyDSMAPIErrorException,
    SynologyDSMRequestException,
)

from openpeerpower.components.camera import SUPPORT_STREAM, Camera
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.helpers.typing import OpenPeerPowerType
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator

from . import SynoApi, SynologyDSMBaseEntity
from .const import (
    COORDINATOR_CAMERAS,
    DOMAIN,
    ENTITY_CLASS,
    ENTITY_ENABLE,
    ENTITY_ICON,
    ENTITY_NAME,
    ENTITY_UNIT,
    SYNO_API,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    opp: OpenPeerPowerType, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the Synology NAS cameras."""

    data = opp.data[DOMAIN][entry.unique_id]
    api = data[SYNO_API]

    if SynoSurveillanceStation.CAMERA_API_KEY not in api.dsm.apis:
        return

    # initial data fetch
    coordinator = data[COORDINATOR_CAMERAS]
    await coordinator.async_refresh()

    async_add_entities(
        SynoDSMCamera(api, coordinator, camera_id)
        for camera_id in coordinator.data["cameras"]
    )


class SynoDSMCamera(SynologyDSMBaseEntity, Camera):
    """Representation a Synology camera."""

    def __init__(
        self, api: SynoApi, coordinator: DataUpdateCoordinator, camera_id: int
    ):
        """Initialize a Synology camera."""
        super().__init__(
            api,
            f"{SynoSurveillanceStation.CAMERA_API_KEY}:{camera_id}",
            {
                ENTITY_NAME: coordinator.data["cameras"][camera_id].name,
                ENTITY_ENABLE: coordinator.data["cameras"][camera_id].is_enabled,
                ENTITY_CLASS: None,
                ENTITY_ICON: None,
                ENTITY_UNIT: None,
            },
            coordinator,
        )
        Camera.__init__(self)

        self._camera_id = camera_id
        self._api = api

    @property
    def camera_data(self):
        """Camera data."""
        return self.coordinator.data["cameras"][self._camera_id]

    @property
    def device_info(self) -> Dict[str, any]:
        """Return the device information."""
        return {
            "identifiers": {
                (
                    DOMAIN,
                    self._api.information.serial,
                    self.camera_data.id,
                )
            },
            "name": self.camera_data.name,
            "model": self.camera_data.model,
            "via_device": (
                DOMAIN,
                self._api.information.serial,
                SynoSurveillanceStation.INFO_API_KEY,
            ),
        }

    @property
    def available(self) -> bool:
        """Return the availability of the camera."""
        return self.camera_data.is_enabled and self.coordinator.last_update_success

    @property
    def supported_features(self) -> int:
        """Return supported features of this camera."""
        return SUPPORT_STREAM

    @property
    def is_recording(self):
        """Return true if the device is recording."""
        return self.camera_data.is_recording

    @property
    def motion_detection_enabled(self):
        """Return the camera motion detection status."""
        return self.camera_data.is_motion_detection_enabled

    def camera_image(self) -> bytes:
        """Return bytes of camera image."""
        _LOGGER.debug(
            "SynoDSMCamera.camera_image(%s)",
            self.camera_data.name,
        )
        if not self.available:
            return None
        try:
            return self._api.surveillance_station.get_camera_image(self._camera_id)
        except (
            SynologyDSMAPIErrorException,
            SynologyDSMRequestException,
            ConnectionRefusedError,
        ) as err:
            _LOGGER.debug(
                "SynoDSMCamera.camera_image(%s) - Exception:%s",
                self.camera_data.name,
                err,
            )
            return None

    async def stream_source(self) -> str:
        """Return the source of the stream."""
        _LOGGER.debug(
            "SynoDSMCamera.stream_source(%s)",
            self.camera_data.name,
        )
        if not self.available:
            return None
        return self.camera_data.live_view.rtsp

    def enable_motion_detection(self):
        """Enable motion detection in the camera."""
        _LOGGER.debug(
            "SynoDSMCamera.enable_motion_detection(%s)",
            self.camera_data.name,
        )
        self._api.surveillance_station.enable_motion_detection(self._camera_id)

    def disable_motion_detection(self):
        """Disable motion detection in camera."""
        _LOGGER.debug(
            "SynoDSMCamera.disable_motion_detection(%s)",
            self.camera_data.name,
        )
        self._api.surveillance_station.disable_motion_detection(self._camera_id)
