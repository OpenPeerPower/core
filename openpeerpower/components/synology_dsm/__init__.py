"""The Synology DSM component."""
import asyncio
from datetime import timedelta
import logging
from typing import Dict

import async_timeout
from synology_dsm import SynologyDSM
from synology_dsm.api.core.security import SynoCoreSecurity
from synology_dsm.api.core.system import SynoCoreSystem
from synology_dsm.api.core.upgrade import SynoCoreUpgrade
from synology_dsm.api.core.utilization import SynoCoreUtilization
from synology_dsm.api.dsm.information import SynoDSMInformation
from synology_dsm.api.dsm.network import SynoDSMNetwork
from synology_dsm.api.storage.storage import SynoStorage
from synology_dsm.api.surveillance_station import SynoSurveillanceStation
from synology_dsm.exceptions import (
    SynologyDSMAPIErrorException,
    SynologyDSMLoginFailedException,
    SynologyDSMRequestException,
)
import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT, ConfigEntry
from openpeerpower.const import (
    ATTR_ATTRIBUTION,
    CONF_DISKS,
    CONF_HOST,
    CONF_MAC,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SSL,
    CONF_TIMEOUT,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from openpeerpower.core import ServiceCall, callback
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import entity_registry
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from openpeerpower.helpers.entity import Entity
from openpeerpower.helpers.event import async_track_time_interval
from openpeerpower.helpers.typing import OpenPeerPowerType
from openpeerpower.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    CONF_SERIAL,
    CONF_VOLUMES,
    COORDINATOR_SURVEILLANCE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_USE_SSL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    ENTITY_CLASS,
    ENTITY_ENABLE,
    ENTITY_ICON,
    ENTITY_NAME,
    ENTITY_UNIT,
    PLATFORMS,
    SERVICE_REBOOT,
    SERVICE_SHUTDOWN,
    SERVICES,
    STORAGE_DISK_BINARY_SENSORS,
    STORAGE_DISK_SENSORS,
    STORAGE_VOL_SENSORS,
    SYNO_API,
    TEMP_SENSORS_KEYS,
    UNDO_UPDATE_LISTENER,
    UTILISATION_SENSORS,
)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT): cv.port,
        vol.Optional(CONF_SSL, default=DEFAULT_USE_SSL): cv.boolean,
        vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): cv.boolean,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_DISKS): cv.ensure_list,
        vol.Optional(CONF_VOLUMES): cv.ensure_list,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema(vol.All(cv.ensure_list, [CONFIG_SCHEMA]))},
    extra=vol.ALLOW_EXTRA,
)

ATTRIBUTION = "Data provided by Synology"


_LOGGER = logging.getLogger(__name__)


async def async_setup.opp, config):
    """Set up Synology DSM sensors from legacy config file."""

    conf = config.get(DOMAIN)
    if conf is None:
        return True

    for dsm_conf in conf:
       .opp.async_create_task(
           .opp.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=dsm_conf,
            )
        )

    return True


