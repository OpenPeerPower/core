"""The Keenetic Client class."""
import logging

from openpeerpower.components.binary_sensor import (
    DEVICE_CLASS_CONNECTIVITY,
    BinarySensorEntity,
)
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.dispatcher import async_dispatcher_connect

from . import KeeneticRouter
from .const import DOMAIN, ROUTER

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    opp: OpenPeerPower, config_entry: ConfigEntry, async_add_entities
):
    """Set up device tracker for Keenetic NDMS2 component."""
    router: KeeneticRouter = opp.data[DOMAIN][config_entry.entry_id][ROUTER]

    async_add_entities([RouterOnlineBinarySensor(router)])


class RouterOnlineBinarySensor(BinarySensorEntity):
    """Representation router connection status."""

    def __init__(self, router: KeeneticRouter):
        """Initialize the APCUPSd binary device."""
        self._router = router

    @property
    def name(self):
        """Return the name of the online status sensor."""
        return f"{self._router.name} Online"

    @property
    def unique_id(self) -> str:
        """Return a unique identifier for this device."""
        return f"online_{self._router.config_entry.entry_id}"

    @property
    def is_on(self):
        """Return true if the UPS is online, else false."""
        return self._router.available

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return DEVICE_CLASS_CONNECTIVITY

    @property
    def should_poll(self) -> bool:
        """Return False since entity pushes its state to HA."""
        return False

    @property
    def device_info(self):
        """Return a client description for device registry."""
        return self._router.device_info

    async def async_added_to_opp(self):
        """Client entity created."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.opp,
                self._router.signal_update,
                self.async_write_op_state,
            )
        )
