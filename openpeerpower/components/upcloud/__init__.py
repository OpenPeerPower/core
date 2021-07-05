"""Support for UpCloud."""
from __future__ import annotations

import dataclasses
from datetime import timedelta
import logging
from typing import Any, Dict

import requests.exceptions
import upcloud_api
import voluptuous as vol

from openpeerpower.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from openpeerpower.components.switch import DOMAIN as SWITCH_DOMAIN
from openpeerpower.config_entries import SOURCE_IMPORT, ConfigEntry
from openpeerpower.const import (
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    STATE_OFF,
    STATE_ON,
    STATE_PROBLEM,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from openpeerpower.helpers.typing import ConfigType
from openpeerpower.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import CONFIG_ENTRY_UPDATE_SIGNAL_TEMPLATE, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

ATTR_CORE_NUMBER = "core_number"
ATTR_HOSTNAME = "hostname"
ATTR_MEMORY_AMOUNT = "memory_amount"
ATTR_TITLE = "title"
ATTR_UUID = "uuid"
ATTR_ZONE = "zone"

CONF_SERVERS = "servers"

DATA_UPCLOUD = "data_upcloud"

DEFAULT_COMPONENT_NAME = "UpCloud {}"
DEFAULT_COMPONENT_DEVICE_CLASS = "power"

CONFIG_ENTRY_DOMAINS = {BINARY_SENSOR_DOMAIN, SWITCH_DOMAIN}

SIGNAL_UPDATE_UPCLOUD = "upcloud_update"

STATE_MAP = {"error": STATE_PROBLEM, "started": STATE_ON, "stopped": STATE_OFF}

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): cv.time_period,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


class UpCloudDataUpdateCoordinator(
    DataUpdateCoordinator[Dict[str, upcloud_api.Server]]
):
    """UpCloud data update coordinator."""

    def __init__(
        self,
        opp: OpenPeerPower,
        *,
        cloud_manager: upcloud_api.CloudManager,
        update_interval: timedelta,
        username: str,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            opp, _LOGGER, name=f"{username}@UpCloud", update_interval=update_interval
        )
        self.cloud_manager = cloud_manager

    async def async_update_config(self, config_entry: ConfigEntry) -> None:
        """Handle config update."""
        self.update_interval = timedelta(
            seconds=config_entry.options[CONF_SCAN_INTERVAL]
        )

    async def _async_update_data(self) -> dict[str, upcloud_api.Server]:
        return {
            x.uuid: x
            for x in await self.opp.async_add_executor_job(
                self.cloud_manager.get_servers
            )
        }


@dataclasses.dataclass
class UpCloudHassData:
    """Open Peer Power UpCloud runtime data."""

    coordinators: dict[str, UpCloudDataUpdateCoordinator] = dataclasses.field(
        default_factory=dict
    )
    scan_interval_migrations: dict[str, int] = dataclasses.field(default_factory=dict)


async def async_setup(opp: OpenPeerPower, config: ConfigType) -> bool:
    """Set up UpCloud component."""
    domain_config = config.get(DOMAIN)
    if not domain_config:
        return True

    _LOGGER.warning(
        "Loading upcloud via top level config is deprecated and no longer "
        "necessary as of 0.117; Please remove it from your YAML configuration"
    )
    opp.async_create_task(
        opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data={
                CONF_USERNAME: domain_config[CONF_USERNAME],
                CONF_PASSWORD: domain_config[CONF_PASSWORD],
            },
        )
    )

    if domain_config[CONF_SCAN_INTERVAL]:
        opp.data[DATA_UPCLOUD] = UpCloudHassData()
        opp.data[DATA_UPCLOUD].scan_interval_migrations[
            domain_config[CONF_USERNAME]
        ] = domain_config[CONF_SCAN_INTERVAL]

    return True


def _config_entry_update_signal_name(config_entry: ConfigEntry) -> str:
    """Get signal name for updates to a config entry."""
    return CONFIG_ENTRY_UPDATE_SIGNAL_TEMPLATE.format(config_entry.unique_id)


async def _async_signal_options_update(
    opp: OpenPeerPower, config_entry: ConfigEntry
) -> None:
    """Signal config entry options update."""
    async_dispatcher_send(
        opp, _config_entry_update_signal_name(config_entry), config_entry
    )


