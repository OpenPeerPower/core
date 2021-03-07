"""Support for HLK-SW16 relay switches."""
import logging

from hlk_sw16 import create_hlk_sw16_connection
import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT
from openpeerpower.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_SWITCHES
from openpeerpower.core import callback
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from openpeerpower.helpers.entity import Entity

from .const import (
    CONNECTION_TIMEOUT,
    DEFAULT_KEEP_ALIVE_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_RECONNECT_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

DATA_DEVICE_REGISTER = "hlk_sw16_device_register"
DATA_DEVICE_LISTENER = "hlk_sw16_device_listener"

SWITCH_SCHEMA = vol.Schema({vol.Optional(CONF_NAME): cv.string})

RELAY_ID = vol.All(
    vol.Any(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, "a", "b", "c", "d", "e", "f"), vol.Coerce(str)
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                cv.string: vol.Schema(
                    {
                        vol.Required(CONF_HOST): cv.string,
                        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                        vol.Required(CONF_SWITCHES): vol.Schema(
                            {RELAY_ID: SWITCH_SCHEMA}
                        ),
                    }
                )
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Component setup, do nothing."""
    if DOMAIN not in config:
        return True

    for device_id in config[DOMAIN]:
        conf = config[DOMAIN][device_id]
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data={CONF_HOST: conf[CONF_HOST], CONF_PORT: conf[CONF_PORT]},
            )
        )
    return True


async def async_setup_entry(opp, entry):
    """Set up the HLK-SW16 switch."""
    opp.data.setdefault(DOMAIN, {})
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    address = f"{host}:{port}"

    opp.data[DOMAIN][entry.entry_id] = {}

    @callback
    def disconnected():
        """Schedule reconnect after connection has been lost."""
        _LOGGER.warning("HLK-SW16 %s disconnected", address)
        async_dispatcher_send(opp, f"hlk_sw16_device_available_{entry.entry_id}", False)

    @callback
    def reconnected():
        """Schedule reconnect after connection has been lost."""
        _LOGGER.warning("HLK-SW16 %s connected", address)
        async_dispatcher_send(opp, f"hlk_sw16_device_available_{entry.entry_id}", True)

    async def connect():
        """Set up connection and hook it into OP for reconnect/shutdown."""
        _LOGGER.info("Initiating HLK-SW16 connection to %s", address)

        client = await create_hlk_sw16_connection(
            host=host,
            port=port,
            disconnect_callback=disconnected,
            reconnect_callback=reconnected,
            loop=opp.loop,
            timeout=CONNECTION_TIMEOUT,
            reconnect_interval=DEFAULT_RECONNECT_INTERVAL,
            keep_alive_interval=DEFAULT_KEEP_ALIVE_INTERVAL,
        )

        opp.data[DOMAIN][entry.entry_id][DATA_DEVICE_REGISTER] = client

        # Load entities
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, "switch")
        )

        _LOGGER.info("Connected to HLK-SW16 device: %s", address)

    opp.loop.create_task(connect())

    return True


async def async_unload_entry(opp, entry):
    """Unload a config entry."""
    client = opp.data[DOMAIN][entry.entry_id].pop(DATA_DEVICE_REGISTER)
    client.stop()
    unload_ok = await opp.config_entries.async_forward_entry_unload(entry, "switch")

    if unload_ok:
        if opp.data[DOMAIN][entry.entry_id]:
            opp.data[DOMAIN].pop(entry.entry_id)
        if not opp.data[DOMAIN]:
            opp.data.pop(DOMAIN)
    return unload_ok


class SW16Device(Entity):
    """Representation of a HLK-SW16 device.

    Contains the common logic for HLK-SW16 entities.
    """

    def __init__(self, device_port, entry_id, client):
        """Initialize the device."""
        # HLK-SW16 specific attributes for every component type
        self._entry_id = entry_id
        self._device_port = device_port
        self._is_on = None
        self._client = client
        self._name = device_port

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._entry_id}_{self._device_port}"

    @callback
    def handle_event_callback(self, event):
        """Propagate changes through ha."""
        _LOGGER.debug("Relay %s new state callback: %r", self.unique_id, event)
        self._is_on = event
        self.async_write_op_state()

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def name(self):
        """Return a name for the device."""
        return self._name

    @property
    def available(self):
        """Return True if entity is available."""
        return bool(self._client.is_connected)

    @callback
    def _availability_callback(self, availability):
        """Update availability state."""
        self.async_write_op_state()

    async def async_added_to_opp(self):
        """Register update callback."""
        self._client.register_status_callback(
            self.handle_event_callback, self._device_port
        )
        self._is_on = await self._client.status(self._device_port)
        self.async_on_remove(
            async_dispatcher_connect(
                self.opp,
                f"hlk_sw16_device_available_{self._entry_id}",
                self._availability_callback,
            )
        )
