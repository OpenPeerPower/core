"""Support for Apple HomeKit."""
import asyncio
import ipaddress
import logging
import os

from aiohttp import web
from pyhap.const import STANDALONE_AID
import voluptuous as vol

from openpeerpower.components import zeroconf
from openpeerpower.components.binary_sensor import (
    DEVICE_CLASS_BATTERY_CHARGING,
    DEVICE_CLASS_MOTION,
    DEVICE_CLASS_OCCUPANCY,
    DOMAIN as BINARY_SENSOR_DOMAIN,
)
from openpeerpower.components.camera import DOMAIN as CAMERA_DOMAIN
from openpeerpower.components.http import OpenPeerPowerView
from openpeerpower.components.humidifier import DOMAIN as HUMIDIFIER_DOMAIN
from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.config_entries import SOURCE_IMPORT, ConfigEntry
from openpeerpower.const import (
    ATTR_BATTERY_CHARGING,
    ATTR_BATTERY_LEVEL,
    ATTR_ENTITY_ID,
    CONF_IP_ADDRESS,
    CONF_NAME,
    CONF_PORT,
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_HUMIDITY,
    EVENT_OPENPEERPOWER_STARTED,
    EVENT_OPENPEERPOWER_STOP,
    SERVICE_RELOAD,
)
from openpeerpower.core import CoreState, OpenPeerPower, callback
from openpeerpower.exceptions import ConfigEntryNotReady, Unauthorized
from openpeerpower.helpers import device_registry, entity_registry
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.entityfilter import BASE_FILTER_SCHEMA, FILTER_SCHEMA
from openpeerpower.helpers.reload import async_integration_yaml_config
from openpeerpower.loader import IntegrationNotFound, async_get_integration
from openpeerpower.util import get_local_ip

from . import (  # noqa: F401
    type_cameras,
    type_covers,
    type_fans,
    type_humidifiers,
    type_lights,
    type_locks,
    type_media_players,
    type_security_systems,
    type_sensors,
    type_switches,
    type_thermostats,
)
from .accessories import HomeBridge, HomeDriver, get_accessory
from .aidmanager import AccessoryAidStorage
from .const import (
    AID_STORAGE,
    ATTR_INTERGRATION,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_SOFTWARE_VERSION,
    BRIDGE_NAME,
    BRIDGE_SERIAL_NUMBER,
    CONF_ADVERTISE_IP,
    CONF_AUTO_START,
    CONF_ENTITY_CONFIG,
    CONF_ENTRY_INDEX,
    CONF_EXCLUDE_ACCESSORY_MODE,
    CONF_FILTER,
    CONF_HOMEKIT_MODE,
    CONF_LINKED_BATTERY_CHARGING_SENSOR,
    CONF_LINKED_BATTERY_SENSOR,
    CONF_LINKED_DOORBELL_SENSOR,
    CONF_LINKED_HUMIDITY_SENSOR,
    CONF_LINKED_MOTION_SENSOR,
    CONF_SAFE_MODE,
    CONF_ZEROCONF_DEFAULT_INTERFACE,
    CONFIG_OPTIONS,
    DEFAULT_AUTO_START,
    DEFAULT_EXCLUDE_ACCESSORY_MODE,
    DEFAULT_HOMEKIT_MODE,
    DEFAULT_PORT,
    DEFAULT_SAFE_MODE,
    DOMAIN,
    HOMEKIT,
    HOMEKIT_MODE_ACCESSORY,
    HOMEKIT_MODES,
    HOMEKIT_PAIRING_QR,
    HOMEKIT_PAIRING_QR_SECRET,
    MANUFACTURER,
    SERVICE_HOMEKIT_RESET_ACCESSORY,
    SERVICE_HOMEKIT_START,
    SHUTDOWN_TIMEOUT,
    UNDO_UPDATE_LISTENER,
)
from .util import (
    accessory_friendly_name,
    dismiss_setup_message,
    get_persist_fullpath_for_entry_id,
    port_is_available,
    remove_state_files_for_entry_id,
    show_setup_message,
    state_needs_accessory_mode,
    validate_entity_config,
)

