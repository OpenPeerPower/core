"""Support for Minut Point."""
import asyncio
import logging

from pypoint import PointSession
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_TOKEN,
    CONF_WEBHOOK_ID,
)
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from openpeerpower.helpers.entity import Entity
from openpeerpower.helpers.event import async_track_time_interval
from openpeerpower.helpers.typing import OpenPeerPowerType
from openpeerpower.util.dt import as_local, parse_datetime, utc_from_timestamp

from . import config_flow
from .const import (
    CONF_WEBHOOK_URL,
    DOMAIN,
    EVENT_RECEIVED,
    POINT_DISCOVERY_NEW,
    SCAN_INTERVAL,
    SIGNAL_UPDATE_ENTITY,
    SIGNAL_WEBHOOK,
)

_LOGGER = logging.getLogger(__name__)

DATA_CONFIG_ENTRY_LOCK = "point_config_entry_lock"
CONFIG_ENTRY_IS_SETUP = "point_config_entry_is_setup"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Required(CONF_CLIENT_SECRET): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup.opp, config):
    """Set up the Minut Point component."""
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]

    config_flow.register_flow_implementation(
       .opp, DOMAIN, conf[CONF_CLIENT_ID], conf[CONF_CLIENT_SECRET]
    )

   .opp.async_create_task(
       .opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}
        )
    )

    return True


async def async_setup_entry.opp: OpenPeerPowerType, entry: ConfigEntry):
    """Set up Point from a config entry."""

    async def token_saver(token, **kwargs):
        _LOGGER.debug("Saving updated token %s", token)
       .opp.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_TOKEN: token}
        )

    session = PointSession(
       .opp.helpers.aiohttp_client.async_get_clientsession(),
        entry.data["refresh_args"][CONF_CLIENT_ID],
        entry.data["refresh_args"][CONF_CLIENT_SECRET],
        token=entry.data[CONF_TOKEN],
        token_saver=token_saver,
    )
    try:
        await session.ensure_active_token()
    except Exception:  # pylint: disable=broad-except
        _LOGGER.error("Authentication Error")
        return False

   .opp.data[DATA_CONFIG_ENTRY_LOCK] = asyncio.Lock()
   .opp.data[CONFIG_ENTRY_IS_SETUP] = set()

    await async_setup_webhook.opp, entry, session)
    client = MinutPointClient.opp, entry, session)
   .opp.data.setdefault(DOMAIN, {}).update({entry.entry_id: client})
   .opp.async_create_task(client.update())

    return True


async def async_setup_webhook.opp: OpenPeerPowerType, entry: ConfigEntry, session):
    """Set up a webhook to handle binary sensor events."""
    if CONF_WEBHOOK_ID not in entry.data:
        webhook_id = opp.components.webhook.async_generate_id()
        webhook_url = opp.components.webhook.async_generate_url(webhook_id)
        _LOGGER.info("Registering new webhook at: %s", webhook_url)

       .opp.config_entries.async_update_entry(
            entry,
            data={
                **entry.data,
                CONF_WEBHOOK_ID: webhook_id,
                CONF_WEBHOOK_URL: webhook_url,
            },
        )
    await session.update_webhook(
        entry.data[CONF_WEBHOOK_URL],
        entry.data[CONF_WEBHOOK_ID],
        ["*"],
    )

   .opp.components.webhook.async_register(
        DOMAIN, "Point", entry.data[CONF_WEBHOOK_ID], handle_webhook
    )


async def async_unload_entry.opp: OpenPeerPowerType, entry: ConfigEntry):
    """Unload a config entry."""
   .opp.components.webhook.async_unregister(entry.data[CONF_WEBHOOK_ID])
    session = opp.data[DOMAIN].pop(entry.entry_id)
    await session.remove_webhook()

    for component in ("binary_sensor", "sensor"):
        await opp.config_entries.async_forward_entry_unload(entry, component)

    if not.opp.data[DOMAIN]:
       .opp.data.pop(DOMAIN)

    return True


async def handle_webhook.opp, webhook_id, request):
    """Handle webhook callback."""
    try:
        data = await request.json()
        _LOGGER.debug("Webhook %s: %s", webhook_id, data)
    except ValueError:
        return None

    if isinstance(data, dict):
        data["webhook_id"] = webhook_id
        async_dispatcher_send.opp, SIGNAL_WEBHOOK, data, data.get("hook_id"))
   .opp.bus.async_fire(EVENT_RECEIVED, data)


