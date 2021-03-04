"""The WiLight integration."""
import asyncio

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.entity import Entity

from .parent_device import WiLightParent

DOMAIN = "wilight"

# List the platforms that you want to support.
PLATFORMS = ["cover", "fan", "light"]


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the WiLight with Config Flow component."""

    opp.data[DOMAIN] = {}

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up a wilight config entry."""

    parent = WiLightParent(opp, entry)

    if not await parent.async_setup():
        raise ConfigEntryNotReady

    opp.data[DOMAIN][entry.entry_id] = parent

    # Set up all platforms for this device/entry.
    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload WiLight config entry."""

    # Unload entities for this entry/device.
    await asyncio.gather(
        *(
            opp.config_entries.async_forward_entry_unload(entry, platform)
            for platform in PLATFORMS
        )
    )

    # Cleanup
    parent = opp.data[DOMAIN][entry.entry_id]
    await parent.async_reset()
    del opp.data[DOMAIN][entry.entry_id]

    return True


class WiLightDevice(Entity):
    """Representation of a WiLight device.

    Contains the common logic for WiLight entities.
    """

    def __init__(self, api_device, index, item_name):
        """Initialize the device."""
        # WiLight specific attributes for every component type
        self._device_id = api_device.device_id
        self._sw_version = api_device.swversion
        self._client = api_device.client
        self._model = api_device.model
        self._name = item_name
        self._index = index
        self._unique_id = f"{self._device_id}_{self._index}"
        self._status = {}

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def name(self):
        """Return a name for this WiLight item."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID for this WiLight item."""
        return self._unique_id

    @property
    def device_info(self):
        """Return the device info."""
        return {
            "name": self._name,
            "identifiers": {(DOMAIN, self._unique_id)},
            "model": self._model,
            "manufacturer": "WiLight",
            "sw_version": self._sw_version,
            "via_device": (DOMAIN, self._device_id),
        }

    @property
    def available(self):
        """Return True if entity is available."""
        return bool(self._client.is_connected)

    @callback
    def handle_event_callback(self, states):
        """Propagate changes through ha."""
        self._status = states
        self.async_write_op_state()

    async def async_update(self):
        """Synchronize state with api_device."""
        await self._client.status(self._index)

    async def async_added_to_opp(self):
        """Register update callback."""
        self._client.register_status_callback(self.handle_event_callback, self._index)
        await self._client.status(self._index)