async def async_setup_entry.opp: OpenPeerPowerType, entry: ConfigEntry):
    """Set up Synology DSM sensors."""

    # Migrate old unique_id
    @callback
    def _async_migrator(entity_entry: entity_registry.RegistryEntry):
        """Migrate away from ID using label."""
        # Reject if new unique_id
        if "SYNO." in entity_entry.unique_id:
            return None

        entries = {
            **STORAGE_DISK_BINARY_SENSORS,
            **STORAGE_DISK_SENSORS,
            **STORAGE_VOL_SENSORS,
            **UTILISATION_SENSORS,
        }
        infos = entity_entry.unique_id.split("_")
        serial = infos.pop(0)
        label = infos.pop(0)
        device_id = "_".join(infos)

        # Removed entity
        if (
            "Type" in entity_entry.unique_id
            or "Device" in entity_entry.unique_id
            or "Name" in entity_entry.unique_id
        ):
            return None

        entity_type = None
        for entity_key, entity_attrs in entries.items():
            if (
                device_id
                and entity_attrs[ENTITY_NAME] == "Status"
                and "Status" in entity_entry.unique_id
                and "(Smart)" not in entity_entry.unique_id
            ):
                if "sd" in device_id and "disk" in entity_key:
                    entity_type = entity_key
                    continue
                if "volume" in device_id and "volume" in entity_key:
                    entity_type = entity_key
                    continue

            if entity_attrs[ENTITY_NAME] == label:
                entity_type = entity_key

        new_unique_id = "_".join([serial, entity_type])
        if device_id:
            new_unique_id += f"_{device_id}"

        _LOGGER.info(
            "Migrating unique_id from [%s] to [%s]",
            entity_entry.unique_id,
            new_unique_id,
        )
        return {"new_unique_id": new_unique_id}

    await entity_registry.async_migrate_entries.opp, entry.entry_id, _async_migrator)

    # Migrate existing entry configuration
    if entry.data.get(CONF_VERIFY_SSL) is None:
       .opp.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_VERIFY_SSL: DEFAULT_VERIFY_SSL}
        )

    # Continue setup
    api = SynoApi.opp, entry)
    try:
        await api.async_setup()
    except (SynologyDSMLoginFailedException, SynologyDSMRequestException) as err:
        _LOGGER.debug("async_setup_entry() - Unable to connect to DSM: %s", err)
        raise ConfigEntryNotReady from err

    undo_listener = entry.add_update_listener(_async_update_listener)

   .opp.data.setdefault(DOMAIN, {})
   .opp.data[DOMAIN][entry.unique_id] = {
        SYNO_API: api,
        UNDO_UPDATE_LISTENER: undo_listener,
    }

    # Services
    await _async_setup_services.opp)

    # For SSDP compat
    if not entry.data.get(CONF_MAC):
        network = await.opp.async_add_executor_job(getattr, api.dsm, "network")
       .opp.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_MAC: network.macs}
        )

    # setup DataUpdateCoordinator
    async def async_coordinator_update_data_surveillance_station():
        """Fetch all surveillance station data from api."""
        surveillance_station = api.surveillance_station
        try:
            async with async_timeout.timeout(10):
                await.opp.async_add_executor_job(surveillance_station.update)
        except SynologyDSMAPIErrorException as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        if SynoSurveillanceStation.CAMERA_API_KEY not in api.dsm.apis:
            return

        return {
            "cameras": {
                camera.id: camera for camera in surveillance_station.get_all_cameras()
            }
        }

   .opp.data[DOMAIN][entry.unique_id][
        COORDINATOR_SURVEILLANCE
    ] = DataUpdateCoordinator(
       .opp,
        _LOGGER,
        name=f"{entry.unique_id}_surveillance_station",
        update_method=async_coordinator_update_data_surveillance_station,
        update_interval=timedelta(seconds=30),
    )

    for platform in PLATFORMS:
       .opp.async_create_task(
           .opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry.opp: OpenPeerPowerType, entry: ConfigEntry):
    """Unload Synology DSM sensors."""
    unload_ok = all(
        await asyncio.gather(
            *[
               .opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    if unload_ok:
        entry_data =.opp.data[DOMAIN][entry.unique_id]
        entry_data[UNDO_UPDATE_LISTENER]()
        await entry_data[SYNO_API].async_unload()
       .opp.data[DOMAIN].pop(entry.unique_id)

    return unload_ok


async def _async_update_listener.opp: OpenPeerPowerType, entry: ConfigEntry):
    """Handle options update."""
    await.opp.config_entries.async_reload(entry.entry_id)


async def _async_setup_services.opp: OpenPeerPowerType):
    """Service handler setup."""

    async def service_op.dler(call: ServiceCall):
        """Handle service call."""
        serial = call.data.get(CONF_SERIAL)
        dsm_devices =.opp.data[DOMAIN]

        if serial:
            dsm_device = dsm_devices.get(serial)
        elif len(dsm_devices) == 1:
            dsm_device = next(iter(dsm_devices.values()))
            serial = next(iter(dsm_devices))
        else:
            _LOGGER.error(
                "service_op.dler - more than one DSM configured, must specify one of serials %s",
                sorted(dsm_devices),
            )
            return

        if not dsm_device:
            _LOGGER.error(
                "service_op.dler - DSM with specified serial %s not found", serial
            )
            return

        _LOGGER.debug("%s DSM with serial %s", call.service, serial)
        dsm_api = dsm_device[SYNO_API]
        if call.service == SERVICE_REBOOT:
            await dsm_api.async_reboot()
        elif call.service == SERVICE_SHUTDOWN:
            await dsm_api.system.shutdown()

    for service in SERVICES:
       .opp.services.async_register(DOMAIN, service, service_op.dler)


class SynoApi:
    """Class to interface with Synology DSM API."""

    def __init__(self,.opp: OpenPeerPowerType, entry: ConfigEntry):
        """Initialize the API wrapper class."""
        self._opp =.opp
        self._entry = entry

        # DSM APIs
        self.dsm: SynologyDSM = None
        self.information: SynoDSMInformation = None
        self.network: SynoDSMNetwork = None
        self.security: SynoCoreSecurity = None
        self.storage: SynoStorage = None
        self.surveillance_station: SynoSurveillanceStation = None
        self.system: SynoCoreSystem = None
        self.upgrade: SynoCoreUpgrade = None
        self.utilisation: SynoCoreUtilization = None

        # Should we fetch them
        self._fetching_entities = {}
        self._with_information = True
        self._with_security = True
        self._with_storage = True
        self._with_surveillance_station = True
        self._with_system = True
        self._with_upgrade = True
        self._with_utilisation = True

        self._unsub_dispatcher = None

    @property
    def signal_sensor_update(self) -> str:
        """Event specific per Synology DSM entry to signal updates in sensors."""
        return f"{DOMAIN}-{self.information.serial}-sensor-update"

    async def async_setup(self):
        """Start interacting with the NAS."""
        # init SynologyDSM object and login
        self.dsm = SynologyDSM(
            self._entry.data[CONF_HOST],
            self._entry.data[CONF_PORT],
            self._entry.data[CONF_USERNAME],
            self._entry.data[CONF_PASSWORD],
            self._entry.data[CONF_SSL],
            self._entry.data[CONF_VERIFY_SSL],
            timeout=self._entry.options.get(CONF_TIMEOUT),
            device_token=self._entry.data.get("device_token"),
        )
        await self._opp.async_add_executor_job(self.dsm.login)

        # check if surveillance station is used
        self._with_surveillance_station = bool(
            self.dsm.apis.get(SynoSurveillanceStation.CAMERA_API_KEY)
        )
        _LOGGER.debug(
            "SynoAPI.async_setup() - self._with_surveillance_station:%s",
            self._with_surveillance_station,
        )

        self._async_setup_api_requests()

        await self._opp.async_add_executor_job(self._fetch_device_configuration)
        await self.async_update()

        self._unsub_dispatcher = async_track_time_interval(
            self._opp,
            self.async_update,
            timedelta(
                minutes=self._entry.options.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                )
            ),
        )

    @callback
    def subscribe(self, api_key, unique_id):
        """Subscribe an entity from API fetches."""
        _LOGGER.debug(
            "SynoAPI.subscribe() - api_key:%s, unique_id:%s", api_key, unique_id
        )
        if api_key not in self._fetching_entities:
            self._fetching_entities[api_key] = set()
        self._fetching_entities[api_key].add(unique_id)

        @callback
        def unsubscribe() -> None:
            """Unsubscribe an entity from API fetches (when disable)."""
            self._fetching_entities[api_key].remove(unique_id)

        return unsubscribe

    @callback
    def _async_setup_api_requests(self):
        """Determine if we should fetch each API, if one entity needs it."""
        _LOGGER.debug(
            "SynoAPI._async_setup_api_requests() - self._fetching_entities:%s",
            self._fetching_entities,
        )

        # Entities not added yet, fetch all
        if not self._fetching_entities:
            _LOGGER.debug(
                "SynoAPI._async_setup_api_requests() - Entities not added yet, fetch all"
            )
            return

        # Determine if we should fetch an API
        self._with_security = bool(
            self._fetching_entities.get(SynoCoreSecurity.API_KEY)
        )
        self._with_storage = bool(self._fetching_entities.get(SynoStorage.API_KEY))
        self._with_system = bool(self._fetching_entities.get(SynoCoreSystem.API_KEY))
        self._with_upgrade = bool(self._fetching_entities.get(SynoCoreUpgrade.API_KEY))
        self._with_utilisation = bool(
            self._fetching_entities.get(SynoCoreUtilization.API_KEY)
        )
        self._with_information = bool(
            self._fetching_entities.get(SynoDSMInformation.API_KEY)
        )
        self._with_surveillance_station = bool(
            self.dsm.apis.get(SynoSurveillanceStation.CAMERA_API_KEY)
        )

        # Reset not used API, information is not reset since it's used in device_info
        if not self._with_security:
            _LOGGER.debug("SynoAPI._async_setup_api_requests() - disable security")
            self.dsm.reset(self.security)
            self.security = None

        if not self._with_storage:
            _LOGGER.debug("SynoAPI._async_setup_api_requests() - disable storage")
            self.dsm.reset(self.storage)
            self.storage = None

        if not self._with_system:
            _LOGGER.debug("SynoAPI._async_setup_api_requests() - disable system")
            self.dsm.reset(self.system)
            self.system = None

        if not self._with_upgrade:
            _LOGGER.debug("SynoAPI._async_setup_api_requests() - disable upgrade")
            self.dsm.reset(self.upgrade)
            self.upgrade = None

        if not self._with_utilisation:
            _LOGGER.debug("SynoAPI._async_setup_api_requests() - disable utilisation")
            self.dsm.reset(self.utilisation)
            self.utilisation = None

        if not self._with_surveillance_station:
            _LOGGER.debug(
                "SynoAPI._async_setup_api_requests() - disable surveillance_station"
            )
            self.dsm.reset(self.surveillance_station)
            self.surveillance_station = None

    def _fetch_device_configuration(self):
        """Fetch initial device config."""
        self.information = self.dsm.information
        self.network = self.dsm.network
        self.network.update()

        if self._with_security:
            _LOGGER.debug("SynoAPI._fetch_device_configuration() - fetch security")
            self.security = self.dsm.security

        if self._with_storage:
            _LOGGER.debug("SynoAPI._fetch_device_configuration() - fetch storage")
            self.storage = self.dsm.storage

        if self._with_upgrade:
            _LOGGER.debug("SynoAPI._fetch_device_configuration() - fetch upgrade")
            self.upgrade = self.dsm.upgrade

        if self._with_system:
            _LOGGER.debug("SynoAPI._fetch_device_configuration() - fetch system")
            self.system = self.dsm.system

        if self._with_utilisation:
            _LOGGER.debug("SynoAPI._fetch_device_configuration() - fetch utilisation")
            self.utilisation = self.dsm.utilisation

        if self._with_surveillance_station:
            _LOGGER.debug(
                "SynoAPI._fetch_device_configuration() - fetch surveillance_station"
            )
            self.surveillance_station = self.dsm.surveillance_station

    async def async_reboot(self):
        """Reboot NAS."""
        if not self.system:
            _LOGGER.debug("SynoAPI.async_reboot() - System API not ready: %s", self)
            return
        await self._opp.async_add_executor_job(self.system.reboot)

    async def async_shutdown(self):
        """Shutdown NAS."""
        if not self.system:
            _LOGGER.debug("SynoAPI.async_shutdown() - System API not ready: %s", self)
            return
        await self._opp.async_add_executor_job(self.system.shutdown)

    async def async_unload(self):
        """Stop interacting with the NAS and prepare for removal from.opp."""
        self._unsub_dispatcher()

    async def async_update(self, now=None):
        """Update function for updating API information."""
        _LOGGER.debug("SynoAPI.async_update()")
        self._async_setup_api_requests()
        try:
            await self._opp.async_add_executor_job(
                self.dsm.update, self._with_information
            )
        except (SynologyDSMLoginFailedException, SynologyDSMRequestException) as err:
            _LOGGER.warning(
                "async_update - connection error during update, fallback by reloading the entry"
            )
            _LOGGER.debug("SynoAPI.async_update() - exception: %s", err)
            await self._opp.config_entries.async_reload(self._entry.entry_id)
            return
        async_dispatcher_send(self._opp, self.signal_sensor_update)


