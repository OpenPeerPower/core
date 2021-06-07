"""Support for exposing Open Peer Power via Zeroconf."""
from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from contextlib import suppress
import fnmatch
import ipaddress
import logging
import socket
from typing import Any, TypedDict, cast

import voluptuous as vol
from zeroconf import (
    InterfaceChoice,
    IPVersion,
    NonUniqueNameException,
    ServiceInfo,
    ServiceStateChange,
    Zeroconf,
)

from openpeerpower import config_entries, util
from openpeerpower.components import network
from openpeerpower.components.network.models import Adapter
from openpeerpower.const import (
    EVENT_OPENPEERPOWER_START,
    EVENT_OPENPEERPOWER_STARTED,
    EVENT_OPENPEERPOWER_STOP,
    __version__,
)
from openpeerpower.core import Event, OpenPeerPower, callback
from openpeerpower.data_entry_flow import FlowResult
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.network import NoURLAvailableError, get_url
from openpeerpower.loader import async_get_homekit, async_get_zeroconf, bind_opp

from .models import HaAsyncZeroconf, HaServiceBrowser, HaZeroconf
from .usage import install_multiple_zeroconf_catcher

_LOGGER = logging.getLogger(__name__)

DOMAIN = "zeroconf"

ZEROCONF_TYPE = "_open-peer-power._tcp.local."
HOMEKIT_TYPES = [
    "_hap._tcp.local.",
    # Thread based devices
    "_hap._udp.local.",
]

CONF_DEFAULT_INTERFACE = "default_interface"
CONF_IPV6 = "ipv6"
DEFAULT_DEFAULT_INTERFACE = True
DEFAULT_IPV6 = True

HOMEKIT_PAIRED_STATUS_FLAG = "sf"
HOMEKIT_MODEL = "md"

MDNS_TARGET_IP = "224.0.0.251"

# Property key=value has a max length of 255
# so we use 230 to leave space for key=
MAX_PROPERTY_VALUE_LEN = 230

# Dns label max length
MAX_NAME_LEN = 63

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            cv.deprecated(CONF_DEFAULT_INTERFACE),
            vol.Schema(
                {
                    vol.Optional(CONF_DEFAULT_INTERFACE): cv.boolean,
                    vol.Optional(CONF_IPV6, default=DEFAULT_IPV6): cv.boolean,
                }
            ),
        )
    },
    extra=vol.ALLOW_EXTRA,
)


class HaServiceInfo(TypedDict):
    """Prepared info from mDNS entries."""

    host: str
    port: int | None
    hostname: str
    type: str
    name: str
    properties: dict[str, Any]


class ZeroconfFlow(TypedDict):
    """A queued zeroconf discovery flow."""

    domain: str
    context: dict[str, Any]
    data: HaServiceInfo


@bind_opp
async def async_get_instance(opp: OpenPeerPower) -> HaZeroconf:
    """Zeroconf instance to be shared with other integrations that use it."""
    return cast(HaZeroconf, (await _async_get_instance(opp)).zeroconf)


@bind_opp
async def async_get_async_instance(opp: OpenPeerPower) -> HaAsyncZeroconf:
    """Zeroconf instance to be shared with other integrations that use it."""
    return await _async_get_instance(opp)


async def _async_get_instance(opp: OpenPeerPower, **zcargs: Any) -> HaAsyncZeroconf:
    if DOMAIN in opp.data:
        return cast(HaAsyncZeroconf, opp.data[DOMAIN])

    logging.getLogger("zeroconf").setLevel(logging.NOTSET)

    aio_zc = HaAsyncZeroconf(**zcargs)
    zeroconf = cast(HaZeroconf, aio_zc.zeroconf)

    install_multiple_zeroconf_catcher(zeroconf)

    def _stop_zeroconf(_event: Event) -> None:
        """Stop Zeroconf."""
        zeroconf.ha_close()

    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, _stop_zeroconf)
    opp.data[DOMAIN] = aio_zc

    return aio_zc


