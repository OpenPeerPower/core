"""Support the ISY-994 controllers."""
import asyncio
from functools import partial
from typing import Optional
from urllib.parse import urlparse

from pyisy import ISY
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers import config_validation as cv
import openpeerpower.helpers.device_registry as dr
from openpeerpower.helpers.typing import ConfigType

from .const import (
    _LOGGER,
    CONF_IGNORE_STRING,
    CONF_RESTORE_LIGHT_STATE,
    CONF_SENSOR_STRING,
    CONF_TLS_VER,
    CONF_VAR_SENSOR_STRING,
    DEFAULT_IGNORE_STRING,
    DEFAULT_RESTORE_LIGHT_STATE,
    DEFAULT_SENSOR_STRING,
    DEFAULT_VAR_SENSOR_STRING,
    DOMAIN,
    ISY994_ISY,
    ISY994_NODES,
    ISY994_PROGRAMS,
    ISY994_VARIABLES,
    MANUFACTURER,
    PLATFORMS,
    SUPPORTED_PROGRAM_PLATFORMS,
    UNDO_UPDATE_LISTENER,
)
from .helpers import _categorize_nodes, _categorize_programs, _categorize_variables
from .services import async_setup_services, async_unload_services

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.url,
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_TLS_VER): vol.Coerce(float),
                vol.Optional(
                    CONF_IGNORE_STRING, default=DEFAULT_IGNORE_STRING
                ): cv.string,
                vol.Optional(
                    CONF_SENSOR_STRING, default=DEFAULT_SENSOR_STRING
                ): cv.string,
                vol.Optional(
                    CONF_VAR_SENSOR_STRING, default=DEFAULT_VAR_SENSOR_STRING
                ): cv.string,
                vol.Required(
                    CONF_RESTORE_LIGHT_STATE, default=DEFAULT_RESTORE_LIGHT_STATE
                ): bool,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp: OpenPeerPower, config: ConfigType) -> bool:
    """Set up the isy994 integration from YAML."""
    isy_config: Optional[ConfigType] = config.get(DOMAIN)
    opp.data.setdefault(DOMAIN, {})

    if not isy_config:
        return True

    # Only import if we haven't before.
    config_entry = _async_find_matching_config_entry(opp)
    if not config_entry:
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_IMPORT},
                data=dict(isy_config),
            )
        )
        return True

    # Update the entry based on the YAML configuration, in case it changed.
    opp.config_entries.async_update_entry(config_entry, data=dict(isy_config))
    return True


@callback
def _async_find_matching_config_entry(opp):
    for entry in opp.config_entries.async_entries(DOMAIN):
        if entry.source == config_entries.SOURCE_IMPORT:
            return entry


