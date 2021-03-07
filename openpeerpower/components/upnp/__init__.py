"""Open ports in your router for Open Peer Power and provide statistics."""
import asyncio
from ipaddress import ip_address

import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import config_validation as cv, device_registry as dr
from openpeerpower.helpers.typing import ConfigType, OpenPeerPowerType
from openpeerpower.util import get_local_ip

from .const import (
    CONF_LOCAL_IP,
    CONFIG_ENTRY_HOSTNAME,
    CONFIG_ENTRY_ST,
    CONFIG_ENTRY_UDN,
    DISCOVERY_LOCATION,
    DISCOVERY_ST,
    DISCOVERY_UDN,
    DOMAIN,
    DOMAIN_CONFIG,
    DOMAIN_COORDINATORS,
    DOMAIN_DEVICES,
    DOMAIN_LOCAL_IP,
    LOGGER as _LOGGER,
)
from .device import Device

NOTIFICATION_ID = "upnp_notification"
NOTIFICATION_TITLE = "UPnP/IGD Setup"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_LOCAL_IP): vol.All(ip_address, cv.string),
            },
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_construct_device(opp: OpenPeerPowerType, udn: str, st: str) -> Device:
    """Discovery devices and construct a Device for one."""
    # pylint: disable=invalid-name
    _LOGGER.debug("Constructing device: %s::%s", udn, st)

    discoveries = [
        discovery
        for discovery in await Device.async_discover(opp)
        if discovery[DISCOVERY_UDN] == udn and discovery[DISCOVERY_ST] == st
    ]
    if not discoveries:
        _LOGGER.info("Device not discovered")
        return None

    # Some additional clues for remote debugging.
    if len(discoveries) > 1:
        _LOGGER.info("Multiple devices discovered: %s", discoveries)

    discovery = discoveries[0]
    _LOGGER.debug("Constructing from discovery: %s", discovery)
    location = discovery[DISCOVERY_LOCATION]
    return await Device.async_create_device(opp, location)


async def async_setup(opp: OpenPeerPowerType, config: ConfigType):
    """Set up UPnP component."""
    _LOGGER.debug("async_setup, config: %s", config)
    conf_default = CONFIG_SCHEMA({DOMAIN: {}})[DOMAIN]
    conf = config.get(DOMAIN, conf_default)
    local_ip = await opp.async_add_executor_job(get_local_ip)
    opp.data[DOMAIN] = {
        DOMAIN_CONFIG: conf,
        DOMAIN_COORDINATORS: {},
        DOMAIN_DEVICES: {},
        DOMAIN_LOCAL_IP: conf.get(CONF_LOCAL_IP, local_ip),
    }

    # Only start if set up via configuration.yaml.
    if DOMAIN in config:
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_IMPORT}
            )
        )

    return True


async def async_setup_entry(opp: OpenPeerPowerType, config_entry: ConfigEntry) -> bool:
    """Set up UPnP/IGD device from a config entry."""
    _LOGGER.debug("Setting up config entry: %s", config_entry.unique_id)

    # Discover and construct.
    udn = config_entry.data[CONFIG_ENTRY_UDN]
    st = config_entry.data[CONFIG_ENTRY_ST]  # pylint: disable=invalid-name
    try:
        device = await async_construct_device(opp, udn, st)
    except asyncio.TimeoutError as err:
        raise ConfigEntryNotReady from err

    if not device:
        _LOGGER.info("Unable to create UPnP/IGD, aborting")
        raise ConfigEntryNotReady

    # Save device.
    opp.data[DOMAIN][DOMAIN_DEVICES][device.udn] = device

    # Ensure entry has a unique_id.
    if not config_entry.unique_id:
        _LOGGER.debug(
            "Setting unique_id: %s, for config_entry: %s",
            device.unique_id,
            config_entry,
        )
        opp.config_entries.async_update_entry(
            entry=config_entry,
            unique_id=device.unique_id,
        )

    # Ensure entry has a hostname, for older entries.
    if (
        CONFIG_ENTRY_HOSTNAME not in config_entry.data
        or config_entry.data[CONFIG_ENTRY_HOSTNAME] != device.hostname
    ):
        opp.config_entries.async_update_entry(
            entry=config_entry,
            data={CONFIG_ENTRY_HOSTNAME: device.hostname, **config_entry.data},
        )

    # Create device registry entry.
    device_registry = await dr.async_get_registry(opp)
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_UPNP, device.udn)},
        identifiers={(DOMAIN, device.udn)},
        name=device.name,
        manufacturer=device.manufacturer,
        model=device.model_name,
    )

    # Create sensors.
    _LOGGER.debug("Enabling sensors")
    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(config_entry, "sensor")
    )

    return True


async def async_unload_entry(opp: OpenPeerPowerType, config_entry: ConfigEntry) -> bool:
    """Unload a UPnP/IGD device from a config entry."""
    _LOGGER.debug("Unloading config entry: %s", config_entry.unique_id)

    udn = config_entry.data.get(CONFIG_ENTRY_UDN)
    if udn in opp.data[DOMAIN][DOMAIN_DEVICES]:
        del opp.data[DOMAIN][DOMAIN_DEVICES][udn]
    if udn in opp.data[DOMAIN][DOMAIN_COORDINATORS]:
        del opp.data[DOMAIN][DOMAIN_COORDINATORS][udn]

    _LOGGER.debug("Deleting sensors")
    return await opp.config_entries.async_forward_entry_unload(config_entry, "sensor")
