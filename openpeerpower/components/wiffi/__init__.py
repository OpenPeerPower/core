"""Component for wiffi support."""
from datetime import timedelta
import errno
import logging

from wiffi import WiffiTcpServer

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_PORT, CONF_TIMEOUT
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import device_registry
from openpeerpower.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from openpeerpower.helpers.entity import Entity
from openpeerpower.helpers.event import async_track_time_interval
from openpeerpower.util.dt import utcnow

from .const import (
    CHECK_ENTITIES_SIGNAL,
    CREATE_ENTITY_SIGNAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    UPDATE_ENTITY_SIGNAL,
)

_LOGGER = logging.getLogger(__name__)


PLATFORMS = ["sensor", "binary_sensor"]


async def async_setup_entry(opp: OpenPeerPower, config_entry: ConfigEntry):
    """Set up wiffi from a config entry, config_entry contains data from config entry database."""
    if not config_entry.update_listeners:
        config_entry.add_update_listener(async_update_options)

    # create api object
    api = WiffiIntegrationApi(opp)
    api.async_setup(config_entry)

    # store api object
    opp.data.setdefault(DOMAIN, {})[config_entry.entry_id] = api

    try:
        await api.server.start_server()
    except OSError as exc:
        if exc.errno != errno.EADDRINUSE:
            _LOGGER.error("Start_server failed, errno: %d", exc.errno)
            return False
        _LOGGER.error("Port %s already in use", config_entry.data[CONF_PORT])
        raise ConfigEntryNotReady from exc

    opp.config_entries.async_setup_platforms(config_entry, PLATFORMS)

    return True


async def async_update_options(opp: OpenPeerPower, config_entry: ConfigEntry):
    """Update options."""
    await opp.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(opp: OpenPeerPower, config_entry: ConfigEntry):
    """Unload a config entry."""
    api: WiffiIntegrationApi = opp.data[DOMAIN][config_entry.entry_id]
    await api.server.close_server()

    unload_ok = await opp.config_entries.async_unload_platforms(config_entry, PLATFORMS)
    if unload_ok:
        api = opp.data[DOMAIN].pop(config_entry.entry_id)
        api.shutdown()

    return unload_ok


def generate_unique_id(device, metric):
    """Generate a unique string for the entity."""
    return f"{device.mac_address.replace(':', '')}-{metric.name}"


class WiffiIntegrationApi:
    """API object for wiffi handling. Stored in opp.data."""

    def __init__(self, opp):
        """Initialize the instance."""
        self._opp = opp
        self._server = None
        self._known_devices = {}
        self._periodic_callback = None

    def async_setup(self, config_entry):
        """Set up api instance."""
        self._server = WiffiTcpServer(config_entry.data[CONF_PORT], self)
        self._periodic_callback = async_track_time_interval(
            self._opp, self._periodic_tick, timedelta(seconds=10)
        )

    def shutdown(self):
        """Shutdown wiffi api.

        Remove listener for periodic callbacks.
        """
        remove_listener = self._periodic_callback
        if remove_listener is not None:
            remove_listener()

    async def __call__(self, device, metrics):
        """Process callback from TCP server if new data arrives from a device."""
        if device.mac_address not in self._known_devices:
            # add empty set for new device
            self._known_devices[device.mac_address] = set()

        for metric in metrics:
            if metric.id not in self._known_devices[device.mac_address]:
                self._known_devices[device.mac_address].add(metric.id)
                async_dispatcher_send(self._opp, CREATE_ENTITY_SIGNAL, device, metric)
            else:
                async_dispatcher_send(
                    self._opp,
                    f"{UPDATE_ENTITY_SIGNAL}-{generate_unique_id(device, metric)}",
                    device,
                    metric,
                )

    @property
    def server(self):
        """Return TCP server instance for start + close."""
        return self._server

    @callback
    def _periodic_tick(self, now=None):
        """Check if any entity has timed out because it has not been updated."""
        async_dispatcher_send(self._opp, CHECK_ENTITIES_SIGNAL)


class WiffiEntity(Entity):
    """Common functionality for all wiffi entities."""

    def __init__(self, device, metric, options):
        """Initialize the base elements of a wiffi entity."""
        self._id = generate_unique_id(device, metric)
        self._device_info = {
            "connections": {
                (device_registry.CONNECTION_NETWORK_MAC, device.mac_address)
            },
            "identifiers": {(DOMAIN, device.mac_address)},
            "manufacturer": "stall.biz",
            "name": f"{device.moduletype} {device.mac_address}",
            "model": device.moduletype,
            "sw_version": device.sw_version,
        }
        self._name = metric.description
        self._expiration_date = None
        self._value = None
        self._timeout = options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)

    async def async_added_to_opp(self):
        """Entity has been added to opp."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.opp,
                f"{UPDATE_ENTITY_SIGNAL}-{self._id}",
                self._update_value_callback,
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.opp, CHECK_ENTITIES_SIGNAL, self._check_expiration_date
            )
        )

    @property
    def should_poll(self):
        """Disable polling because data driven ."""
        return False

    @property
    def device_info(self):
        """Return wiffi device info which is shared between all entities of a device."""
        return self._device_info

    @property
    def unique_id(self):
        """Return unique id for entity."""
        return self._id

    @property
    def name(self):
        """Return entity name."""
        return self._name

    @property
    def available(self):
        """Return true if value is valid."""
        return self._value is not None

    def reset_expiration_date(self):
        """Reset value expiration date.

        Will be called by derived classes after a value update has been received.
        """
        self._expiration_date = utcnow() + timedelta(minutes=self._timeout)

    @callback
    def _update_value_callback(self, device, metric):
        """Update the value of the entity."""

    @callback
    def _check_expiration_date(self):
        """Periodically check if entity value has been updated.

        If there are no more updates from the wiffi device, the value will be
        set to unavailable.
        """
        if (
            self._value is not None
            and self._expiration_date is not None
            and utcnow() > self._expiration_date
        ):
            self._value = None
            self.async_write_op_state()