_LOGGER = logging.getLogger(__name__)

MAX_DEVICES = 150

# #### Driver Status ####
STATUS_READY = 0
STATUS_RUNNING = 1
STATUS_STOPPED = 2
STATUS_WAIT = 3


def _has_all_unique_names_and_ports(bridges):
    """Validate that each homekit bridge configured has a unique name."""
    names = [bridge[CONF_NAME] for bridge in bridges]
    ports = [bridge[CONF_PORT] for bridge in bridges]
    vol.Schema(vol.Unique())(names)
    vol.Schema(vol.Unique())(ports)
    return bridges


BRIDGE_SCHEMA = vol.All(
    cv.deprecated(CONF_ZEROCONF_DEFAULT_INTERFACE),
    cv.deprecated(CONF_SAFE_MODE),
    vol.Schema(
        {
            vol.Optional(CONF_HOMEKIT_MODE, default=DEFAULT_HOMEKIT_MODE): vol.In(
                HOMEKIT_MODES
            ),
            vol.Optional(CONF_NAME, default=BRIDGE_NAME): vol.All(
                cv.string, vol.Length(min=3, max=25)
            ),
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
            vol.Optional(CONF_IP_ADDRESS): vol.All(ipaddress.ip_address, cv.string),
            vol.Optional(CONF_ADVERTISE_IP): vol.All(ipaddress.ip_address, cv.string),
            vol.Optional(CONF_AUTO_START, default=DEFAULT_AUTO_START): cv.boolean,
            vol.Optional(CONF_SAFE_MODE, default=DEFAULT_SAFE_MODE): cv.boolean,
            vol.Optional(CONF_FILTER, default={}): BASE_FILTER_SCHEMA,
            vol.Optional(CONF_ENTITY_CONFIG, default={}): validate_entity_config,
            vol.Optional(CONF_ZEROCONF_DEFAULT_INTERFACE): cv.boolean,
        },
        extra=vol.ALLOW_EXTRA,
    ),
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.All(cv.ensure_list, [BRIDGE_SCHEMA], _has_all_unique_names_and_ports)},
    extra=vol.ALLOW_EXTRA,
)


RESET_ACCESSORY_SERVICE_SCHEMA = vol.Schema(
    {vol.Required(ATTR_ENTITY_ID): cv.entity_ids}
)


