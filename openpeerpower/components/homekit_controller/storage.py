"""Helpers for HomeKit data stored in OPP storage."""

from openpeerpower.core import callback
from openpeerpower.helpers.storage import Store

from .const import DOMAIN

ENTITY_MAP_STORAGE_KEY = f"{DOMAIN}-entity-map"
ENTITY_MAP_STORAGE_VERSION = 1
ENTITY_MAP_SAVE_DELAY = 10


class EntityMapStorage:
    """
    Holds a cache of entity structure data from a paired HomeKit device.

    HomeKit has a cacheable entity map that describes how an IP or BLE
    endpoint is structured. This object holds the latest copy of that data.

    An endpoint is made of accessories, services and characteristics. It is
    safe to cache this data until the c# discovery data changes.

    Caching this data means we can add HomeKit devices to OPP immediately at
    start even if discovery hasn't seen them yet or they are out of range. It
    is also important for BLE devices - accessing the entity structure is
    very slow for these devices.
    """

    def __init__(self, opp):
        """Create a new entity map store."""
        self.opp = opp
        self.store = Store(opp, ENTITY_MAP_STORAGE_VERSION, ENTITY_MAP_STORAGE_KEY)
        self.storage_data = {}

    async def async_initialize(self):
        """Get the pairing cache data."""
        raw_storage = await self.store.async_load()
        if not raw_storage:
            # There is no cached data about HomeKit devices yet
            return

        self.storage_data = raw_storage.get("pairings", {})

    def get_map(self, homekit_id):
        """Get a pairing cache item."""
        return self.storage_data.get(homekit_id)

    @callback
    def async_create_or_update_map(self, homekit_id, config_num, accessories):
        """Create a new pairing cache."""
        data = {"config_num": config_num, "accessories": accessories}
        self.storage_data[homekit_id] = data
        self._async_schedule_save()
        return data

    @callback
    def async_delete_map(self, homekit_id):
        """Delete pairing cache."""
        if homekit_id not in self.storage_data:
            return

        self.storage_data.pop(homekit_id)
        self._async_schedule_save()

    @callback
    def _async_schedule_save(self):
        """Schedule saving the entity map cache."""
        self.store.async_delay_save(self._data_to_save, ENTITY_MAP_SAVE_DELAY)

    @callback
    def _data_to_save(self):
        """Return data of entity map to store in a file."""
        return {"pairings": self.storage_data}