def _async_use_default_interface(adapters: list[Adapter]) -> bool:
    for adapter in adapters:
        if adapter["enabled"] and not adapter["default"]:
            return False
    return True


async def async_setup(opp: OpenPeerPower, config: dict) -> bool:
    """Set up Zeroconf and make Open Peer Power discoverable."""
    zc_config = config.get(DOMAIN, {})
    zc_args: dict = {}

    adapters = await network.async_get_adapters(opp)
    if _async_use_default_interface(adapters):
        zc_args["interfaces"] = InterfaceChoice.Default
    else:
        interfaces = zc_args["interfaces"] = []
        for adapter in adapters:
            if not adapter["enabled"]:
                continue
            if ipv4s := adapter["ipv4"]:
                interfaces.append(ipv4s[0]["address"])
            elif ipv6s := adapter["ipv6"]:
                interfaces.append(ipv6s[0]["scope_id"])
    if not zc_config.get(CONF_IPV6, DEFAULT_IPV6):
        zc_args["ip_version"] = IPVersion.V4Only

    aio_zc = await _async_get_instance(opp, **zc_args)
    zeroconf = aio_zc.zeroconf

    zeroconf_types, homekit_models = await asyncio.gather(
        async_get_zeroconf(opp), async_get_homekit(opp)
    )
    discovery = ZeroconfDiscovery(opp, zeroconf, zeroconf_types, homekit_models)
    await discovery.async_setup()

    async def _async_zeroconf_opp_start(_event: Event) -> None:
        """Expose Open Peer Power on zeroconf when it starts.

        Wait till started or otherwise HTTP is not up and running.
        """
        uuid = await opp.helpers.instance_id.async_get()
        await _async_register_opp_zc_service(opp, aio_zc, uuid)

    @callback
    def _async_start_discovery(_event: Event) -> None:
        """Start processing flows."""
        discovery.async_start()

    async def _async_zeroconf_opp_stop(_event: Event) -> None:
        await discovery.async_stop()

    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, _async_zeroconf_opp_stop)
    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_START, _async_zeroconf_opp_start)
    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STARTED, _async_start_discovery)

    return True


async def _async_register_opp_zc_service(
    opp: OpenPeerPower, aio_zc: HaAsyncZeroconf, uuid: str
) -> None:
    # Get instance UUID
    valid_location_name = _truncate_location_name_to_valid(opp.config.location_name)

    params = {
        "location_name": valid_location_name,
        "uuid": uuid,
        "version": __version__,
        "external_url": "",
        "internal_url": "",
        # Old base URL, for backward compatibility
        "base_url": "",
        # Always needs authentication
        "requires_api_password": True,
    }

    # Get instance URL's
    with suppress(NoURLAvailableError):
        params["external_url"] = get_url(opp, allow_internal=False)

    with suppress(NoURLAvailableError):
        params["internal_url"] = get_url(opp, allow_external=False)

    # Set old base URL based on external or internal
    params["base_url"] = params["external_url"] or params["internal_url"]

    host_ip = util.get_local_ip()

    try:
        host_ip_pton = socket.inet_pton(socket.AF_INET, host_ip)
    except OSError:
        host_ip_pton = socket.inet_pton(socket.AF_INET6, host_ip)

    _suppress_invalid_properties(params)

    info = ServiceInfo(
        ZEROCONF_TYPE,
        name=f"{valid_location_name}.{ZEROCONF_TYPE}",
        server=f"{uuid}.local.",
        addresses=[host_ip_pton],
        port=opp.http.server_port,
        properties=params,
    )

    _LOGGER.info("Starting Zeroconf broadcast")
    try:
        await aio_zc.async_register_service(info)
    except NonUniqueNameException:
        _LOGGER.error(
            "Open Peer Power instance with identical name present in the local network"
        )


