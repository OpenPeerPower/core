"""Code to handle a Dynalite bridge."""

from typing import Any, Callable, Dict, List, Optional

from dynalite_devices_lib.dynalite_devices import (
    CONF_AREA as dyn_CONF_AREA,
    CONF_PRESET as dyn_CONF_PRESET,
    NOTIFICATION_PACKET,
    NOTIFICATION_PRESET,
    DynaliteBaseDevice,
    DynaliteDevices,
    DynaliteNotification,
)

from openpeerpower.const import CONF_HOST
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers.dispatcher import async_dispatcher_send

from .const import ATTR_AREA, ATTR_HOST, ATTR_PACKET, ATTR_PRESET, LOGGER, PLATFORMS
from .convert_config import convert_config


class DynaliteBridge:
    """Manages a single Dynalite bridge."""

    def __init__(self, opp: OpenPeerPower, config: Dict[str, Any]) -> None:
        """Initialize the system based on host parameter."""
        self.opp = opp
        self.area = {}
        self.async_add_devices = {}
        self.waiting_devices = {}
        self.host = config[CONF_HOST]
        # Configure the dynalite devices
        self.dynalite_devices = DynaliteDevices(
            new_device_func=self.add_devices_when_registered,
            update_device_func=self.update_device,
            notification_func=self.handle_notification,
        )
        self.dynalite_devices.configure(convert_config(config))

    async def async_setup(self) -> bool:
        """Set up a Dynalite bridge."""
        # Configure the dynalite devices
        LOGGER.debug("Setting up bridge - host %s", self.host)
        return await self.dynalite_devices.async_setup()

    def reload_config(self, config: Dict[str, Any]) -> None:
        """Reconfigure a bridge when config changes."""
        LOGGER.debug("Reloading bridge - host %s, config %s", self.host, config)
        self.dynalite_devices.configure(convert_config(config))

    def update_signal(self, device: Optional[DynaliteBaseDevice] = None) -> str:
        """Create signal to use to trigger entity update."""
        if device:
            signal = f"dynalite-update-{self.host}-{device.unique_id}"
        else:
            signal = f"dynalite-update-{self.host}"
        return signal

    @callback
    def update_device(self, device: Optional[DynaliteBaseDevice] = None) -> None:
        """Call when a device or all devices should be updated."""
        if not device:
            # This is used to signal connection or disconnection, so all devices may become available or not.
            log_string = (
                "Connected" if self.dynalite_devices.connected else "Disconnected"
            )
            LOGGER.info("%s to dynalite host", log_string)
            async_dispatcher_send(self.opp, self.update_signal())
        else:
            async_dispatcher_send(self.opp, self.update_signal(device))

    @callback
    def handle_notification(self, notification: DynaliteNotification) -> None:
        """Handle a notification from the platform and issue events."""
        if notification.notification == NOTIFICATION_PACKET:
            self.opp.bus.async_fire(
                "dynalite_packet",
                {
                    ATTR_HOST: self.host,
                    ATTR_PACKET: notification.data[NOTIFICATION_PACKET],
                },
            )
        if notification.notification == NOTIFICATION_PRESET:
            self.opp.bus.async_fire(
                "dynalite_preset",
                {
                    ATTR_HOST: self.host,
                    ATTR_AREA: notification.data[dyn_CONF_AREA],
                    ATTR_PRESET: notification.data[dyn_CONF_PRESET],
                },
            )

    @callback
    def register_add_devices(self, platform: str, async_add_devices: Callable) -> None:
        """Add an async_add_entities for a category."""
        self.async_add_devices[platform] = async_add_devices
        if platform in self.waiting_devices:
            self.async_add_devices[platform](self.waiting_devices[platform])

    def add_devices_when_registered(self, devices: List[DynaliteBaseDevice]) -> None:
        """Add the devices to OP if the add devices callback was registered, otherwise queue until it is."""
        for platform in PLATFORMS:
            platform_devices = [
                device for device in devices if device.category == platform
            ]
            if platform in self.async_add_devices:
                self.async_add_devices[platform](platform_devices)
            else:  # handle it later when it is registered
                if platform not in self.waiting_devices:
                    self.waiting_devices[platform] = []
                self.waiting_devices[platform].extend(platform_devices)
