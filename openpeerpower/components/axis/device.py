"""Axis network device abstraction."""

import asyncio

import async_timeout
import axis
from axis.configuration import Configuration
from axis.errors import Unauthorized
from axis.event_stream import OPERATION_INITIALIZED
from axis.mqtt import mqtt_json_to_event
from axis.streammanager import SIGNAL_PLAYING, STATE_STOPPED

from openpeerpower.components import mqtt
from openpeerpower.components.mqtt import DOMAIN as MQTT_DOMAIN
from openpeerpower.components.mqtt.models import Message
from openpeerpower.config_entries import SOURCE_REAUTH
from openpeerpower.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_TRIGGER_TIME,
    CONF_USERNAME,
)
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.device_registry import CONNECTION_NETWORK_MAC
from openpeerpower.helpers.dispatcher import async_dispatcher_send
from openpeerpower.helpers.httpx_client import get_async_client
from openpeerpower.setup import async_when_setup

from .const import (
    ATTR_MANUFACTURER,
    CONF_EVENTS,
    CONF_MODEL,
    CONF_STREAM_PROFILE,
    CONF_VIDEO_SOURCE,
    DEFAULT_EVENTS,
    DEFAULT_STREAM_PROFILE,
    DEFAULT_TRIGGER_TIME,
    DEFAULT_VIDEO_SOURCE,
    DOMAIN as AXIS_DOMAIN,
    LOGGER,
    PLATFORMS,
)
from .errors import AuthenticationRequired, CannotConnect