class FlowDispatcher:
    """Dispatch discovery flows."""

    def __init__(self, opp: OpenPeerPower) -> None:
        """Init the discovery dispatcher."""
        self.opp = opp
        self.pending_flows: list[ZeroconfFlow] = []
        self.started = False

    @callback
    def async_start(self) -> None:
        """Start processing pending flows."""
        self.started = True
        self.opp.loop.call_soon(self._async_process_pending_flows)

    def _async_process_pending_flows(self) -> None:
        for flow in self.pending_flows:
            self.opp.async_create_task(self._init_flow(flow))
        self.pending_flows = []

    def create(self, flow: ZeroconfFlow) -> None:
        """Create and add or queue a flow."""
        if self.started:
            self.opp.create_task(self._init_flow(flow))
        else:
            self.pending_flows.append(flow)

    def _init_flow(self, flow: ZeroconfFlow) -> Coroutine[None, None, FlowResult]:
        """Create a flow."""
        return self.opp.config_entries.flow.async_init(
            flow["domain"], context=flow["context"], data=flow["data"]
        )


class ZeroconfDiscovery:
    """Discovery via zeroconf."""

    def __init__(
        self,
        opp: OpenPeerPower,
        zeroconf: Zeroconf,
        zeroconf_types: dict[str, list[dict[str, str]]],
        homekit_models: dict[str, str],
    ) -> None:
        """Init discovery."""
        self.opp = opp
        self.zeroconf = zeroconf
        self.zeroconf_types = zeroconf_types
        self.homekit_models = homekit_models

        self.flow_dispatcher: FlowDispatcher | None = None
        self.service_browser: HaServiceBrowser | None = None

    async def async_setup(self) -> None:
        """Start discovery."""
        self.flow_dispatcher = FlowDispatcher(self.opp)
        types = list(self.zeroconf_types)
        # We want to make sure we know about other OpenPeerPower
        # instances as soon as possible to avoid name conflicts
        # so we always browse for ZEROCONF_TYPE
        for hk_type in (ZEROCONF_TYPE, *HOMEKIT_TYPES):
            if hk_type not in self.zeroconf_types:
                types.append(hk_type)
        _LOGGER.debug("Starting Zeroconf browser")
        self.service_browser = HaServiceBrowser(
            self.zeroconf, types, handlers=[self.service_update]
        )

    async def async_stop(self) -> None:
        """Cancel the service browser and stop processing the queue."""
        if self.service_browser:
            await self.opp.async_add_executor_job(self.service_browser.cancel)

    @callback
    def async_start(self) -> None:
        """Start processing discovery flows."""
        assert self.flow_dispatcher is not None
        self.flow_dispatcher.async_start()

    def service_update(
        self,
        zeroconf: Zeroconf,
        service_type: str,
        name: str,
        state_change: ServiceStateChange,
    ) -> None:
        """Service state changed."""
        if state_change == ServiceStateChange.Removed:
            return

        service_info = ServiceInfo(service_type, name)
        service_info.load_from_cache(zeroconf)

        info = info_from_service(service_info)
        if not info:
            # Prevent the browser thread from collapsing
            _LOGGER.debug("Failed to get addresses for device %s", name)
            return

        _LOGGER.debug("Discovered new device %s %s", name, info)
        assert self.flow_dispatcher is not None

        # If we can handle it as a HomeKit discovery, we do that here.
        if service_type in HOMEKIT_TYPES:
            if pending_flow := handle_homekit(self.opp, self.homekit_models, info):
                self.flow_dispatcher.create(pending_flow)
            # Continue on here as homekit_controller
            # still needs to get updates on devices
            # so it can see when the 'c#' field is updated.
            #
            # We only send updates to homekit_controller
            # if the device is already paired in order to avoid
            # offering a second discovery for the same device
            if pending_flow and HOMEKIT_PAIRED_STATUS_FLAG in info["properties"]:
                try:
                    # 0 means paired and not discoverable by iOS clients)
                    if int(info["properties"][HOMEKIT_PAIRED_STATUS_FLAG]):
                        return
                except ValueError:
                    # HomeKit pairing status unknown
                    # likely bad homekit data
                    return

        if "name" in info:
            lowercase_name: str | None = info["name"].lower()
        else:
            lowercase_name = None

        if "macaddress" in info["properties"]:
            uppercase_mac: str | None = info["properties"]["macaddress"].upper()
        else:
            uppercase_mac = None

        if "manufacturer" in info["properties"]:
            lowercase_manufacturer: str | None = info["properties"][
                "manufacturer"
            ].lower()
        else:
            lowercase_manufacturer = None

        # Not all homekit types are currently used for discovery
        # so not all service type exist in zeroconf_types
        for matcher in self.zeroconf_types.get(service_type, []):
            if len(matcher) > 1:
                if "macaddress" in matcher and (
                    uppercase_mac is None
                    or not fnmatch.fnmatch(uppercase_mac, matcher["macaddress"])
                ):
                    continue
                if "name" in matcher and (
                    lowercase_name is None
                    or not fnmatch.fnmatch(lowercase_name, matcher["name"])
                ):
                    continue
                if "manufacturer" in matcher and (
                    lowercase_manufacturer is None
                    or not fnmatch.fnmatch(
                        lowercase_manufacturer, matcher["manufacturer"]
                    )
                ):
                    continue

            flow: ZeroconfFlow = {
                "domain": matcher["domain"],
                "context": {"source": config_entries.SOURCE_ZEROCONF},
                "data": info,
            }
            self.flow_dispatcher.create(flow)