def _async_get_entries_by_name(current_entries):
    """Return a dict of the entries by name."""

    # For backwards compat, its possible the first bridge is using the default
    # name.
    return {entry.data.get(CONF_NAME, BRIDGE_NAME): entry for entry in current_entries}


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the HomeKit from yaml."""
    opp.data.setdefault(DOMAIN, {})

    _async_register_events_and_services(opp)

    if DOMAIN not in config:
        return True

    current_entries = opp.config_entries.async_entries(DOMAIN)
    entries_by_name = _async_get_entries_by_name(current_entries)

    for index, conf in enumerate(config[DOMAIN]):
        if _async_update_config_entry_if_from_yaml(opp, entries_by_name, conf):
            continue

        conf[CONF_ENTRY_INDEX] = index
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=conf,
            )
        )

    return True


@callback
def _async_update_config_entry_if_from_yaml(opp, entries_by_name, conf):
    """Update a config entry with the latest yaml.

    Returns True if a matching config entry was found

    Returns False if there is no matching config entry
    """
    bridge_name = conf[CONF_NAME]

    if (
        bridge_name in entries_by_name
        and entries_by_name[bridge_name].source == SOURCE_IMPORT
    ):
        entry = entries_by_name[bridge_name]
        # If they alter the yaml config we import the changes
        # since there currently is no practical way to support
        # all the options in the UI at this time.
        data = conf.copy()
        options = {}
        for key in CONFIG_OPTIONS:
            options[key] = data[key]
            del data[key]

        opp.config_entries.async_update_entry(entry, data=data, options=options)
        return True

    return False


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up HomeKit from a config entry."""
    _async_import_options_from_data_if_missing(opp, entry)

    conf = entry.data
    options = entry.options

    name = conf[CONF_NAME]
    port = conf[CONF_PORT]
    _LOGGER.debug("Begin setup HomeKit for %s", name)

    aid_storage = AccessoryAidStorage(opp, entry.entry_id)

    await aid_storage.async_initialize()
    # ip_address and advertise_ip are yaml only
    ip_address = conf.get(CONF_IP_ADDRESS)
    advertise_ip = conf.get(CONF_ADVERTISE_IP)
    # exclude_accessory_mode is only used for config flow
    # to indicate that the config entry was setup after
    # we started creating config entries for entities that
    # to run in accessory mode and that we should never include
    # these entities on the bridge. For backwards compatibility
    # with users who have not migrated yet we do not do exclude
    # these entities by default as we cannot migrate automatically
    # since it requires a re-pairing.
    exclude_accessory_mode = conf.get(
        CONF_EXCLUDE_ACCESSORY_MODE, DEFAULT_EXCLUDE_ACCESSORY_MODE
    )
    homekit_mode = options.get(CONF_HOMEKIT_MODE, DEFAULT_HOMEKIT_MODE)
    entity_config = options.get(CONF_ENTITY_CONFIG, {}).copy()
    auto_start = options.get(CONF_AUTO_START, DEFAULT_AUTO_START)
    entity_filter = FILTER_SCHEMA(options.get(CONF_FILTER, {}))

    homekit = HomeKit(
        opp,
        name,
        port,
        ip_address,
        entity_filter,
        exclude_accessory_mode,
        entity_config,
        homekit_mode,
        advertise_ip,
        entry.entry_id,
        entry.title,
    )
    zeroconf_instance = await zeroconf.async_get_instance(opp)

    # If the previous instance hasn't cleaned up yet
    # we need to wait a bit
    try:
        await opp.async_add_executor_job(homekit.setup, zeroconf_instance)
    except (OSError, AttributeError) as ex:
        _LOGGER.warning(
            "%s could not be setup because the local port %s is in use", name, port
        )
        raise ConfigEntryNotReady from ex

    undo_listener = entry.add_update_listener(_async_update_listener)

    opp.data[DOMAIN][entry.entry_id] = {
        AID_STORAGE: aid_storage,
        HOMEKIT: homekit,
        UNDO_UPDATE_LISTENER: undo_listener,
    }

    if opp.state == CoreState.running:
        await homekit.async_start()
    elif auto_start:
        opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STARTED, homekit.async_start)

    return True


async def _async_update_listener(opp: OpenPeerPower, entry: ConfigEntry):
    """Handle options update."""
    if entry.source == SOURCE_IMPORT:
        return
    await opp.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    dismiss_setup_message(opp, entry.entry_id)

    opp.data[DOMAIN][entry.entry_id][UNDO_UPDATE_LISTENER]()

    homekit = opp.data[DOMAIN][entry.entry_id][HOMEKIT]

    if homekit.status == STATUS_RUNNING:
        await homekit.async_stop()

    for _ in range(0, SHUTDOWN_TIMEOUT):
        if not await opp.async_add_executor_job(
            port_is_available, entry.data[CONF_PORT]
        ):
            _LOGGER.info("Waiting for the HomeKit server to shutdown")
            await asyncio.sleep(1)

    opp.data[DOMAIN].pop(entry.entry_id)

    return True


