"""Support for Zigbee Home Automation devices."""

import asyncio
import logging

import voluptuous as vol
from zhaquirks import setup as setup_quirks
from zigpy.config import CONF_DEVICE, CONF_DEVICE_PATH

from openpeerpower import config_entries, const as ha_const
from openpeerpower.core import OpenPeerPower
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.device_registry import CONNECTION_ZIGBEE
from openpeerpower.helpers.dispatcher import async_dispatcher_send

from . import api
from .core import ZHAGateway
from .core.const import (
    BAUD_RATES,
    CONF_BAUDRATE,
    CONF_CUSTOM_QUIRKS_PATH,
    CONF_DATABASE,
    CONF_DEVICE_CONFIG,
    CONF_ENABLE_QUIRKS,
    CONF_RADIO_TYPE,
    CONF_USB_PATH,
    CONF_ZIGPY,
    DATA_ZHA,
    DATA_ZHA_CONFIG,
    DATA_ZHA_DISPATCHERS,
    DATA_ZHA_GATEWAY,
    DATA_ZHA_PLATFORM_LOADED,
    DATA_ZHA_SHUTDOWN_TASK,
    DOMAIN,
    PLATFORMS,
    SIGNAL_ADD_ENTITIES,
    RadioType,
)
from .core.discovery import GROUP_PROBE

DEVICE_CONFIG_SCHEMA_ENTRY = vol.Schema({vol.Optional(ha_const.CONF_TYPE): cv.string})
ZHA_CONFIG_SCHEMA = {
    vol.Optional(CONF_BAUDRATE): cv.positive_int,
    vol.Optional(CONF_DATABASE): cv.string,
    vol.Optional(CONF_DEVICE_CONFIG, default={}): vol.Schema(
        {cv.string: DEVICE_CONFIG_SCHEMA_ENTRY}
    ),
    vol.Optional(CONF_ENABLE_QUIRKS, default=True): cv.boolean,
    vol.Optional(CONF_ZIGPY): dict,
    vol.Optional(CONF_RADIO_TYPE): cv.enum(RadioType),
    vol.Optional(CONF_USB_PATH): cv.string,
    vol.Optional(CONF_CUSTOM_QUIRKS_PATH): cv.isdir,
}
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            vol.All(
                cv.deprecated(CONF_USB_PATH),
                cv.deprecated(CONF_BAUDRATE),
                cv.deprecated(CONF_RADIO_TYPE),
                ZHA_CONFIG_SCHEMA,
            ),
        ),
    },
    extra=vol.ALLOW_EXTRA,
)

# Zigbee definitions
CENTICELSIUS = "C-100"

# Internal definitions
_LOGGER = logging.getLogger(__name__)


async def async_setup(opp, config):
    """Set up ZHA from config."""
    opp.data[DATA_ZHA] = {}

    if DOMAIN in config:
        conf = config[DOMAIN]
        opp.data[DATA_ZHA][DATA_ZHA_CONFIG] = conf

    return True


async def async_setup_entry(opp, config_entry):
    """Set up ZHA.

    Will automatically load components to support devices found on the network.
    """

    zha_data = opp.data.setdefault(DATA_ZHA, {})
    config = zha_data.get(DATA_ZHA_CONFIG, {})

    for platform in PLATFORMS:
        zha_data.setdefault(platform, [])

    if config.get(CONF_ENABLE_QUIRKS, True):
        setup_quirks(config)

    zha_gateway = ZHAGateway(opp, config, config_entry)
    await zha_gateway.async_initialize()

    zha_data[DATA_ZHA_DISPATCHERS] = []
    zha_data[DATA_ZHA_PLATFORM_LOADED] = []
    for platform in PLATFORMS:
        coro = opp.config_entries.async_forward_entry_setup(config_entry, platform)
        zha_data[DATA_ZHA_PLATFORM_LOADED].append(opp.async_create_task(coro))

    device_registry = await opp.helpers.device_registry.async_get_registry()
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(CONNECTION_ZIGBEE, str(zha_gateway.application_controller.ieee))},
        identifiers={(DOMAIN, str(zha_gateway.application_controller.ieee))},
        name="Zigbee Coordinator",
        manufacturer="ZHA",
        model=zha_gateway.radio_description,
    )

    api.async_load_api(opp)

    async def async_zha_shutdown(event):
        """Handle shutdown tasks."""
        await zha_data[DATA_ZHA_GATEWAY].shutdown()
        await zha_data[DATA_ZHA_GATEWAY].async_update_device_storage()

    zha_data[DATA_ZHA_SHUTDOWN_TASK] = opp.bus.async_listen_once(
        ha_const.EVENT_OPENPEERPOWER_STOP, async_zha_shutdown
    )
    asyncio.create_task(async_load_entities(opp))
    return True


async def async_unload_entry(opp, config_entry):
    """Unload ZHA config entry."""
    await opp.data[DATA_ZHA][DATA_ZHA_GATEWAY].shutdown()
    await opp.data[DATA_ZHA][DATA_ZHA_GATEWAY].async_update_device_storage()

    GROUP_PROBE.cleanup()
    api.async_unload_api(opp)

    dispatchers = opp.data[DATA_ZHA].get(DATA_ZHA_DISPATCHERS, [])
    for unsub_dispatcher in dispatchers:
        unsub_dispatcher()

    # our components don't have unload methods so no need to look at return values
    await asyncio.gather(
        *[
            opp.config_entries.async_forward_entry_unload(config_entry, platform)
            for platform in PLATFORMS
        ]
    )

    opp.data[DATA_ZHA][DATA_ZHA_SHUTDOWN_TASK]()

    return True


async def async_load_entities(opp: OpenPeerPower) -> None:
    """Load entities after integration was setup."""
    await opp.data[DATA_ZHA][DATA_ZHA_GATEWAY].async_initialize_devices_and_entities()
    to_setup = opp.data[DATA_ZHA][DATA_ZHA_PLATFORM_LOADED]
    results = await asyncio.gather(*to_setup, return_exceptions=True)
    for res in results:
        if isinstance(res, Exception):
            _LOGGER.warning("Couldn't setup zha platform: %s", res)
    async_dispatcher_send(opp, SIGNAL_ADD_ENTITIES)


async def async_migrate_entry(
    opp: OpenPeerPower, config_entry: config_entries.ConfigEntry
):
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        data = {
            CONF_RADIO_TYPE: config_entry.data[CONF_RADIO_TYPE],
            CONF_DEVICE: {CONF_DEVICE_PATH: config_entry.data[CONF_USB_PATH]},
        }

        baudrate = opp.data[DATA_ZHA].get(DATA_ZHA_CONFIG, {}).get(CONF_BAUDRATE)
        if data[CONF_RADIO_TYPE] != RadioType.deconz and baudrate in BAUD_RATES:
            data[CONF_DEVICE][CONF_BAUDRATE] = baudrate

        config_entry.version = 2
        opp.config_entries.async_update_entry(config_entry, data=data)

    _LOGGER.info("Migration to version %s successful", config_entry.version)
    return True
