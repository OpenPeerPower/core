"""Support for WeMo device discovery."""
from __future__ import annotations

import logging

import pywemo
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from openpeerpower.components.fan import DOMAIN as FAN_DOMAIN
from openpeerpower.components.light import DOMAIN as LIGHT_DOMAIN
from openpeerpower.components.switch import DOMAIN as SWITCH_DOMAIN
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_DISCOVERY, EVENT_OPENPEERPOWER_STOP
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.dispatcher import async_dispatcher_send
from openpeerpower.helpers.event import async_call_later
from openpeerpower.util.async_ import gather_with_concurrency

from .const import DOMAIN

# Max number of devices to initialize at once. This limit is in place to
# avoid tying up too many executor threads with WeMo device setup.
MAX_CONCURRENCY = 3

# Mapping from Wemo model_name to domain.
WEMO_MODEL_DISPATCH = {
    "Bridge": LIGHT_DOMAIN,
    "CoffeeMaker": SWITCH_DOMAIN,
    "Dimmer": LIGHT_DOMAIN,
    "Humidifier": FAN_DOMAIN,
    "Insight": SWITCH_DOMAIN,
    "LightSwitch": SWITCH_DOMAIN,
    "Maker": SWITCH_DOMAIN,
    "Motion": BINARY_SENSOR_DOMAIN,
    "OutdoorPlug": SWITCH_DOMAIN,
    "Sensor": BINARY_SENSOR_DOMAIN,
    "Socket": SWITCH_DOMAIN,
}

_LOGGER = logging.getLogger(__name__)


def coerce_host_port(value):
    """Validate that provided value is either just host or host:port.

    Returns (host, None) or (host, port) respectively.
    """
    host, _, port = value.partition(":")

    if not host:
        raise vol.Invalid("host cannot be empty")

    if port:
        port = cv.port(port)
    else:
        port = None

    return host, port


CONF_STATIC = "static"

DEFAULT_DISCOVERY = True

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_STATIC, default=[]): vol.Schema(
                    [vol.All(cv.string, coerce_host_port)]
                ),
                vol.Optional(CONF_DISCOVERY, default=DEFAULT_DISCOVERY): cv.boolean,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Set up for WeMo devices."""
    opp.data[DOMAIN] = {
        "config": config.get(DOMAIN, {}),
        "registry": None,
        "pending": {},
    }

    if DOMAIN in config:
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_IMPORT}
            )
        )

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up a wemo config entry."""
    config = opp.data[DOMAIN].pop("config")

    # Keep track of WeMo device subscriptions for push updates
    registry = opp.data[DOMAIN]["registry"] = pywemo.SubscriptionRegistry()
    await opp.async_add_executor_job(registry.start)
    static_conf = config.get(CONF_STATIC, [])
    wemo_dispatcher = WemoDispatcher(entry)
    wemo_discovery = WemoDiscovery(opp, wemo_dispatcher, static_conf)

    async def async_stop_wemo(event):
        """Shutdown Wemo subscriptions and subscription thread on exit."""
        _LOGGER.debug("Shutting down WeMo event subscriptions")
        await opp.async_add_executor_job(registry.stop)
        wemo_discovery.async_stop_discovery()

    entry.async_on_unload(
        opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, async_stop_wemo)
    )

    # Need to do this at least once in case statics are defined and discovery is disabled
    await wemo_discovery.discover_statics()

    if config.get(CONF_DISCOVERY, DEFAULT_DISCOVERY):
        await wemo_discovery.async_discover_and_schedule()

    return True


class WemoDispatcher:
    """Dispatch WeMo devices to the correct platform."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the WemoDispatcher."""
        self._config_entry = config_entry
        self._added_serial_numbers = set()
        self._loaded_components = set()

    @callback
    def async_add_unique_device(
        self, opp: OpenPeerPower, device: pywemo.WeMoDevice
    ) -> None:
        """Add a WeMo device to opp.if it has not already been added."""
        if device.serialnumber in self._added_serial_numbers:
            return

        component = WEMO_MODEL_DISPATCH.get(device.model_name, SWITCH_DOMAIN)

        # Three cases:
        # - First time we see component, we need to load it and initialize the backlog
        # - Component is being loaded, add to backlog
        # - Component is loaded, backlog is gone, dispatch discovery

        if component not in self._loaded_components:
            opp.data[DOMAIN]["pending"][component] = [device]
            self._loaded_components.add(component)
            opp.async_create_task(
                opp.config_entries.async_forward_entry_setup(
                    self._config_entry, component
                )
            )

        elif component in opp.data[DOMAIN]["pending"]:
            opp.data[DOMAIN]["pending"][component].append(device)

        else:
            async_dispatcher_send(
                opp,
                f"{DOMAIN}.{component}",
                device,
            )

        self._added_serial_numbers.add(device.serialnumber)


class WemoDiscovery:
    """Use SSDP to discover WeMo devices."""

    ADDITIONAL_SECONDS_BETWEEN_SCANS = 10
    MAX_SECONDS_BETWEEN_SCANS = 300

    def __init__(
        self,
        opp: OpenPeerPower,
        wemo_dispatcher: WemoDispatcher,
        static_config: list[tuple[[str, str | None]]],
    ) -> None:
        """Initialize the WemoDiscovery."""
        self._opp = opp
        self._wemo_dispatcher = wemo_dispatcher
        self._stop = None
        self._scan_delay = 0
        self._static_config = static_config

    async def async_discover_and_schedule(self, *_) -> None:
        """Periodically scan the network looking for WeMo devices."""
        _LOGGER.debug("Scanning network for WeMo devices")
        try:
            for device in await self._opp.async_add_executor_job(
                pywemo.discover_devices
            ):
                self._wemo_dispatcher.async_add_unique_device(self._opp, device)
            await self.discover_statics()

        finally:
            # Run discovery more frequently after opp.has just started.
            self._scan_delay = min(
                self._scan_delay + self.ADDITIONAL_SECONDS_BETWEEN_SCANS,
                self.MAX_SECONDS_BETWEEN_SCANS,
            )
            self._stop = async_call_later(
                self._opp,
                self._scan_delay,
                self.async_discover_and_schedule,
            )

    @callback
    def async_stop_discovery(self) -> None:
        """Stop the periodic background scanning."""
        if self._stop:
            self._stop()
            self._stop = None

    async def discover_statics(self):
        """Initialize or Re-Initialize connections to statically configured devices."""
        if self._static_config:
            _LOGGER.debug("Adding statically configured WeMo devices")
            for device in await gather_with_concurrency(
                MAX_CONCURRENCY,
                *[
                    self._opp.async_add_executor_job(validate_static_config, host, port)
                    for host, port in self._static_config
                ],
            ):
                if device:
                    self._wemo_dispatcher.async_add_unique_device(self._opp, device)


def validate_static_config(host, port):
    """Handle a static config."""
    url = pywemo.setup_url_for_address(host, port)

    if not url:
        _LOGGER.error(
            "Unable to get description url for WeMo at: %s",
            f"{host}:{port}" if port else host,
        )
        return None

    try:
        device = pywemo.discovery.device_from_description(url)
    except (
        pywemo.exceptions.ActionException,
        pywemo.exceptions.HTTPException,
    ) as err:
        _LOGGER.error("Unable to access WeMo at %s (%s)", url, err)
        return None

    return device