class SynologyDSMBaseEntity(Entity):
    """Representation of a Synology NAS entry."""

    def __init__(
        self,
        api: SynoApi,
        entity_type: str,
        entity_info: Dict[str, str],
    ):
        """Initialize the Synology DSM entity."""
        self._api = api
        self._api_key = entity_type.split(":")[0]
        self.entity_type = entity_type.split(":")[-1]
        self._name = f"{api.network.hostname} {entity_info[ENTITY_NAME]}"
        self._class = entity_info[ENTITY_CLASS]
        self._enable_default = entity_info[ENTITY_ENABLE]
        self._icon = entity_info[ENTITY_ICON]
        self._unit = entity_info[ENTITY_UNIT]
        self._unique_id = f"{self._api.information.serial}_{entity_type}"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    @property
    def name(self) -> str:
        """Return the name."""
        return self._name

    @property
    def icon(self) -> str:
        """Return the icon."""
        return self._icon

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit the value is expressed in."""
        if self.entity_type in TEMP_SENSORS_KEYS:
            return self.opp.config.units.temperature_unit
        return self._unit

    @property
    def device_class(self) -> str:
        """Return the class of this device."""
        return self._class

    @property
    def device_state_attributes(self) -> Dict[str, any]:
        """Return the state attributes."""
        return {ATTR_ATTRIBUTION: ATTRIBUTION}

    @property
    def device_info(self) -> Dict[str, any]:
        """Return the device information."""
        return {
            "identifiers": {(DOMAIN, self._api.information.serial)},
            "name": "Synology NAS",
            "manufacturer": "Synology",
            "model": self._api.information.model,
            "sw_version": self._api.information.version_string,
        }

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return self._enable_default


class SynologyDSMDispatcherEntity(SynologyDSMBaseEntity, Entity):
    """Representation of a Synology NAS entry."""

    def __init__(
        self,
        api: SynoApi,
        entity_type: str,
        entity_info: Dict[str, str],
    ):
        """Initialize the Synology DSM entity."""
        super().__init__(api, entity_type, entity_info)
        Entity.__init__(self)

    @property
    def should_poll(self) -> bool:
        """No polling needed."""
        return False

    async def async_update(self):
        """Only used by the generic entity update service."""
        if not self.enabled:
            return

        await self._api.async_update()

    async def async_added_to_opp(self):
        """Register state update callback."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.opp, self._api.signal_sensor_update, self.async_write_op.state
            )
        )

        self.async_on_remove(self._api.subscribe(self._api_key, self.unique_id))