class AxisNetworkDevice:
    """Manages a Axis device."""

    def __init__(self, opp, config_entry):
        """Initialize the device."""
        self.opp = opp
        self.config_entry = config_entry
        self.available = True

        self.api = None
        self.fw_version = None
        self.product_type = None

        self.listeners = []

    @property
    def host(self):
        """Return the host address of this device."""
        return self.config_entry.data[CONF_HOST]

    @property
    def port(self):
        """Return the HTTP port of this device."""
        return self.config_entry.data[CONF_PORT]

    @property
    def username(self):
        """Return the username of this device."""
        return self.config_entry.data[CONF_USERNAME]

    @property
    def password(self):
        """Return the password of this device."""
        return self.config_entry.data[CONF_PASSWORD]

    @property
    def model(self):
        """Return the model of this device."""
        return self.config_entry.data[CONF_MODEL]

    @property
    def name(self):
        """Return the name of this device."""
        return self.config_entry.data[CONF_NAME]

    @property
    def unique_id(self):
        """Return the unique ID (serial number) of this device."""
        return self.config_entry.unique_id

    # Options

    @property
    def option_events(self):
        """Config entry option defining if platforms based on events should be created."""
        return self.config_entry.options.get(CONF_EVENTS, DEFAULT_EVENTS)

    @property
    def option_stream_profile(self):
        """Config entry option defining what stream profile camera platform should use."""
        return self.config_entry.options.get(
            CONF_STREAM_PROFILE, DEFAULT_STREAM_PROFILE
        )

    @property
    def option_trigger_time(self):
        """Config entry option defining minimum number of seconds to keep trigger high."""
        return self.config_entry.options.get(CONF_TRIGGER_TIME, DEFAULT_TRIGGER_TIME)

    @property
    def option_video_source(self):
        """Config entry option defining what video source camera platform should use."""
        return self.config_entry.options.get(CONF_VIDEO_SOURCE, DEFAULT_VIDEO_SOURCE)

    # Signals

    @property
    def signal_reachable(self):
        """Device specific event to signal a change in connection status."""
        return f"axis_reachable_{self.unique_id}"

    @property
    def signal_new_event(self):
        """Device specific event to signal new device event available."""
        return f"axis_new_event_{self.unique_id}"

    @property
    def signal_new_address(self):
        """Device specific event to signal a change in device address."""
        return f"axis_new_address_{self.unique_id}"

    # Callbacks

    @callback
    def async_connection_status_callback(self, status):
        """Handle signals of device connection status.

        This is called on every RTSP keep-alive message.
        Only signal state change if state change is true.
        """

        if self.available != (status == SIGNAL_PLAYING):
            self.available = not self.available
            async_dispatcher_send(self.opp, self.signal_reachable, True)

    @callback
    def async_event_callback(self, action, event_id):
        """Call to configure events when initialized on event stream."""
        if action == OPERATION_INITIALIZED:
            async_dispatcher_send(self.opp, self.signal_new_event, event_id)

    @staticmethod
    async def async_new_address_callback(opp, entry):
        """Handle signals of device getting new address.

        Called when config entry is updated.
        This is a static method because a class method (bound method),
        can not be used with weak references.
        """
        device = opp.data[AXIS_DOMAIN][entry.unique_id]
        device.api.config.host = device.host
        async_dispatcher_send(opp, device.signal_new_address)

    async def async_update_device_registry(self):
        """Update device registry."""
        device_registry = await self.opp.helpers.device_registry.async_get_registry()
        device_registry.async_get_or_create(
            config_entry_id=self.config_entry.entry_id,
            connections={(CONNECTION_NETWORK_MAC, self.unique_id)},
            identifiers={(AXIS_DOMAIN, self.unique_id)},
            manufacturer=ATTR_MANUFACTURER,
            model=f"{self.model} {self.product_type}",
            name=self.name,
            sw_version=self.fw_version,
        )

    async def use_mqtt(self, opp: OpenPeerPower, component: str) -> None:
        """Set up to use MQTT."""
        try:
            status = await self.api.vapix.mqtt.get_client_status()
        except Unauthorized:
            # This means the user has too low privileges
            status = {}

        if status.get("data", {}).get("status", {}).get("state") == "active":
            self.listeners.append(
                await mqtt.async_subscribe(
                    opp, f"{self.api.vapix.serial_number}/#", self.mqtt_message
                )
            )

    @callback
    def mqtt_message(self, message: Message) -> None:
        """Receive Axis MQTT message."""
        self.disconnect_from_stream()

        event = mqtt_json_to_event(message.payload)
        self.api.event.update([event])

    # Setup and teardown methods

    async def async_setup(self):
        """Set up the device."""
        try:
            self.api = await get_device(
                self.opp,
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
            )

        except CannotConnect as err:
            raise ConfigEntryNotReady from err

        except AuthenticationRequired:
            self.opp.async_create_task(
                self.opp.config_entries.flow.async_init(
                    AXIS_DOMAIN,
                    context={"source": SOURCE_REAUTH},
                    data=self.config_entry.data,
                )
            )
            return False

        self.fw_version = self.api.vapix.firmware_version
        self.product_type = self.api.vapix.product_type

        async def start_platforms():
            await asyncio.gather(
                *[
                    self.opp.config_entries.async_forward_entry_setup(
                        self.config_entry, platform
                    )
                    for platform in PLATFORMS
                ]
            )
            if self.option_events:
                self.api.stream.connection_status_callback.append(
                    self.async_connection_status_callback
                )
                self.api.enable_events(event_callback=self.async_event_callback)
                self.api.stream.start()

                if self.api.vapix.mqtt:
                    async_when_setup(self.opp, MQTT_DOMAIN, self.use_mqtt)

        self.opp.async_create_task(start_platforms())

        self.config_entry.add_update_listener(self.async_new_address_callback)

        return True

    @callback
    def disconnect_from_stream(self):
        """Stop stream."""
        if self.api.stream.state != STATE_STOPPED:
            self.api.stream.connection_status_callback.remove(
                self.async_connection_status_callback
            )
            self.api.stream.stop()

    async def shutdown(self, event):
        """Stop the event stream."""
        self.disconnect_from_stream()

    async def async_reset(self):
        """Reset this device to default state."""
        self.disconnect_from_stream()

        unload_ok = all(
            await asyncio.gather(
                *[
                    self.opp.config_entries.async_forward_entry_unload(
                        self.config_entry, platform
                    )
                    for platform in PLATFORMS
                ]
            )
        )
        if not unload_ok:
            return False

        for unsubscribe_listener in self.listeners:
            unsubscribe_listener()

        return True


async def get_device(opp, host, port, username, password):
    """Create a Axis device."""
    session = get_async_client(opp, verify_ssl=False)

    device = axis.AxisDevice(
        Configuration(session, host, port=port, username=username, password=password)
    )

    try:
        with async_timeout.timeout(15):
            await device.vapix.initialize()

        return device

    except axis.Unauthorized as err:
        LOGGER.warning("Connected to device at %s but not registered.", host)
        raise AuthenticationRequired from err

    except (asyncio.TimeoutError, axis.RequestError) as err:
        LOGGER.error("Error connecting to the Axis device at %s", host)
        raise CannotConnect from err

    except axis.AxisException as err:
        LOGGER.exception("Unknown Axis communication error occurred")
        raise AuthenticationRequired from err
