"""Support for Telldus Live."""
import asyncio
from functools import partial
import logging

from tellduslive import DIM, TURNON, UP, Session
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.const import CONF_SCAN_INTERVAL
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.dispatcher import async_dispatcher_send
from openpeerpower.helpers.event import async_call_later

from .const import (
    CONF_HOST,
    DOMAIN,
    KEY_SCAN_INTERVAL,
    KEY_SESSION,
    MIN_UPDATE_INTERVAL,
    NOT_SO_PRIVATE_KEY,
    PUBLIC_KEY,
    SCAN_INTERVAL,
    SIGNAL_UPDATE_ENTITY,
    TELLDUS_DISCOVERY_NEW,
)

APPLICATION_NAME = "Open Peer Power"

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_HOST, default=DOMAIN): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL): vol.All(
                    cv.time_period, vol.Clamp(min=MIN_UPDATE_INTERVAL)
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

DATA_CONFIG_ENTRY_LOCK = "tellduslive_config_entry_lock"
CONFIG_ENTRY_IS_SETUP = "telldus_config_entry_is_setup"

NEW_CLIENT_TASK = "telldus_new_client_task"
INTERVAL_TRACKER = f"{DOMAIN}_INTERVAL"


async def async_setup_entry(opp, entry):
    """Create a tellduslive session."""

    conf = entry.data[KEY_SESSION]

    if CONF_HOST in conf:
        # Session(**conf) does blocking IO when
        # communicating with local devices.
        session = await opp.async_add_executor_job(partial(Session, **conf))
    else:
        session = Session(
            PUBLIC_KEY, NOT_SO_PRIVATE_KEY, application=APPLICATION_NAME, **conf
        )

    if not session.is_authorized:
        _LOGGER.error("Authentication Error")
        return False

    opp.data[DATA_CONFIG_ENTRY_LOCK] = asyncio.Lock()
    opp.data[CONFIG_ENTRY_IS_SETUP] = set()
    opp.data[NEW_CLIENT_TASK] = opp.loop.create_task(
        async_new_client(opp, session, entry)
    )

    return True


async def async_new_client(opp, session, entry):
    """Add the hubs associated with the current client to device_registry."""
    interval = entry.data[KEY_SCAN_INTERVAL]
    _LOGGER.debug("Update interval %s seconds", interval)
    client = TelldusLiveClient(opp, entry, session, interval)
    opp.data[DOMAIN] = client
    dev_reg = await opp.helpers.device_registry.async_get_registry()
    for hub in await client.async_get_hubs():
        _LOGGER.debug("Connected hub %s", hub["name"])
        dev_reg.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, hub["id"])},
            manufacturer="Telldus",
            name=hub["name"],
            model=hub["type"],
            sw_version=hub["version"],
        )
    await client.update()


async def async_setup(opp, config):
    """Set up the Telldus Live component."""
    if DOMAIN not in config:
        return True

    opp.async_create_task(
        opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={
                CONF_HOST: config[DOMAIN].get(CONF_HOST),
                KEY_SCAN_INTERVAL: config[DOMAIN][CONF_SCAN_INTERVAL],
            },
        )
    )
    return True


async def async_unload_entry(opp, config_entry):
    """Unload a config entry."""
    if not opp.data[NEW_CLIENT_TASK].done():
        opp.data[NEW_CLIENT_TASK].cancel()
    interval_tracker = opp.data.pop(INTERVAL_TRACKER)
    interval_tracker()
    await asyncio.wait(
        [
            opp.config_entries.async_forward_entry_unload(config_entry, platform)
            for platform in opp.data.pop(CONFIG_ENTRY_IS_SETUP)
        ]
    )
    del opp.data[DOMAIN]
    del opp.data[DATA_CONFIG_ENTRY_LOCK]
    return True


class TelldusLiveClient:
    """Get the latest data and update the states."""

    def __init__(self, opp, config_entry, session, interval):
        """Initialize the Tellus data object."""
        self._known_devices = set()
        self._device_infos = {}

        self._opp = opp
        self._config_entry = config_entry
        self._client = session
        self._interval = interval

    async def async_get_hubs(self):
        """Return hubs registered for the user."""
        clients = await self._opp.async_add_executor_job(self._client.get_clients)
        return clients or []

    def device_info(self, device_id):
        """Return device info."""
        return self._device_infos.get(device_id)

    @staticmethod
    def identify_device(device):
        """Find out what type of OP component to create."""
        if device.is_sensor:
            return "sensor"

        if device.methods & DIM:
            return "light"
        if device.methods & UP:
            return "cover"
        if device.methods & TURNON:
            return "switch"
        if device.methods == 0:
            return "binary_sensor"
        _LOGGER.warning("Unidentified device type (methods: %d)", device.methods)
        return "switch"

    async def _discover(self, device_id):
        """Discover the component."""
        device = self._client.device(device_id)
        component = self.identify_device(device)
        self._device_infos.update(
            {device_id: await self._opp.async_add_executor_job(device.info)}
        )
        async with self._opp.data[DATA_CONFIG_ENTRY_LOCK]:
            if component not in self._opp.data[CONFIG_ENTRY_IS_SETUP]:
                await self._opp.config_entries.async_forward_entry_setup(
                    self._config_entry, component
                )
                self._opp.data[CONFIG_ENTRY_IS_SETUP].add(component)
        device_ids = []
        if device.is_sensor:
            for item in device.items:
                device_ids.append((device.device_id, item.name, item.scale))
        else:
            device_ids.append(device_id)
        for _id in device_ids:
            async_dispatcher_send(
                self._opp, TELLDUS_DISCOVERY_NEW.format(component, DOMAIN), _id
            )

    async def update(self, *args):
        """Periodically poll the servers for current state."""
        try:
            if not await self._opp.async_add_executor_job(self._client.update):
                _LOGGER.warning("Failed request")
                return
            dev_ids = {dev.device_id for dev in self._client.devices}
            new_devices = dev_ids - self._known_devices
            # just await each discover as `gather` use up all HTTPAdapter pools
            for d_id in new_devices:
                await self._discover(d_id)
            self._known_devices |= new_devices
            async_dispatcher_send(self._opp, SIGNAL_UPDATE_ENTITY)
        finally:
            self._opp.data[INTERVAL_TRACKER] = async_call_later(
                self._opp, self._interval, self.update
            )

    def device(self, device_id):
        """Return device representation."""
        return self._client.device(device_id)

    def is_available(self, device_id):
        """Return device availability."""
        return device_id in self._client.device_ids