class SynologyDSMCoordinatorEntity(SynologyDSMBaseEntity, CoordinatorEntity):
    """Representation of a Synology NAS entry."""

    def __init__(
        self,
        api: SynoApi,
        entity_type: str,
        entity_info: Dict[str, str],
        coordinator: DataUpdateCoordinator,
    ):
        """Initialize the Synology DSM entity."""
        super().__init__(api, entity_type, entity_info)
        CoordinatorEntity.__init__(self, coordinator)


class SynologyDSMDeviceEntity(SynologyDSMDispatcherEntity):
    """Representation of a Synology NAS disk or volume entry."""

    def __init__(
        self,
        api: SynoApi,
        entity_type: str,
        entity_info: Dict[str, str],
        device_id: str = None,
    ):
        """Initialize the Synology DSM disk or volume entity."""
        super().__init__(api, entity_type, entity_info)
        self._device_id = device_id
        self._device_name = None
        self._device_manufacturer = None
        self._device_model = None
        self._device_firmware = None
        self._device_type = None

        if "volume" in entity_type:
            volume = self._api.storage.get_volume(self._device_id)
            # Volume does not have a name
            self._device_name = volume["id"].replace("_", " ").capitalize()
            self._device_manufacturer = "Synology"
            self._device_model = self._api.information.model
            self._device_firmware = self._api.information.version_string
            self._device_type = (
                volume["device_type"]
                .replace("_", " ")
                .replace("raid", "RAID")
                .replace("shr", "SHR")
            )
        elif "disk" in entity_type:
            disk = self._api.storage.get_disk(self._device_id)
            self._device_name = disk["name"]
            self._device_manufacturer = disk["vendor"]
            self._device_model = disk["model"].strip()
            self._device_firmware = disk["firm"]
            self._device_type = disk["diskType"]
        self._name = f"{self._api.network.hostname} {self._device_name} {entity_info[ENTITY_NAME]}"
        self._unique_id += f"_{self._device_id}"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return bool(self._api.storage)

    @property
    def device_info(self) -> Dict[str, any]:
        """Return the device information."""
        return {
            "identifiers": {(DOMAIN, self._api.information.serial, self._device_id)},
            "name": f"Synology NAS ({self._device_name} - {self._device_type})",
            "manufacturer": self._device_manufacturer,
            "model": self._device_model,
            "sw_version": self._device_firmware,
            "via_device": (DOMAIN, self._api.information.serial),
        }