def handle_homekit(
    opp: OpenPeerPower, homekit_models: dict[str, str], info: HaServiceInfo
) -> ZeroconfFlow | None:
    """Handle a HomeKit discovery.

    Return if discovery was forwarded.
    """
    model = None
    props = info["properties"]

    for key in props:
        if key.lower() == HOMEKIT_MODEL:
            model = props[key]
            break

    if model is None:
        return None

    for test_model in homekit_models:
        if (
            model != test_model
            and not model.startswith((f"{test_model} ", f"{test_model}-"))
            and not fnmatch.fnmatch(model, test_model)
        ):
            continue

        return {
            "domain": homekit_models[test_model],
            "context": {"source": config_entries.SOURCE_HOMEKIT},
            "data": info,
        }

    return None


def info_from_service(service: ServiceInfo) -> HaServiceInfo | None:
    """Return prepared info from mDNS entries."""
    properties: dict[str, Any] = {"_raw": {}}

    for key, value in service.properties.items():
        # See https://ietf.org/rfc/rfc6763.html#section-6.4 and
        # https://ietf.org/rfc/rfc6763.html#section-6.5 for expected encodings
        # for property keys and values
        try:
            key = key.decode("ascii")
        except UnicodeDecodeError:
            _LOGGER.debug(
                "Ignoring invalid key provided by [%s]: %s", service.name, key
            )
            continue

        properties["_raw"][key] = value

        with suppress(UnicodeDecodeError):
            if isinstance(value, bytes):
                properties[key] = value.decode("utf-8")

    if not service.addresses:
        return None

    address = service.addresses[0]

    return {
        "host": str(ipaddress.ip_address(address)),
        "port": service.port,
        "hostname": service.server,
        "type": service.type,
        "name": service.name,
        "properties": properties,
    }


def _suppress_invalid_properties(properties: dict) -> None:
    """Suppress any properties that will cause zeroconf to fail to startup."""

    for prop, prop_value in properties.items():
        if not isinstance(prop_value, str):
            continue

        if len(prop_value.encode("utf-8")) > MAX_PROPERTY_VALUE_LEN:
            _LOGGER.error(
                "The property '%s' was suppressed because it is longer than the maximum length of %d bytes: %s",
                prop,
                MAX_PROPERTY_VALUE_LEN,
                prop_value,
            )
            properties[prop] = ""


def _truncate_location_name_to_valid(location_name: str) -> str:
    """Truncate or return the location name usable for zeroconf."""
    if len(location_name.encode("utf-8")) < MAX_NAME_LEN:
        return location_name

    _LOGGER.warning(
        "The location name was truncated because it is longer than the maximum length of %d bytes: %s",
        MAX_NAME_LEN,
        location_name,
    )
    return location_name.encode("utf-8")[:MAX_NAME_LEN].decode("utf-8", "ignore")