class MinutPointClient:
    """Get the latest data and update the states."""

    def __init__(self,.opp: OpenPeerPowerType, config_entry: ConfigEntry, session):
        """Initialize the Minut data object."""
        self._known_devices = set()
        self._known_homes = set()
        self._opp = opp
        self._config_entry = config_entry
        self._is_available = True
        self._client = session

        async_track_time_interval(self._opp, self.update, SCAN_INTERVAL)

    async def update(self, *args):
        """Periodically poll the cloud for current state."""
        await self._sync()

    async def _sync(self):
        """Update local list of devices."""
        if not await self._client.update() and self._is_available:
            self._is_available = False
            _LOGGER.warning("Device is unavailable")
            async_dispatcher_send(self._opp, SIGNAL_UPDATE_ENTITY)
            return

        async def new_device(device_id, component):
            """Load new device."""
            config_entries_key = f"{component}.{DOMAIN}"
            async with self._opp.data[DATA_CONFIG_ENTRY_LOCK]:
                if config_entries_key not in self._opp.data[CONFIG_ENTRY_IS_SETUP]:
                    await self._opp.config_entries.async_forward_entry_setup(
                        self._config_entry, component
                    )
                    self._opp.data[CONFIG_ENTRY_IS_SETUP].add(config_entries_key)

            async_dispatcher_send(
                self._opp, POINT_DISCOVERY_NEW.format(component, DOMAIN), device_id
            )

        self._is_available = True
        for home_id in self._client.homes:
            if home_id not in self._known_homes:
                await new_device(home_id, "alarm_control_panel")
                self._known_homes.add(home_id)
        for device in self._client.devices:
            if device.device_id not in self._known_devices:
                for component in ("sensor", "binary_sensor"):
                    await new_device(device.device_id, component)
                self._known_devices.add(device.device_id)
        async_dispatcher_send(self._opp, SIGNAL_UPDATE_ENTITY)

    def device(self, device_id):
        """Return device representation."""
        return self._client.device(device_id)

    def is_available(self, device_id):
        """Return device availability."""
        if not self._is_available:
            return False
        return device_id in self._client.device_ids

    async def remove_webhook(self):
        """Remove the session webhook."""
        return await self._client.remove_webhook()

    @property
    def homes(self):
        """Return known homes."""
        return self._client.homes

    async def async_alarm_disarm(self, home_id):
        """Send alarm disarm command."""
        return await self._client.alarm_disarm(home_id)

    async def async_alarm_arm(self, home_id):
        """Send alarm arm command."""
        return await self._client.alarm_arm(home_id)


class MinutPointEntity(Entity):
    """Base Entity used by the sensors."""

    def __init__(self, point_client, device_id, device_class):
        """Initialize the entity."""
        self._async_unsub_dispatcher_connect = None
        self._client = point_client
        self._id = device_id
        self._name = self.device.name
        self._device_class = device_class
        self._updated = utc_from_timestamp(0)
        self._value = None

    def __str__(self):
        """Return string representation of device."""
        return f"MinutPoint {self.name}"

    async def async_added_to_opp(self):
        """Call when entity is added to.opp."""
        _LOGGER.debug("Created device %s", self)
        self._async_unsub_dispatcher_connect = async_dispatcher_connect(
            self.opp, SIGNAL_UPDATE_ENTITY, self._update_callback
        )
        await self._update_callback()

    async def async_will_remove_from_opp(self):
        """Disconnect dispatcher listener when removed."""
        if self._async_unsub_dispatcher_connect:
            self._async_unsub_dispatcher_connect()

    async def _update_callback(self):
        """Update the value of the sensor."""

    @property
    def available(self):
        """Return true if device is not offline."""
        return self._client.is_available(self.device_id)

    @property
    def device(self):
        """Return the representation of the device."""
        return self._client.device(self.device_id)

    @property
    def device_class(self):
        """Return the device class."""
        return self._device_class

    @property
    def device_id(self):
        """Return the id of the device."""
        return self._id

    @property
    def device_state_attributes(self):
        """Return status of device."""
        attrs = self.device.device_status
        attrs["last_heard_from"] = as_local(self.last_update).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        return attrs

    @property
    def device_info(self):
        """Return a device description for device registry."""
        device = self.device.device
        return {
            "connections": {("mac", device["device_mac"])},
            "identifieres": device["device_id"],
            "manufacturer": "Minut",
            "model": f"Point v{device['hardware_version']}",
            "name": device["description"],
            "sw_version": device["firmware"]["installed"],
            "via_device": (DOMAIN, device["home"]),
        }

    @property
    def name(self):
        """Return the display name of this device."""
        return f"{self._name} {self.device_class.capitalize()}"

    @property
    def is_updated(self):
        """Return true if sensor have been updated."""
        return self.last_update > self._updated

    @property
    def last_update(self):
        """Return the last_update time for the device."""
        last_update = parse_datetime(self.device.last_update)
        return last_update

    @property
    def should_poll(self):
        """No polling needed for point."""
        return False

    @property
    def unique_id(self):
        """Return the unique id of the sensor."""
        return f"point.{self._id}-{self.device_class}"

    @property
    def value(self):
        """Return the sensor value."""
        return self._value
