"""Support for the Netatmo camera lights."""
import logging

import pyatmo

from openpeerpower.components.light import LightEntity
from openpeerpower.core import callback
from openpeerpower.exceptions import PlatformNotReady
from openpeerpower.helpers.dispatcher import async_dispatcher_connect

from .const import (
    DATA_HANDLER,
    DOMAIN,
    EVENT_TYPE_LIGHT_MODE,
    MANUFACTURER,
    SIGNAL_NAME,
)
from .data_op.dler import CAMERA_DATA_CLASS_NAME, NetatmoDataHandler
from .netatmo_entity_base import NetatmoBase

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry.opp, entry, async_add_entities):
    """Set up the Netatmo camera light platform."""
    if "access_camera" not in entry.data["token"]["scope"]:
        _LOGGER.info(
            "Cameras are currently not supported with this authentication method"
        )
        return

    data_op.dler = opp.data[DOMAIN][entry.entry_id][DATA_HANDLER]

    async def get_entities():
        """Retrieve Netatmo entities."""
        await data_op.dler.register_data_class(
            CAMERA_DATA_CLASS_NAME, CAMERA_DATA_CLASS_NAME, None
        )

        entities = []
        all_cameras = []

        if CAMERA_DATA_CLASS_NAME not in data_op.dler.data:
            raise PlatformNotReady

        try:
            for home in data_op.dler.data[CAMERA_DATA_CLASS_NAME].cameras.values():
                for camera in home.values():
                    all_cameras.append(camera)

        except pyatmo.NoDevice:
            _LOGGER.debug("No cameras found")

        for camera in all_cameras:
            if camera["type"] == "NOC":
                _LOGGER.debug("Adding camera light %s %s", camera["id"], camera["name"])
                entities.append(
                    NetatmoLight(
                        data_op.dler,
                        camera["id"],
                        camera["type"],
                        camera["home_id"],
                    )
                )

        return entities

    async_add_entities(await get_entities(), True)


class NetatmoLight(NetatmoBase, LightEntity):
    """Representation of a Netatmo Presence camera light."""

    def __init__(
        self,
        data_op.dler: NetatmoDataHandler,
        camera_id: str,
        camera_type: str,
        home_id: str,
    ):
        """Initialize a Netatmo Presence camera light."""
        LightEntity.__init__(self)
        super().__init__(data_op.dler)

        self._data_classes.append(
            {"name": CAMERA_DATA_CLASS_NAME, SIGNAL_NAME: CAMERA_DATA_CLASS_NAME}
        )
        self._id = camera_id
        self._home_id = home_id
        self._model = camera_type
        self._device_name = self._data.get_camera(camera_id).get("name")
        self._name = f"{MANUFACTURER} {self._device_name}"
        self._is_on = False
        self._unique_id = f"{self._id}-light"

    async def async_added_to_opp(self) -> None:
        """Entity created."""
        await super().async_added_to_opp()

        self._listeners.append(
            async_dispatcher_connect(
                self.opp,
                f"signal-{DOMAIN}-webhook-{EVENT_TYPE_LIGHT_MODE}",
                self.handle_event,
            )
        )

    @callback
    def handle_event(self, event):
        """Handle webhook events."""
        data = event["data"]

        if not data.get("camera_id"):
            return

        if (
            data["home_id"] == self._home_id
            and data["camera_id"] == self._id
            and data["push_type"] == "NOC-light_mode"
        ):
            self._is_on = bool(data["sub_type"] == "on")

            self.async_write_op.state()
            return

    @property
    def available(self) -> bool:
        """If the webhook is not established, mark as unavailable."""
        return bool(self.data_op.dler.webhook)

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._is_on

    def turn_on(self, **kwargs):
        """Turn camera floodlight on."""
        _LOGGER.debug("Turn camera '%s' on", self._name)
        self._data.set_state(
            home_id=self._home_id,
            camera_id=self._id,
            floodlight="on",
        )

    def turn_off(self, **kwargs):
        """Turn camera floodlight into auto mode."""
        _LOGGER.debug("Turn camera '%s' to auto mode", self._name)
        self._data.set_state(
            home_id=self._home_id,
            camera_id=self._id,
            floodlight="auto",
        )

    @callback
    def async_update_callback(self):
        """Update the entity's state."""
        self._is_on = bool(self._data.get_light_state(self._id) == "on")
