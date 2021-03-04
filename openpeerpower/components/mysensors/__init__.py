"""Connect to a MySensors gateway via pymysensors API."""
import asyncio
import logging
from typing import Callable, Dict, List, Optional, Tuple, Type, Union

from mysensors import BaseAsyncGateway
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.components.mqtt import valid_publish_topic, valid_subscribe_topic
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_OPTIMISTIC
from openpeerpower.core import callback
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.typing import ConfigType, OpenPeerPowerType

from .const import (
    ATTR_DEVICES,
    CONF_BAUD_RATE,
    CONF_DEVICE,
    CONF_GATEWAYS,
    CONF_NODES,
    CONF_PERSISTENCE,
    CONF_PERSISTENCE_FILE,
    CONF_RETAIN,
    CONF_TCP_PORT,
    CONF_TOPIC_IN_PREFIX,
    CONF_TOPIC_OUT_PREFIX,
    CONF_VERSION,
    DOMAIN,
    MYSENSORS_GATEWAYS,
    MYSENSORS_ON_UNLOAD,
    PLATFORMS_WITH_ENTRY_SUPPORT,
    DevId,
    GatewayId,
    SensorType,
)
from .device import MySensorsDevice, MySensorsEntity, get_mysensors_devices
from .gateway import finish_setup, get_mysensors_gateway, gw_stop, setup_gateway

_LOGGER = logging.getLogger(__name__)

CONF_DEBUG = "debug"
CONF_NODE_NAME = "name"

DEFAULT_BAUD_RATE = 115200
DEFAULT_TCP_PORT = 5003
DEFAULT_VERSION = "1.4"


def has_all_unique_files(value):
    """Validate that all persistence files are unique and set if any is set."""
    persistence_files = [gateway.get(CONF_PERSISTENCE_FILE) for gateway in value]
    if None in persistence_files and any(
        name is not None for name in persistence_files
    ):
        raise vol.Invalid(
            "persistence file name of all devices must be set if any is set"
        )
    if not all(name is None for name in persistence_files):
        schema = vol.Schema(vol.Unique())
        schema(persistence_files)
    return value


def is_persistence_file(value):
    """Validate that persistence file path ends in either .pickle or .json."""
    if value.endswith((".json", ".pickle")):
        return value
    raise vol.Invalid(f"{value} does not end in either `.json` or `.pickle`")


def deprecated(key):
    """Mark key as deprecated in configuration."""

    def validator(config):
        """Check if key is in config, log warning and remove key."""
        if key not in config:
            return config
        _LOGGER.warning(
            "%s option for %s is deprecated. Please remove %s from your "
            "configuration file",
            key,
            DOMAIN,
            key,
        )
        config.pop(key)
        return config

    return validator


NODE_SCHEMA = vol.Schema({cv.positive_int: {vol.Required(CONF_NODE_NAME): cv.string}})

GATEWAY_SCHEMA = vol.Schema(
    vol.All(
        deprecated(CONF_NODES),
        {
            vol.Required(CONF_DEVICE): cv.string,
            vol.Optional(CONF_PERSISTENCE_FILE): vol.All(
                cv.string, is_persistence_file
            ),
            vol.Optional(CONF_BAUD_RATE, default=DEFAULT_BAUD_RATE): cv.positive_int,
            vol.Optional(CONF_TCP_PORT, default=DEFAULT_TCP_PORT): cv.port,
            vol.Optional(CONF_TOPIC_IN_PREFIX): valid_subscribe_topic,
            vol.Optional(CONF_TOPIC_OUT_PREFIX): valid_publish_topic,
            vol.Optional(CONF_NODES, default={}): NODE_SCHEMA,
        },
    )
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            vol.All(
                deprecated(CONF_DEBUG),
                deprecated(CONF_OPTIMISTIC),
                deprecated(CONF_PERSISTENCE),
                {
                    vol.Required(CONF_GATEWAYS): vol.All(
                        cv.ensure_list, has_all_unique_files, [GATEWAY_SCHEMA]
                    ),
                    vol.Optional(CONF_RETAIN, default=True): cv.boolean,
                    vol.Optional(CONF_VERSION, default=DEFAULT_VERSION): cv.string,
                    vol.Optional(CONF_OPTIMISTIC, default=False): cv.boolean,
                    vol.Optional(CONF_PERSISTENCE, default=True): cv.boolean,
                },
            )
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp: OpenPeerPowerType, config: ConfigType) -> bool:
    """Set up the MySensors component."""
    if DOMAIN not in config or bool(opp.config_entries.async_entries(DOMAIN)):
        return True

    config = config[DOMAIN]
    user_inputs = [
        {
            CONF_DEVICE: gw[CONF_DEVICE],
            CONF_BAUD_RATE: gw[CONF_BAUD_RATE],
            CONF_TCP_PORT: gw[CONF_TCP_PORT],
            CONF_TOPIC_OUT_PREFIX: gw.get(CONF_TOPIC_OUT_PREFIX, ""),
            CONF_TOPIC_IN_PREFIX: gw.get(CONF_TOPIC_IN_PREFIX, ""),
            CONF_RETAIN: config[CONF_RETAIN],
            CONF_VERSION: config[CONF_VERSION],
            CONF_PERSISTENCE_FILE: gw.get(CONF_PERSISTENCE_FILE)
            # nodes config ignored at this time. renaming nodes can now be done from the frontend.
        }
        for gw in config[CONF_GATEWAYS]
    ]
    user_inputs = [
        {k: v for k, v in userinput.items() if v is not None}
        for userinput in user_inputs
    ]

    # there is an actual configuration in configuration.yaml, so we have to process it
    for user_input in user_inputs:
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_IMPORT},
                data=user_input,
            )
        )

    return True


