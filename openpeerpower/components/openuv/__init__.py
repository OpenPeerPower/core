"""Support for UV data from openuv.io."""
import asyncio

from pyopenuv import Client
from pyopenuv.errors import OpenUvError

from openpeerpower.const import (
    ATTR_ATTRIBUTION,
    CONF_API_KEY,
    CONF_BINARY_SENSORS,
    CONF_ELEVATION,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_SENSORS,
)
from openpeerpower.core import callback
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import aiohttp_client
from openpeerpower.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from openpeerpower.helpers.entity import Entity
from openpeerpower.helpers.service import verify_domain_control

from .const import (
    DATA_CLIENT,
    DATA_LISTENER,
    DATA_PROTECTION_WINDOW,
    DATA_UV,
    DOMAIN,
    LOGGER,
)

DEFAULT_ATTRIBUTION = "Data provided by OpenUV"

NOTIFICATION_ID = "openuv_notification"
NOTIFICATION_TITLE = "OpenUV Component Setup"

TOPIC_UPDATE = f"{DOMAIN}_data_update"

PLATFORMS = ["binary_sensor", "sensor"]


async def async_setup(opp, config):
    """Set up the OpenUV component."""
    opp.data[DOMAIN] = {DATA_CLIENT: {}, DATA_LISTENER: {}}
    return True


async def async_setup_entry(opp, config_entry):
    """Set up OpenUV as config entry."""
    _verify_domain_control = verify_domain_control(opp, DOMAIN)

    try:
        websession = aiohttp_client.async_get_clientsession(opp)
        openuv = OpenUV(
            Client(
                config_entry.data[CONF_API_KEY],
                config_entry.data.get(CONF_LATITUDE, opp.config.latitude),
                config_entry.data.get(CONF_LONGITUDE, opp.config.longitude),
                websession,
                altitude=config_entry.data.get(CONF_ELEVATION, opp.config.elevation),
            )
        )
        await openuv.async_update()
        opp.data[DOMAIN][DATA_CLIENT][config_entry.entry_id] = openuv
    except OpenUvError as err:
        LOGGER.error("Config entry failed: %s", err)
        raise ConfigEntryNotReady from err

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    @_verify_domain_control
    async def update_data(service):
        """Refresh all OpenUV data."""
        LOGGER.debug("Refreshing all OpenUV data")
        await openuv.async_update()
        async_dispatcher_send(opp, TOPIC_UPDATE)

    @_verify_domain_control
    async def update_uv_index_data(service):
        """Refresh OpenUV UV index data."""
        LOGGER.debug("Refreshing OpenUV UV index data")
        await openuv.async_update_uv_index_data()
        async_dispatcher_send(opp, TOPIC_UPDATE)

    @_verify_domain_control
    async def update_protection_data(service):
        """Refresh OpenUV protection window data."""
        LOGGER.debug("Refreshing OpenUV protection window data")
        await openuv.async_update_protection_data()
        async_dispatcher_send(opp, TOPIC_UPDATE)

    for service, method in [
        ("update_data", update_data),
        ("update_uv_index_data", update_uv_index_data),
        ("update_protection_data", update_protection_data),
    ]:
        opp.services.async_register(DOMAIN, service, method)

    return True


async def async_unload_entry(opp, config_entry):
    """Unload an OpenUV config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(config_entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        opp.data[DOMAIN][DATA_CLIENT].pop(config_entry.entry_id)

    return unload_ok


async def async_migrate_entry(opp, config_entry):
    """Migrate the config entry upon new versions."""
    version = config_entry.version
    data = {**config_entry.data}

    LOGGER.debug("Migrating from version %s", version)

    # 1 -> 2: Remove unused condition data:
    if version == 1:
        data.pop(CONF_BINARY_SENSORS, None)
        data.pop(CONF_SENSORS, None)
        version = config_entry.version = 2
        opp.config_entries.async_update_entry(config_entry, data=data)
        LOGGER.debug("Migration to version %s successful", version)

    return True


class OpenUV:
    """Define a generic OpenUV object."""

    def __init__(self, client):
        """Initialize."""
        self.client = client
        self.data = {}

    async def async_update_protection_data(self):
        """Update binary sensor (protection window) data."""
        try:
            resp = await self.client.uv_protection_window()
            self.data[DATA_PROTECTION_WINDOW] = resp["result"]
        except OpenUvError as err:
            LOGGER.error("Error during protection data update: %s", err)
            self.data[DATA_PROTECTION_WINDOW] = {}

    async def async_update_uv_index_data(self):
        """Update sensor (uv index, etc) data."""
        try:
            data = await self.client.uv_index()
            self.data[DATA_UV] = data
        except OpenUvError as err:
            LOGGER.error("Error during uv index data update: %s", err)
            self.data[DATA_UV] = {}

    async def async_update(self):
        """Update sensor/binary sensor data."""
        tasks = [self.async_update_protection_data(), self.async_update_uv_index_data()]
        await asyncio.gather(*tasks)


class OpenUvEntity(Entity):
    """Define a generic OpenUV entity."""

    def __init__(self, openuv):
        """Initialize."""
        self._attrs = {ATTR_ATTRIBUTION: DEFAULT_ATTRIBUTION}
        self._available = True
        self._name = None
        self.openuv = openuv

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attrs

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    async def async_added_to_opp(self):
        """Register callbacks."""

        @callback
        def update():
            """Update the state."""
            self.update_from_latest_data()
            self.async_write_op_state()

        self.async_on_remove(async_dispatcher_connect(self.opp, TOPIC_UPDATE, update))

        self.update_from_latest_data()

    def update_from_latest_data(self):
        """Update the sensor using the latest data."""
        raise NotImplementedError