async def async_setup_entry(opp: OpenPeerPower, config_entry: ConfigEntry) -> bool:
    """Set up the UpCloud config entry."""

    manager = upcloud_api.CloudManager(
        config_entry.data[CONF_USERNAME], config_entry.data[CONF_PASSWORD]
    )

    try:
        await opp.async_add_executor_job(manager.authenticate)
    except upcloud_api.UpCloudAPIError:
        _LOGGER.error("Authentication failed", exc_info=True)
        return False
    except requests.exceptions.RequestException as err:
        _LOGGER.error("Failed to connect", exc_info=True)
        raise ConfigEntryNotReady from err

    upcloud_data = opp.data.setdefault(DATA_UPCLOUD, UpCloudHassData())

    # Handle pre config entry (0.117) scan interval migration to options
    migrated_scan_interval = upcloud_data.scan_interval_migrations.pop(
        config_entry.data[CONF_USERNAME], None
    )
    if migrated_scan_interval and (
        not config_entry.options.get(CONF_SCAN_INTERVAL)
        or config_entry.options[CONF_SCAN_INTERVAL]
        == DEFAULT_SCAN_INTERVAL.total_seconds()
    ):
        update_interval = migrated_scan_interval
        opp.config_entries.async_update_entry(
            config_entry,
            options={CONF_SCAN_INTERVAL: update_interval.total_seconds()},
        )
    elif config_entry.options.get(CONF_SCAN_INTERVAL):
        update_interval = timedelta(seconds=config_entry.options[CONF_SCAN_INTERVAL])
    else:
        update_interval = DEFAULT_SCAN_INTERVAL

    coordinator = UpCloudDataUpdateCoordinator(
        opp,
        update_interval=update_interval,
        cloud_manager=manager,
        username=config_entry.data[CONF_USERNAME],
    )

    # Call the UpCloud API to refresh data
    await coordinator.async_config_entry_first_refresh()

    # Listen to config entry updates
    config_entry.async_on_unload(
        config_entry.add_update_listener(_async_signal_options_update)
    )
    config_entry.async_on_unload(
        async_dispatcher_connect(
            opp,
            _config_entry_update_signal_name(config_entry),
            coordinator.async_update_config,
        )
    )

    upcloud_data.coordinators[config_entry.data[CONF_USERNAME]] = coordinator

    # Forward entry setup
    opp.config_entries.async_setup_platforms(config_entry, CONFIG_ENTRY_DOMAINS)

    return True


async def async_unload_entry(opp: OpenPeerPower, config_entry: ConfigEntry) -> bool:
    """Unload the config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(
        config_entry, CONFIG_ENTRY_DOMAINS
    )

    opp.data[DATA_UPCLOUD].coordinators.pop(config_entry.data[CONF_USERNAME])

    return unload_ok


class UpCloudServerEntity(CoordinatorEntity):
    """Entity class for UpCloud servers."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[dict[str, upcloud_api.Server]],
        uuid: str,
    ) -> None:
        """Initialize the UpCloud server entity."""
        super().__init__(coordinator)
        self.uuid = uuid

    @property
    def _server(self) -> upcloud_api.Server:
        return self.coordinator.data[self.uuid]

    @property
    def unique_id(self) -> str:
        """Return unique ID for the entity."""
        return self.uuid

    @property
    def name(self) -> str:
        """Return the name of the component."""
        try:
            return DEFAULT_COMPONENT_NAME.format(self._server.title)
        except (AttributeError, KeyError, TypeError):
            return DEFAULT_COMPONENT_NAME.format(self.uuid)

    @property
    def icon(self) -> str:
        """Return the icon of this server."""
        return "mdi:server" if self.is_on else "mdi:server-off"

    @property
    def state(self) -> str | None:
        """Return state of the server."""
        try:
            return STATE_MAP.get(self._server.state, self._server.state)
        except AttributeError:
            return None

    @property
    def is_on(self) -> bool:
        """Return true if the server is on."""
        return self.state == STATE_ON

    @property
    def device_class(self) -> str:
        """Return the class of this server."""
        return DEFAULT_COMPONENT_DEVICE_CLASS

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes of the UpCloud server."""
        return {
            x: getattr(self._server, x, None)
            for x in (
                ATTR_UUID,
                ATTR_TITLE,
                ATTR_HOSTNAME,
                ATTR_ZONE,
                ATTR_CORE_NUMBER,
                ATTR_MEMORY_AMOUNT,
            )
        }