async def async_remove_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Remove a config entry."""
    return await opp.async_add_executor_job(
        remove_state_files_for_entry_id, opp, entry.entry_id
    )


@callback
def _async_import_options_from_data_if_missing(opp: OpenPeerPower, entry: ConfigEntry):
    options = dict(entry.options)
    data = dict(entry.data)
    modified = False
    for importable_option in CONFIG_OPTIONS:
        if importable_option not in entry.options and importable_option in entry.data:
            options[importable_option] = entry.data[importable_option]
            del data[importable_option]
            modified = True

    if modified:
        opp.config_entries.async_update_entry(entry, data=data, options=options)


@callback
def _async_register_events_and_services(opp: OpenPeerPower):
    """Register events and services for HomeKit."""
    opp.http.register_view(HomeKitPairingQRView)

    def handle_homekit_reset_accessory(service):
        """Handle start HomeKit service call."""
        for entry_id in opp.data[DOMAIN]:
            if HOMEKIT not in opp.data[DOMAIN][entry_id]:
                continue
            homekit = opp.data[DOMAIN][entry_id][HOMEKIT]
            if homekit.status != STATUS_RUNNING:
                _LOGGER.warning(
                    "HomeKit is not running. Either it is waiting to be "
                    "started or has been stopped"
                )
                continue

            entity_ids = service.data.get("entity_id")
            homekit.reset_accessories(entity_ids)

    opp.services.async_register(
        DOMAIN,
        SERVICE_HOMEKIT_RESET_ACCESSORY,
        handle_homekit_reset_accessory,
        schema=RESET_ACCESSORY_SERVICE_SCHEMA,
    )

    async def async_handle_homekit_service_start(service):
        """Handle start HomeKit service call."""
        tasks = []
        for entry_id in opp.data[DOMAIN]:
            if HOMEKIT not in opp.data[DOMAIN][entry_id]:
                continue
            homekit = opp.data[DOMAIN][entry_id][HOMEKIT]
            if homekit.status == STATUS_RUNNING:
                _LOGGER.debug("HomeKit is already running")
                continue
            if homekit.status != STATUS_READY:
                _LOGGER.warning(
                    "HomeKit is not ready. Either it is already starting up or has "
                    "been stopped"
                )
                continue
            tasks.append(homekit.async_start())
        await asyncio.gather(*tasks)

    opp.services.async_register(
        DOMAIN, SERVICE_HOMEKIT_START, async_handle_homekit_service_start
    )

    async def _handle_homekit_reload(service):
        """Handle start HomeKit service call."""
        config = await async_integration_yaml_config(opp, DOMAIN)

        if not config or DOMAIN not in config:
            return

        current_entries = opp.config_entries.async_entries(DOMAIN)
        entries_by_name = _async_get_entries_by_name(current_entries)

        for conf in config[DOMAIN]:
            _async_update_config_entry_if_from_yaml(opp, entries_by_name, conf)

        reload_tasks = [
            opp.config_entries.async_reload(entry.entry_id) for entry in current_entries
        ]

        await asyncio.gather(*reload_tasks)

    opp.helpers.service.async_register_admin_service(
        DOMAIN,
        SERVICE_RELOAD,
        _handle_homekit_reload,
    )


class HomeKit:
    """Class to handle all actions between HomeKit and Open Peer Power."""

    def __init__(
        self,
        opp,
        name,
        port,
        ip_address,
        entity_filter,
        exclude_accessory_mode,
        entity_config,
        homekit_mode,
        advertise_ip=None,
        entry_id=None,
        entry_title=None,
    ):
        """Initialize a HomeKit object."""
        self.opp = opp
        self._name = name
        self._port = port
        self._ip_address = ip_address
        self._filter = entity_filter
        self._config = entity_config
        self._exclude_accessory_mode = exclude_accessory_mode
        self._advertise_ip = advertise_ip
        self._entry_id = entry_id
        self._entry_title = entry_title
        self._homekit_mode = homekit_mode
        self.status = STATUS_READY

        self.bridge = None
        self.driver = None

    def setup(self, zeroconf_instance):
        """Set up bridge and accessory driver."""
        self.opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, self.async_stop)
        ip_addr = self._ip_address or get_local_ip()
        persist_file = get_persist_fullpath_for_entry_id(self.opp, self._entry_id)

        self.driver = HomeDriver(
            self.opp,
            self._entry_id,
            self._name,
            self._entry_title,
            loop=self.opp.loop,
            address=ip_addr,
            port=self._port,
            persist_file=persist_file,
            advertised_address=self._advertise_ip,
            zeroconf_instance=zeroconf_instance,
        )

        # If we do not load the mac address will be wrong
        # as pyhap uses a random one until state is restored
        if os.path.exists(persist_file):
            self.driver.load()
            self.driver.state.config_version += 1
            if self.driver.state.config_version > 65535:
                self.driver.state.config_version = 1

        self.driver.persist()

    def reset_accessories(self, entity_ids):
        """Reset the accessory to load the latest configuration."""
        if not self.bridge:
            self.driver.config_changed()
            return

        aid_storage = self.opp.data[DOMAIN][self._entry_id][AID_STORAGE]
        removed = []
        for entity_id in entity_ids:
            aid = aid_storage.get_or_allocate_aid_for_entity_id(entity_id)
            if aid not in self.bridge.accessories:
                continue

            _LOGGER.info(
                "HomeKit Bridge %s will reset accessory with linked entity_id %s",
                self._name,
                entity_id,
            )

            acc = self.remove_bridge_accessory(aid)
            removed.append(acc)

        if not removed:
            # No matched accessories, probably on another bridge
            return

        self.driver.config_changed()

        for acc in removed:
            self.bridge.add_accessory(acc)
        self.driver.config_changed()

    def add_bridge_accessory(self, state):
        """Try adding accessory to bridge if configured beforehand."""
        if not self._filter(state.entity_id):
            return

        # The bridge itself counts as an accessory
        if len(self.bridge.accessories) + 1 >= MAX_DEVICES:
            _LOGGER.warning(
                "Cannot add %s as this would exceed the %d device limit. Consider using the filter option",
                state.entity_id,
                MAX_DEVICES,
            )
            return

        if state_needs_accessory_mode(state):
            if self._exclude_accessory_mode:
                return
            _LOGGER.warning(
                "The bridge %s has entity %s. For best performance, "
                "and to prevent unexpected unavailability, create and "
                "pair a separate HomeKit instance in accessory mode for "
                "this entity.",
                self._name,
                state.entity_id,
            )

        aid = self.opp.data[DOMAIN][self._entry_id][
            AID_STORAGE
        ].get_or_allocate_aid_for_entity_id(state.entity_id)
        conf = self._config.pop(state.entity_id, {})
        # If an accessory cannot be created or added due to an exception
        # of any kind (usually in pyhap) it should not prevent
        # the rest of the accessories from being created
        try:
            acc = get_accessory(self.opp, self.driver, state, aid, conf)
            if acc is not None:
                self.bridge.add_accessory(acc)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception(
                "Failed to create a HomeKit accessory for %s", state.entity_id
            )

    def remove_bridge_accessory(self, aid):
        """Try adding accessory to bridge if configured beforehand."""
        acc = None
        if aid in self.bridge.accessories:
            acc = self.bridge.accessories.pop(aid)
        return acc

    async def async_start(self, *args):
        """Start the accessory driver."""
        if self.status != STATUS_READY:
            return
        self.status = STATUS_WAIT

        ent_reg = await entity_registry.async_get_registry(self.opp)
        dev_reg = await device_registry.async_get_registry(self.opp)

        device_lookup = ent_reg.async_get_device_class_lookup(
            {
                (BINARY_SENSOR_DOMAIN, DEVICE_CLASS_BATTERY_CHARGING),
                (BINARY_SENSOR_DOMAIN, DEVICE_CLASS_MOTION),
                (BINARY_SENSOR_DOMAIN, DEVICE_CLASS_OCCUPANCY),
                (SENSOR_DOMAIN, DEVICE_CLASS_BATTERY),
                (SENSOR_DOMAIN, DEVICE_CLASS_HUMIDITY),
            }
        )

        bridged_states = []
        for state in self.opp.states.async_all():
            entity_id = state.entity_id

            if not self._filter(entity_id):
                continue

            ent_reg_ent = ent_reg.async_get(entity_id)
            if ent_reg_ent:
                await self._async_set_device_info_attributes(
                    ent_reg_ent, dev_reg, entity_id
                )
                self._async_configure_linked_sensors(ent_reg_ent, device_lookup, state)

            bridged_states.append(state)

        self._async_register_bridge(dev_reg)
        await self._async_start(bridged_states)
        _LOGGER.debug("Driver start for %s", self._name)
        self.opp.add_job(self.driver.start_service)
        self.status = STATUS_RUNNING

    @callback
    def _async_register_bridge(self, dev_reg):
        """Register the bridge as a device so homekit_controller and exclude it from discovery."""
        formatted_mac = device_registry.format_mac(self.driver.state.mac)
        # Connections and identifiers are both used here.
        #
        # connections exists so homekit_controller can know the
        # virtual mac address of the bridge and know to not offer
        # it via discovery.
        #
        # identifiers is used as well since the virtual mac may change
        # because it will not survive manual pairing resets (deleting state file)
        # which we have trained users to do over the past few years
        # because this was the way you had to fix homekit when pairing
        # failed.
        #
        connection = (device_registry.CONNECTION_NETWORK_MAC, formatted_mac)
        identifier = (DOMAIN, self._entry_id, BRIDGE_SERIAL_NUMBER)
        self._async_purge_old_bridges(dev_reg, identifier, connection)
        is_accessory_mode = self._homekit_mode == HOMEKIT_MODE_ACCESSORY
        hk_mode_name = "Accessory" if is_accessory_mode else "Bridge"
        dev_reg.async_get_or_create(
            config_entry_id=self._entry_id,
            identifiers={identifier},
            connections={connection},
            manufacturer=MANUFACTURER,
            name=self._name,
            model=f"Open Peer Power HomeKit {hk_mode_name}",
        )

    @callback
    def _async_purge_old_bridges(self, dev_reg, identifier, connection):
        """Purge bridges that exist from failed pairing or manual resets."""
        devices_to_purge = []
        for entry in dev_reg.devices.values():
            if self._entry_id in entry.config_entries and (
                identifier not in entry.identifiers
                or connection not in entry.connections
            ):
                devices_to_purge.append(entry.id)

        for device_id in devices_to_purge:
            dev_reg.async_remove_device(device_id)

    async def _async_start(self, entity_states):
        """Start the accessory."""
        if self._homekit_mode == HOMEKIT_MODE_ACCESSORY:
            state = entity_states[0]
            conf = self._config.pop(state.entity_id, {})
            acc = get_accessory(self.opp, self.driver, state, STANDALONE_AID, conf)

            self.driver.add_accessory(acc)
        else:
            self.bridge = HomeBridge(self.opp, self.driver, self._name)
            for state in entity_states:
                self.add_bridge_accessory(state)
            acc = self.bridge

        await self.opp.async_add_executor_job(self.driver.add_accessory, acc)

        if not self.driver.state.paired:
            show_setup_message(
                self.opp,
                self._entry_id,
                accessory_friendly_name(self._entry_title, self.driver.accessory),
                self.driver.state.pincode,
                self.driver.accessory.xhm_uri(),
            )

    async def async_stop(self, *args):
        """Stop the accessory driver."""
        if self.status != STATUS_RUNNING:
            return
        self.status = STATUS_STOPPED
        _LOGGER.debug("Driver stop for %s", self._name)
        await self.driver.async_stop()
        if self.bridge:
            for acc in self.bridge.accessories.values():
                acc.async_stop()
        else:
            self.driver.accessory.async_stop()

    @callback
    def _async_configure_linked_sensors(self, ent_reg_ent, device_lookup, state):
        if (
            ent_reg_ent is None
            or ent_reg_ent.device_id is None
            or ent_reg_ent.device_id not in device_lookup
            or ent_reg_ent.device_class
            in (DEVICE_CLASS_BATTERY_CHARGING, DEVICE_CLASS_BATTERY)
        ):
            return

        if ATTR_BATTERY_CHARGING not in state.attributes:
            battery_charging_binary_sensor_entity_id = device_lookup[
                ent_reg_ent.device_id
            ].get((BINARY_SENSOR_DOMAIN, DEVICE_CLASS_BATTERY_CHARGING))
            if battery_charging_binary_sensor_entity_id:
                self._config.setdefault(state.entity_id, {}).setdefault(
                    CONF_LINKED_BATTERY_CHARGING_SENSOR,
                    battery_charging_binary_sensor_entity_id,
                )

        if ATTR_BATTERY_LEVEL not in state.attributes:
            battery_sensor_entity_id = device_lookup[ent_reg_ent.device_id].get(
                (SENSOR_DOMAIN, DEVICE_CLASS_BATTERY)
            )
            if battery_sensor_entity_id:
                self._config.setdefault(state.entity_id, {}).setdefault(
                    CONF_LINKED_BATTERY_SENSOR, battery_sensor_entity_id
                )

        if state.entity_id.startswith(f"{CAMERA_DOMAIN}."):
            motion_binary_sensor_entity_id = device_lookup[ent_reg_ent.device_id].get(
                (BINARY_SENSOR_DOMAIN, DEVICE_CLASS_MOTION)
            )
            if motion_binary_sensor_entity_id:
                self._config.setdefault(state.entity_id, {}).setdefault(
                    CONF_LINKED_MOTION_SENSOR,
                    motion_binary_sensor_entity_id,
                )
            doorbell_binary_sensor_entity_id = device_lookup[ent_reg_ent.device_id].get(
                (BINARY_SENSOR_DOMAIN, DEVICE_CLASS_OCCUPANCY)
            )
            if doorbell_binary_sensor_entity_id:
                self._config.setdefault(state.entity_id, {}).setdefault(
                    CONF_LINKED_DOORBELL_SENSOR,
                    doorbell_binary_sensor_entity_id,
                )

        if state.entity_id.startswith(f"{HUMIDIFIER_DOMAIN}."):
            current_humidity_sensor_entity_id = device_lookup[
                ent_reg_ent.device_id
            ].get((SENSOR_DOMAIN, DEVICE_CLASS_HUMIDITY))
            if current_humidity_sensor_entity_id:
                self._config.setdefault(state.entity_id, {}).setdefault(
                    CONF_LINKED_HUMIDITY_SENSOR,
                    current_humidity_sensor_entity_id,
                )

    async def _async_set_device_info_attributes(self, ent_reg_ent, dev_reg, entity_id):
        """Set attributes that will be used for homekit device info."""
        ent_cfg = self._config.setdefault(entity_id, {})
        if ent_reg_ent.device_id:
            dev_reg_ent = dev_reg.async_get(ent_reg_ent.device_id)
            if dev_reg_ent is not None:
                # Handle missing devices
                if dev_reg_ent.manufacturer:
                    ent_cfg[ATTR_MANUFACTURER] = dev_reg_ent.manufacturer
                if dev_reg_ent.model:
                    ent_cfg[ATTR_MODEL] = dev_reg_ent.model
                if dev_reg_ent.sw_version:
                    ent_cfg[ATTR_SOFTWARE_VERSION] = dev_reg_ent.sw_version
        if ATTR_MANUFACTURER not in ent_cfg:
            try:
                integration = await async_get_integration(
                    self.opp, ent_reg_ent.platform
                )
                ent_cfg[ATTR_INTERGRATION] = integration.name
            except IntegrationNotFound:
                ent_cfg[ATTR_INTERGRATION] = ent_reg_ent.platform


class HomeKitPairingQRView(OpenPeerPowerView):
    """Display the homekit pairing code at a protected url."""

    url = "/api/homekit/pairingqr"
    name = "api:homekit:pairingqr"
    requires_auth = False

    async def get(self, request):
        """Retrieve the pairing QRCode image."""
        if not request.query_string:
            raise Unauthorized()
        entry_id, secret = request.query_string.split("-")

        if (
            entry_id not in request.app["opp"].data[DOMAIN]
            or secret
            != request.app["opp"].data[DOMAIN][entry_id][HOMEKIT_PAIRING_QR_SECRET]
        ):
            raise Unauthorized()
        return web.Response(
            body=request.app["opp"].data[DOMAIN][entry_id][HOMEKIT_PAIRING_QR],
            content_type="image/svg+xml",
        )