async def async_setup_entry(
    opp: OpenPeerPower, entry: config_entries.ConfigEntry
) -> bool:
    """Set up the ISY 994 integration."""
    # As there currently is no way to import options from yaml
    # when setting up a config entry, we fallback to adding
    # the options to the config entry and pull them out here if
    # they are missing from the options
    _async_import_options_from_data_if_missing(opp, entry)

    opp.data[DOMAIN][entry.entry_id] = {}
    opp_isy_data = opp.data[DOMAIN][entry.entry_id]

    opp_isy_data[ISY994_NODES] = {}
    for platform in PLATFORMS:
        opp_isy_data[ISY994_NODES][platform] = []

    opp_isy_data[ISY994_PROGRAMS] = {}
    for platform in SUPPORTED_PROGRAM_PLATFORMS:
        opp_isy_data[ISY994_PROGRAMS][platform] = []

    opp_isy_data[ISY994_VARIABLES] = []

    isy_config = entry.data
    isy_options = entry.options

    # Required
    user = isy_config[CONF_USERNAME]
    password = isy_config[CONF_PASSWORD]
    host = urlparse(isy_config[CONF_HOST])

    # Optional
    tls_version = isy_config.get(CONF_TLS_VER)
    ignore_identifier = isy_options.get(CONF_IGNORE_STRING, DEFAULT_IGNORE_STRING)
    sensor_identifier = isy_options.get(CONF_SENSOR_STRING, DEFAULT_SENSOR_STRING)
    variable_identifier = isy_options.get(
        CONF_VAR_SENSOR_STRING, DEFAULT_VAR_SENSOR_STRING
    )

    if host.scheme == "http":
        https = False
        port = host.port or 80
    elif host.scheme == "https":
        https = True
        port = host.port or 443
    else:
        _LOGGER.error("isy994 host value in configuration is invalid")
        return False

    # Connect to ISY controller.
    isy = await opp.async_add_executor_job(
        partial(
            ISY,
            host.hostname,
            port,
            username=user,
            password=password,
            use_https=https,
            tls_ver=tls_version,
            webroot=host.path,
        )
    )
    if not isy.connected:
        return False

    # Trigger a status update for all nodes, not done automatically in PyISY v2.x
    await opp.async_add_executor_job(isy.nodes.update)

    _categorize_nodes(opp_isy_data, isy.nodes, ignore_identifier, sensor_identifier)
    _categorize_programs(opp_isy_data, isy.programs)
    _categorize_variables(opp_isy_data, isy.variables, variable_identifier)

    # Dump ISY Clock Information. Future: Add ISY as sensor to Opp with attrs
    _LOGGER.info(repr(isy.clock))

    opp_isy_data[ISY994_ISY] = isy
    await _async_get_or_create_isy_device_in_registry(opp, entry, isy)

    # Load platforms for the devices in the ISY controller that we support.
    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    def _start_auto_update() -> None:
        """Start isy auto update."""
        _LOGGER.debug("ISY Starting Event Stream and automatic updates")
        isy.auto_update = True

    await opp.async_add_executor_job(_start_auto_update)

    undo_listener = entry.add_update_listener(_async_update_listener)

    opp_isy_data[UNDO_UPDATE_LISTENER] = undo_listener

    # Register Integration-wide Services:
    async_setup_services(opp)

    return True


async def _async_update_listener(opp: OpenPeerPower, entry: config_entries.ConfigEntry):
    """Handle options update."""
    await opp.config_entries.async_reload(entry.entry_id)


@callback
def _async_import_options_from_data_if_missing(
    opp: OpenPeerPower, entry: config_entries.ConfigEntry
):
    options = dict(entry.options)
    modified = False
    for importable_option in [
        CONF_IGNORE_STRING,
        CONF_SENSOR_STRING,
        CONF_RESTORE_LIGHT_STATE,
    ]:
        if importable_option not in entry.options and importable_option in entry.data:
            options[importable_option] = entry.data[importable_option]
            modified = True

    if modified:
        opp.config_entries.async_update_entry(entry, options=options)


async def _async_get_or_create_isy_device_in_registry(
    opp: OpenPeerPower, entry: config_entries.ConfigEntry, isy
) -> None:
    device_registry = await dr.async_get_registry(opp)

    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, isy.configuration["uuid"])},
        identifiers={(DOMAIN, isy.configuration["uuid"])},
        manufacturer=MANUFACTURER,
        name=isy.configuration["name"],
        model=isy.configuration["model"],
        sw_version=isy.configuration["firmware"],
    )


async def async_unload_entry(
    opp: OpenPeerPower, entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    opp_isy_data = opp.data[DOMAIN][entry.entry_id]

    isy = opp_isy_data[ISY994_ISY]

    def _stop_auto_update() -> None:
        """Start isy auto update."""
        _LOGGER.debug("ISY Stopping Event Stream and automatic updates")
        isy.auto_update = False

    await opp.async_add_executor_job(_stop_auto_update)

    opp_isy_data[UNDO_UPDATE_LISTENER]()

    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    async_unload_services(opp)

    return unload_ok
