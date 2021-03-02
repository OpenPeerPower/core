"""Component to embed Aqualink devices."""
import asyncio
from functools import wraps
import logging
from typing import Any, Dict

import aiohttp.client_exceptions
from iaqualink import (
    AqualinkBinarySensor,
    AqualinkClient,
    AqualinkDevice,
    AqualinkLight,
    AqualinkLoginException,
    AqualinkSensor,
    AqualinkThermostat,
    AqualinkToggle,
)
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from openpeerpower.components.climate import DOMAIN as CLIMATE_DOMAIN
from openpeerpower.components.light import DOMAIN as LIGHT_DOMAIN
from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.components.switch import DOMAIN as SWITCH_DOMAIN
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from openpeerpower.helpers.entity import Entity
from openpeerpower.helpers.event import async_track_time_interval
from openpeerpower.helpers.typing import ConfigType, OpenPeerPowerType

from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

ATTR_CONFIG = "config"
PARALLEL_UPDATES = 0

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp: OpenPeerPowerType, config: ConfigType) -> None:
    """Set up the Aqualink component."""
    conf = config.get(DOMAIN)

    opp.data[DOMAIN] = {}

    if conf is not None:
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=conf
            )
        )

    return True


async def async_setup_entry(opp: OpenPeerPowerType, entry: ConfigEntry) -> None:
    """Set up Aqualink from a config entry."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    # These will contain the initialized devices
    binary_sensors = opp.data[DOMAIN][BINARY_SENSOR_DOMAIN] = []
    climates = opp.data[DOMAIN][CLIMATE_DOMAIN] = []
    lights = opp.data[DOMAIN][LIGHT_DOMAIN] = []
    sensors = opp.data[DOMAIN][SENSOR_DOMAIN] = []
    switches = opp.data[DOMAIN][SWITCH_DOMAIN] = []

    session = async_get_clientsession(opp)
    aqualink = AqualinkClient(username, password, session)
    try:
        await aqualink.login()
    except AqualinkLoginException as login_exception:
        _LOGGER.error("Failed to login: %s", login_exception)
        return False
    except (
        asyncio.TimeoutError,
        aiohttp.client_exceptions.ClientConnectorError,
    ) as aio_exception:
        _LOGGER.warning("Exception raised while attempting to login: %s", aio_exception)
        raise ConfigEntryNotReady from aio_exception

    systems = await aqualink.get_systems()
    systems = list(systems.values())
    if not systems:
        _LOGGER.error("No systems detected or supported")
        return False

    # Only supporting the first system for now.
    devices = await systems[0].get_devices()

    for dev in devices.values():
        if isinstance(dev, AqualinkThermostat):
            climates += [dev]
        elif isinstance(dev, AqualinkLight):
            lights += [dev]
        elif isinstance(dev, AqualinkBinarySensor):
            binary_sensors += [dev]
        elif isinstance(dev, AqualinkSensor):
            sensors += [dev]
        elif isinstance(dev, AqualinkToggle):
            switches += [dev]

    forward_setup = opp.config_entries.async_forward_entry_setup
    if binary_sensors:
        _LOGGER.debug("Got %s binary sensors: %s", len(binary_sensors), binary_sensors)
        opp.async_create_task(forward_setup(entry, BINARY_SENSOR_DOMAIN))
    if climates:
        _LOGGER.debug("Got %s climates: %s", len(climates), climates)
        opp.async_create_task(forward_setup(entry, CLIMATE_DOMAIN))
    if lights:
        _LOGGER.debug("Got %s lights: %s", len(lights), lights)
        opp.async_create_task(forward_setup(entry, LIGHT_DOMAIN))
    if sensors:
        _LOGGER.debug("Got %s sensors: %s", len(sensors), sensors)
        opp.async_create_task(forward_setup(entry, SENSOR_DOMAIN))
    if switches:
        _LOGGER.debug("Got %s switches: %s", len(switches), switches)
        opp.async_create_task(forward_setup(entry, SWITCH_DOMAIN))

    async def _async_systems_update(now):
        """Refresh internal state for all systems."""
        prev = systems[0].last_run_success

        await systems[0].update()
        success = systems[0].last_run_success

        if not success and prev:
            _LOGGER.warning("Failed to refresh iAqualink state")
        elif success and not prev:
            _LOGGER.warning("Reconnected to iAqualink")

        async_dispatcher_send(opp, DOMAIN)

    async_track_time_interval(opp, _async_systems_update, UPDATE_INTERVAL)

    return True


async def async_unload_entry(opp: OpenPeerPowerType, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    forward_unload = opp.config_entries.async_forward_entry_unload

    tasks = []

    if opp.data[DOMAIN][BINARY_SENSOR_DOMAIN]:
        tasks += [forward_unload(entry, BINARY_SENSOR_DOMAIN)]
    if opp.data[DOMAIN][CLIMATE_DOMAIN]:
        tasks += [forward_unload(entry, CLIMATE_DOMAIN)]
    if opp.data[DOMAIN][LIGHT_DOMAIN]:
        tasks += [forward_unload(entry, LIGHT_DOMAIN)]
    if opp.data[DOMAIN][SENSOR_DOMAIN]:
        tasks += [forward_unload(entry, SENSOR_DOMAIN)]
    if opp.data[DOMAIN][SWITCH_DOMAIN]:
        tasks += [forward_unload(entry, SWITCH_DOMAIN)]

    opp.data[DOMAIN].clear()

    return all(await asyncio.gather(*tasks))


def refresh_system(func):
    """Force update all entities after state change."""

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        """Call decorated function and send update signal to all entities."""
        await func(self, *args, **kwargs)
        async_dispatcher_send(self.opp, DOMAIN)

    return wrapper


class AqualinkEntity(Entity):
    """Abstract class for all Aqualink platforms.

    Entity state is updated via the interval timer within the integration.
    Any entity state change via the iaqualink library triggers an internal
    state refresh which is then propagated to all the entities in the system
    via the refresh_system decorator above to the _update_callback in this
    class.
    """

    def __init__(self, dev: AqualinkDevice):
        """Initialize the entity."""
        self.dev = dev

    async def async_added_to_opp(self) -> None:
        """Set up a listener when this entity is added to HA."""
        self.async_on_remove(
            async_dispatcher_connect(self.opp, DOMAIN, self.async_write_op_state)
        )

    @property
    def should_poll(self) -> bool:
        """Return False as entities shouldn't be polled.

        Entities are checked periodically as the integration runs periodic
        updates on a timer.
        """
        return False

    @property
    def unique_id(self) -> str:
        """Return a unique identifier for this entity."""
        return f"{self.dev.system.serial}_{self.dev.name}"

    @property
    def assumed_state(self) -> bool:
        """Return whether the state is based on actual reading from the device."""
        return not self.dev.system.last_run_success

    @property
    def available(self) -> bool:
        """Return whether the device is available or not."""
        return self.dev.system.online

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return the device info."""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "model": self.dev.__class__.__name__.replace("Aqualink", ""),
            "manufacturer": "Jandy",
            "via_device": (DOMAIN, self.dev.system.serial),
        }
