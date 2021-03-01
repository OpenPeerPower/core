"""Integration to UniFi controllers and its various features."""
from openpeerpower.const import EVENT_OPENPEERPOWER_STOP
from openpeerpower.core import callback
from openpeerpower.helpers.device_registry import CONNECTION_NETWORK_MAC

from .const import (
    ATTR_MANUFACTURER,
    CONF_CONTROLLER,
    DOMAIN as UNIFI_DOMAIN,
    LOGGER,
    UNIFI_WIRELESS_CLIENTS,
)
from .controller import UniFiController

SAVE_DELAY = 10
STORAGE_KEY = "unifi_data"
STORAGE_VERSION = 1


async def async_setup(opp, config):
    """Component doesn't support configuration through configuration.yaml."""
    opp.data[UNIFI_WIRELESS_CLIENTS] = wireless_clients = UnifiWirelessClients(opp)
    await wireless_clients.async_load()

    return True


async def async_setup_entry(opp, config_entry):
    """Set up the UniFi component."""
    opp.data.setdefault(UNIFI_DOMAIN, {})

    # Flat configuration was introduced with 2021.3
    await async_flatten_entry_data(opp, config_entry)

    controller = UniFiController(opp, config_entry)
    if not await controller.async_setup():
        return False

    # Unique ID was introduced with 2021.3
    if config_entry.unique_id is None:
        opp.config_entries.async_update_entry(
            config_entry, unique_id=controller.site_id
        )

    opp.data[UNIFI_DOMAIN][config_entry.entry_id] = controller

    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, controller.shutdown)

    LOGGER.debug("UniFi config options %s", config_entry.options)

    if controller.mac is None:
        return True

    device_registry = await opp.helpers.device_registry.async_get_registry()
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(CONNECTION_NETWORK_MAC, controller.mac)},
        default_manufacturer=ATTR_MANUFACTURER,
        default_model="UniFi Controller",
        default_name="UniFi Controller",
    )

    return True


async def async_unload_entry(opp, config_entry):
    """Unload a config entry."""
    controller = opp.data[UNIFI_DOMAIN].pop(config_entry.entry_id)
    return await controller.async_reset()


async def async_flatten_entry_data(opp, config_entry):
    """Simpler configuration structure for entry data.

    Keep controller key layer in case user rollbacks.
    """

    data: dict = {**config_entry.data, **config_entry.data[CONF_CONTROLLER]}
    if config_entry.data != data:
        opp.config_entries.async_update_entry(config_entry, data=data)


class UnifiWirelessClients:
    """Class to store clients known to be wireless.

    This is needed since wireless devices going offline might get marked as wired by UniFi.
    """

    def __init__(self, opp):
        """Set up client storage."""
        self.opp = opp
        self.data = {}
        self._store = opp.helpers.storage.Store(STORAGE_VERSION, STORAGE_KEY)

    async def async_load(self):
        """Load data from file."""
        data = await self._store.async_load()

        if data is not None:
            self.data = data

    @callback
    def get_data(self, config_entry):
        """Get data related to a specific controller."""
        data = self.data.get(config_entry.entry_id, {"wireless_devices": []})
        return set(data["wireless_devices"])

    @callback
    def update_data(self, data, config_entry):
        """Update data and schedule to save to file."""
        self.data[config_entry.entry_id] = {"wireless_devices": list(data)}
        self._store.async_delay_save(self._data_to_save, SAVE_DELAY)

    @callback
    def _data_to_save(self):
        """Return data of UniFi wireless clients to store in a file."""
        return self.data