async def async_setup_entry(opp: OpenPeerPowerType, entry: ConfigEntry) -> bool:
    """Set up an instance of the MySensors integration.

    Every instance has a connection to exactly one Gateway.
    """
    gateway = await setup_gateway(opp, entry)

    if not gateway:
        _LOGGER.error("Gateway setup failed for %s", entry.data)
        return False

    if DOMAIN not in opp.data:
        opp.data[DOMAIN] = {}

    if MYSENSORS_GATEWAYS not in opp.data[DOMAIN]:
        opp.data[DOMAIN][MYSENSORS_GATEWAYS] = {}
    opp.data[DOMAIN][MYSENSORS_GATEWAYS][entry.entry_id] = gateway

    async def finish():
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_setup(entry, platform)
                for platform in PLATFORMS_WITH_ENTRY_SUPPORT
            ]
        )
        await finish_setup(opp, entry, gateway)

    opp.async_create_task(finish())

    return True


async def async_unload_entry(opp: OpenPeerPowerType, entry: ConfigEntry) -> bool:
    """Remove an instance of the MySensors integration."""

    gateway = get_mysensors_gateway(opp, entry.entry_id)

    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS_WITH_ENTRY_SUPPORT
            ]
        )
    )
    if not unload_ok:
        return False

    key = MYSENSORS_ON_UNLOAD.format(entry.entry_id)
    if key in opp.data[DOMAIN]:
        for fnct in opp.data[DOMAIN][key]:
            fnct()

    del opp.data[DOMAIN][MYSENSORS_GATEWAYS][entry.entry_id]

    await gw_stop(opp, entry, gateway)
    return True


async def on_unload(
    opp: OpenPeerPowerType, entry: Union[ConfigEntry, GatewayId], fnct: Callable
) -> None:
    """Register a callback to be called when entry is unloaded.

    This function is used by platforms to cleanup after themselves
    """
    if isinstance(entry, GatewayId):
        uniqueid = entry
    else:
        uniqueid = entry.entry_id
    key = MYSENSORS_ON_UNLOAD.format(uniqueid)
    if key not in opp.data[DOMAIN]:
        opp.data[DOMAIN][key] = []
    opp.data[DOMAIN][key].append(fnct)


@callback
def setup_mysensors_platform(
    opp,
    domain: str,  # opp platform name
    discovery_info: Optional[Dict[str, List[DevId]]],
    device_class: Union[Type[MySensorsDevice], Dict[SensorType, Type[MySensorsEntity]]],
    device_args: Optional[
        Tuple
    ] = None,  # extra arguments that will be given to the entity constructor
    async_add_entities: Callable = None,
) -> Optional[List[MySensorsDevice]]:
    """Set up a MySensors platform.

    Sets up a bunch of instances of a single platform that is supported by this integration.
    The function is given a list of device ids, each one describing an instance to set up.
    The function is also given a class.
    A new instance of the class is created for every device id, and the device id is given to the constructor of the class
    """
    # Only act if called via MySensors by discovery event.
    # Otherwise gateway is not set up.
    if not discovery_info:
        _LOGGER.debug("Skipping setup due to no discovery info")
        return None
    if device_args is None:
        device_args = ()
    new_devices: List[MySensorsDevice] = []
    new_dev_ids: List[DevId] = discovery_info[ATTR_DEVICES]
    for dev_id in new_dev_ids:
        devices: Dict[DevId, MySensorsDevice] = get_mysensors_devices(opp, domain)
        if dev_id in devices:
            _LOGGER.debug(
                "Skipping setup of %s for platform %s as it already exists",
                dev_id,
                domain,
            )
            continue
        gateway_id, node_id, child_id, value_type = dev_id
        gateway: Optional[BaseAsyncGateway] = get_mysensors_gateway(opp, gateway_id)
        if not gateway:
            _LOGGER.warning("Skipping setup of %s, no gateway found", dev_id)
            continue
        device_class_copy = device_class
        if isinstance(device_class, dict):
            child = gateway.sensors[node_id].children[child_id]
            s_type = gateway.const.Presentation(child.type).name
            device_class_copy = device_class[s_type]

        args_copy = (*device_args, gateway_id, gateway, node_id, child_id, value_type)
        devices[dev_id] = device_class_copy(*args_copy)
        new_devices.append(devices[dev_id])
    if new_devices:
        _LOGGER.info("Adding new devices: %s", new_devices)
        if async_add_entities is not None:
            async_add_entities(new_devices, True)
    return new_devices
