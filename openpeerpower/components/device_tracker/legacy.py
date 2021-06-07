"""Legacy device tracker classes."""
from __future__ import annotations

import asyncio
from collections.abc import Coroutine, Sequence
from datetime import timedelta
import hashlib
from types import ModuleType
from typing import Any, Callable, Final, final

import attr
import voluptuous as vol

from openpeerpower import util
from openpeerpower.components import zone
from openpeerpower.config import async_log_exception, load_yaml_config_file
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_GPS_ACCURACY,
    ATTR_ICON,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    ATTR_NAME,
    CONF_ICON,
    CONF_MAC,
    CONF_NAME,
    DEVICE_DEFAULT_NAME,
    STATE_HOME,
    STATE_NOT_HOME,
)
from openpeerpower.core import OpenPeerPower, ServiceCall, callback
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.helpers import config_per_platform, discovery
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.entity_registry import async_get_registry
from openpeerpower.helpers.event import (
    async_track_time_interval,
    async_track_utc_time_change,
)
from openpeerpower.helpers.restore_state import RestoreEntity
from openpeerpower.helpers.typing import ConfigType, GPSType, StateType
from openpeerpower.setup import async_prepare_setup_platform, async_start_setup
from openpeerpower.util import dt as dt_util
from openpeerpower.util.yaml import dump

from .const import (
    ATTR_ATTRIBUTES,
    ATTR_BATTERY,
    ATTR_CONSIDER_HOME,
    ATTR_DEV_ID,
    ATTR_GPS,
    ATTR_HOST_NAME,
    ATTR_LOCATION_NAME,
    ATTR_MAC,
    ATTR_SOURCE_TYPE,
    CONF_CONSIDER_HOME,
    CONF_NEW_DEVICE_DEFAULTS,
    CONF_SCAN_INTERVAL,
    CONF_TRACK_NEW,
    DEFAULT_CONSIDER_HOME,
    DEFAULT_TRACK_NEW,
    DOMAIN,
    LOGGER,
    PLATFORM_TYPE_LEGACY,
    SCAN_INTERVAL,
    SOURCE_TYPE_BLUETOOTH,
    SOURCE_TYPE_BLUETOOTH_LE,
    SOURCE_TYPE_GPS,
    SOURCE_TYPE_ROUTER,
)

SERVICE_SEE: Final = "see"

SOURCE_TYPES: Final[tuple[str, ...]] = (
    SOURCE_TYPE_GPS,
    SOURCE_TYPE_ROUTER,
    SOURCE_TYPE_BLUETOOTH,
    SOURCE_TYPE_BLUETOOTH_LE,
)

NEW_DEVICE_DEFAULTS_SCHEMA = vol.Any(
    None,
    vol.Schema({vol.Optional(CONF_TRACK_NEW, default=DEFAULT_TRACK_NEW): cv.boolean}),
)
PLATFORM_SCHEMA: Final = cv.PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_SCAN_INTERVAL): cv.time_period,
        vol.Optional(CONF_TRACK_NEW): cv.boolean,
        vol.Optional(CONF_CONSIDER_HOME, default=DEFAULT_CONSIDER_HOME): vol.All(
            cv.time_period, cv.positive_timedelta
        ),
        vol.Optional(CONF_NEW_DEVICE_DEFAULTS, default={}): NEW_DEVICE_DEFAULTS_SCHEMA,
    }
)
PLATFORM_SCHEMA_BASE: Final[vol.Schema] = cv.PLATFORM_SCHEMA_BASE.extend(
    PLATFORM_SCHEMA.schema
)

SERVICE_SEE_PAYLOAD_SCHEMA: Final[vol.Schema] = vol.Schema(
    vol.All(
        cv.has_at_least_one_key(ATTR_MAC, ATTR_DEV_ID),
        {
            ATTR_MAC: cv.string,
            ATTR_DEV_ID: cv.string,
            ATTR_HOST_NAME: cv.string,
            ATTR_LOCATION_NAME: cv.string,
            ATTR_GPS: cv.gps,
            ATTR_GPS_ACCURACY: cv.positive_int,
            ATTR_BATTERY: cv.positive_int,
            ATTR_ATTRIBUTES: dict,
            ATTR_SOURCE_TYPE: vol.In(SOURCE_TYPES),
            ATTR_CONSIDER_HOME: cv.time_period,
            # Temp workaround for iOS app introduced in 0.65
            vol.Optional("battery_status"): str,
            vol.Optional("hostname"): str,
        },
    )
)

YAML_DEVICES: Final = "known_devices.yaml"
EVENT_NEW_DEVICE: Final = "device_tracker_new_device"


def see(
    opp: OpenPeerPower,
    mac: str | None = None,
    dev_id: str | None = None,
    host_name: str | None = None,
    location_name: str | None = None,
    gps: GPSType | None = None,
    gps_accuracy: int | None = None,
    battery: int | None = None,
    attributes: dict | None = None,
) -> None:
    """Call service to notify you see device."""
    data: dict[str, Any] = {
        key: value
        for key, value in (
            (ATTR_MAC, mac),
            (ATTR_DEV_ID, dev_id),
            (ATTR_HOST_NAME, host_name),
            (ATTR_LOCATION_NAME, location_name),
            (ATTR_GPS, gps),
            (ATTR_GPS_ACCURACY, gps_accuracy),
            (ATTR_BATTERY, battery),
        )
        if value is not None
    }
    if attributes is not None:
        data[ATTR_ATTRIBUTES] = attributes
    opp.services.call(DOMAIN, SERVICE_SEE, data)


async def async_setup_integration(opp: OpenPeerPower, config: ConfigType) -> None:
    """Set up the legacy integration."""
    tracker = await get_tracker(opp, config)

    legacy_platforms = await async_extract_config(opp, config)

    setup_tasks = [
        asyncio.create_task(legacy_platform.async_setup_legacy(opp, tracker))
        for legacy_platform in legacy_platforms
    ]

    if setup_tasks:
        await asyncio.wait(setup_tasks)

    async def async_platform_discovered(
        p_type: str, info: dict[str, Any] | None
    ) -> None:
        """Load a platform."""
        platform = await async_create_platform_type(opp, config, p_type, {})

        if platform is None or platform.type != PLATFORM_TYPE_LEGACY:
            return

        await platform.async_setup_legacy(opp, tracker, info)

    discovery.async_listen_platform(opp, DOMAIN, async_platform_discovered)

    # Clean up stale devices
    async_track_utc_time_change(opp, tracker.async_update_stale, second=range(0, 60, 5))

    async def async_see_service(call: ServiceCall) -> None:
        """Service to see a device."""
        # Temp workaround for iOS, introduced in 0.65
        data = dict(call.data)
        data.pop("hostname", None)
        data.pop("battery_status", None)
        await tracker.async_see(**data)

    opp.services.async_register(
        DOMAIN, SERVICE_SEE, async_see_service, SERVICE_SEE_PAYLOAD_SCHEMA
    )

    # restore
    await tracker.async_setup_tracked_device()


@attr.s
class DeviceTrackerPlatform:
    """Class to hold platform information."""

    LEGACY_SETUP: Final[tuple[str, ...]] = (
        "async_get_scanner",
        "get_scanner",
        "async_setup_scanner",
        "setup_scanner",
    )

    name: str = attr.ib()
    platform: ModuleType = attr.ib()
    config: dict = attr.ib()

    @property
    def type(self) -> str | None:
        """Return platform type."""
        methods, platform_type = self.LEGACY_SETUP, PLATFORM_TYPE_LEGACY
        for method in methods:
            if hasattr(self.platform, method):
                return platform_type
        return None

    async def async_setup_legacy(
        self,
        opp: OpenPeerPower,
        tracker: DeviceTracker,
        discovery_info: dict[str, Any] | None = None,
    ) -> None:
        """Set up a legacy platform."""
        assert self.type == PLATFORM_TYPE_LEGACY
        full_name = f"{DOMAIN}.{self.name}"
        LOGGER.info("Setting up %s", full_name)
        with async_start_setup(opp, [full_name]):
            try:
                scanner = None
                setup = None
                if hasattr(self.platform, "async_get_scanner"):
                    scanner = await self.platform.async_get_scanner(  # type: ignore[attr-defined]
                        opp, {DOMAIN: self.config}
                    )
                elif hasattr(self.platform, "get_scanner"):
                    scanner = await opp.async_add_executor_job(
                        self.platform.get_scanner,  # type: ignore[attr-defined]
                        opp,
                        {DOMAIN: self.config},
                    )
                elif hasattr(self.platform, "async_setup_scanner"):
                    setup = await self.platform.async_setup_scanner(  # type: ignore[attr-defined]
                        opp, self.config, tracker.async_see, discovery_info
                    )
                elif hasattr(self.platform, "setup_scanner"):
                    setup = await opp.async_add_executor_job(
                        self.platform.setup_scanner,  # type: ignore[attr-defined]
                        opp,
                        self.config,
                        tracker.see,
                        discovery_info,
                    )
                else:
                    raise OpenPeerPowerError("Invalid legacy device_tracker platform.")

                if scanner is not None:
                    async_setup_scanner_platform(
                        opp, self.config, scanner, tracker.async_see, self.type
                    )

                if setup is None and scanner is None:
                    LOGGER.error(
                        "Error setting up platform %s %s", self.type, self.name
                    )
                    return

                opp.config.components.add(full_name)

            except Exception:  # pylint: disable=broad-except
                LOGGER.exception(
                    "Error setting up platform %s %s", self.type, self.name
                )


async def async_extract_config(
    opp: OpenPeerPower, config: ConfigType
) -> list[DeviceTrackerPlatform]:
    """Extract device tracker config and split between legacy and modern."""
    legacy: list[DeviceTrackerPlatform] = []

    for platform in await asyncio.gather(
        *(
            async_create_platform_type(opp, config, p_type, p_config)
            for p_type, p_config in config_per_platform(config, DOMAIN)
        )
    ):
        if platform is None:
            continue

        if platform.type == PLATFORM_TYPE_LEGACY:
            legacy.append(platform)
        else:
            raise ValueError(
                f"Unable to determine type for {platform.name}: {platform.type}"
            )

    return legacy


async def async_create_platform_type(
    opp: OpenPeerPower, config: ConfigType, p_type: str, p_config: dict
) -> DeviceTrackerPlatform | None:
    """Determine type of platform."""
    platform = await async_prepare_setup_platform(opp, config, DOMAIN, p_type)

    if platform is None:
        return None

    return DeviceTrackerPlatform(p_type, platform, p_config)


@callback
def async_setup_scanner_platform(
    opp: OpenPeerPower,
    config: ConfigType,
    scanner: DeviceScanner,
    async_see_device: Callable[..., Coroutine[None, None, None]],
    platform: str,
) -> None:
    """Set up the connect scanner-based platform to device tracker.

    This method must be run in the event loop.
    """
    interval = config.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL)
    update_lock = asyncio.Lock()
    scanner.opp = opp

    # Initial scan of each mac we also tell about host name for config
    seen: Any = set()

    async def async_device_tracker_scan(now: dt_util.dt.datetime | None) -> None:
        """Handle interval matches."""
        if update_lock.locked():
            LOGGER.warning(
                "Updating device list from %s took longer than the scheduled "
                "scan interval %s",
                platform,
                interval,
            )
            return

        async with update_lock:
            found_devices = await scanner.async_scan_devices()

        for mac in found_devices:
            if mac in seen:
                host_name = None
            else:
                host_name = await scanner.async_get_device_name(mac)
                seen.add(mac)

            try:
                extra_attributes = await scanner.async_get_extra_attributes(mac)
            except NotImplementedError:
                extra_attributes = {}

            kwargs: dict[str, Any] = {
                "mac": mac,
                "host_name": host_name,
                "source_type": SOURCE_TYPE_ROUTER,
                "attributes": {
                    "scanner": scanner.__class__.__name__,
                    **extra_attributes,
                },
            }

            zone_home = opp.states.get(opp.components.zone.ENTITY_ID_HOME)
            if zone_home is not None:
                kwargs["gps"] = [
                    zone_home.attributes[ATTR_LATITUDE],
                    zone_home.attributes[ATTR_LONGITUDE],
                ]
                kwargs["gps_accuracy"] = 0

            opp.async_create_task(async_see_device(**kwargs))

    async_track_time_interval(opp, async_device_tracker_scan, interval)
    opp.async_create_task(async_device_tracker_scan(None))


async def get_tracker(opp: OpenPeerPower, config: ConfigType) -> DeviceTracker:
    """Create a tracker."""
    yaml_path = opp.config.path(YAML_DEVICES)

    conf = config.get(DOMAIN, [])
    conf = conf[0] if conf else {}
    consider_home = conf.get(CONF_CONSIDER_HOME, DEFAULT_CONSIDER_HOME)

    defaults = conf.get(CONF_NEW_DEVICE_DEFAULTS, {})
    track_new = conf.get(CONF_TRACK_NEW)
    if track_new is None:
        track_new = defaults.get(CONF_TRACK_NEW, DEFAULT_TRACK_NEW)

    devices = await async_load_config(yaml_path, opp, consider_home)
    tracker = DeviceTracker(opp, consider_home, track_new, defaults, devices)
    return tracker


class DeviceTracker:
    """Representation of a device tracker."""

    def __init__(
        self,
        opp: OpenPeerPower,
        consider_home: timedelta,
        track_new: bool,
        defaults: dict[str, Any],
        devices: Sequence[Device],
    ) -> None:
        """Initialize a device tracker."""
        self.opp = opp
        self.devices: dict[str, Device] = {dev.dev_id: dev for dev in devices}
        self.mac_to_dev = {dev.mac: dev for dev in devices if dev.mac}
        self.consider_home = consider_home
        self.track_new = (
            track_new
            if track_new is not None
            else defaults.get(CONF_TRACK_NEW, DEFAULT_TRACK_NEW)
        )
        self.defaults = defaults
        self._is_updating = asyncio.Lock()

        for dev in devices:
            if self.devices[dev.dev_id] is not dev:
                LOGGER.warning("Duplicate device IDs detected %s", dev.dev_id)
            if dev.mac and self.mac_to_dev[dev.mac] is not dev:
                LOGGER.warning("Duplicate device MAC addresses detected %s", dev.mac)

    def see(
        self,
        mac: str | None = None,
        dev_id: str | None = None,
        host_name: str | None = None,
        location_name: str | None = None,
        gps: GPSType | None = None,
        gps_accuracy: int | None = None,
        battery: int | None = None,
        attributes: dict | None = None,
        source_type: str = SOURCE_TYPE_GPS,
        picture: str | None = None,
        icon: str | None = None,
        consider_home: timedelta | None = None,
    ) -> None:
        """Notify the device tracker that you see a device."""
        self.opp.create_task(
            self.async_see(
                mac,
                dev_id,
                host_name,
                location_name,
                gps,
                gps_accuracy,
                battery,
                attributes,
                source_type,
                picture,
                icon,
                consider_home,
            )
        )

    async def async_see(
        self,
        mac: str | None = None,
        dev_id: str | None = None,
        host_name: str | None = None,
        location_name: str | None = None,
        gps: GPSType | None = None,
        gps_accuracy: int | None = None,
        battery: int | None = None,
        attributes: dict | None = None,
        source_type: str = SOURCE_TYPE_GPS,
        picture: str | None = None,
        icon: str | None = None,
        consider_home: timedelta | None = None,
    ) -> None:
        """Notify the device tracker that you see a device.

        This method is a coroutine.
        """
        registry = await async_get_registry(self.opp)
        if mac is None and dev_id is None:
            raise OpenPeerPowerError("Neither mac or device id passed in")
        if mac is not None:
            mac = str(mac).upper()
            device = self.mac_to_dev.get(mac)
            if device is None:
                dev_id = util.slugify(host_name or "") or util.slugify(mac)
        else:
            dev_id = cv.slug(str(dev_id).lower())
            device = self.devices.get(dev_id)

        if device is not None:
            await device.async_seen(
                host_name,
                location_name,
                gps,
                gps_accuracy,
                battery,
                attributes,
                source_type,
                consider_home,
            )
            if device.track:
                device.async_write_op_state()
            return

        # If it's None then device is not None and we can't get here.
        assert dev_id is not None

        # Guard from calling see on entity registry entities.
        entity_id = f"{DOMAIN}.{dev_id}"
        if registry.async_is_registered(entity_id):
            LOGGER.error(
                "The see service is not supported for this entity %s", entity_id
            )
            return

        # If no device can be found, create it
        dev_id = util.ensure_unique_string(dev_id, self.devices.keys())
        device = Device(
            self.opp,
            consider_home or self.consider_home,
            self.track_new,
            dev_id,
            mac,
            picture=picture,
            icon=icon,
        )
        self.devices[dev_id] = device
        if mac is not None:
            self.mac_to_dev[mac] = device

        await device.async_seen(
            host_name,
            location_name,
            gps,
            gps_accuracy,
            battery,
            attributes,
            source_type,
        )

        if device.track:
            device.async_write_op_state()

        self.opp.bus.async_fire(
            EVENT_NEW_DEVICE,
            {
                ATTR_ENTITY_ID: device.entity_id,
                ATTR_HOST_NAME: device.host_name,
                ATTR_MAC: device.mac,
            },
        )

        # update known_devices.yaml
        self.opp.async_create_task(
            self.async_update_config(self.opp.config.path(YAML_DEVICES), dev_id, device)
        )

    async def async_update_config(self, path: str, dev_id: str, device: Device) -> None:
        """Add device to YAML configuration file.

        This method is a coroutine.
        """
        async with self._is_updating:
            await self.opp.async_add_executor_job(
                update_config, self.opp.config.path(YAML_DEVICES), dev_id, device
            )

    @callback
    def async_update_stale(self, now: dt_util.dt.datetime) -> None:
        """Update stale devices.

        This method must be run in the event loop.
        """
        for device in self.devices.values():
            if (device.track and device.last_update_home) and device.stale(now):
                self.opp.async_create_task(device.async_update_op_state(True))

    async def async_setup_tracked_device(self) -> None:
        """Set up all not exists tracked devices.

        This method is a coroutine.
        """

        async def async_init_single_device(dev: Device) -> None:
            """Init a single device_tracker entity."""
            await dev.async_added_to_opp()
            dev.async_write_op_state()

        tasks: list[asyncio.Task] = []
        for device in self.devices.values():
            if device.track and not device.last_seen:
                tasks.append(
                    self.opp.async_create_task(async_init_single_device(device))
                )

        if tasks:
            await asyncio.wait(tasks)


class Device(RestoreEntity):
    """Base class for a tracked device."""

    host_name: str | None = None
    location_name: str | None = None
    gps: GPSType | None = None
    gps_accuracy: int = 0
    last_seen: dt_util.dt.datetime | None = None
    battery: int | None = None
    attributes: dict | None = None

    # Track if the last update of this device was HOME.
    last_update_home: bool = False
    _state: str = STATE_NOT_HOME

    def __init__(
        self,
        opp: OpenPeerPower,
        consider_home: timedelta,
        track: bool,
        dev_id: str,
        mac: str | None,
        name: str | None = None,
        picture: str | None = None,
        gravatar: str | None = None,
        icon: str | None = None,
    ) -> None:
        """Initialize a device."""
        self.opp = opp
        self.entity_id = f"{DOMAIN}.{dev_id}"

        # Timedelta object how long we consider a device home if it is not
        # detected anymore.
        self.consider_home = consider_home

        # Device ID
        self.dev_id = dev_id
        self.mac = mac

        # If we should track this device
        self.track = track

        # Configured name
        self.config_name = name

        # Configured picture
        self.config_picture: str | None
        if gravatar is not None:
            self.config_picture = get_gravatar_for_email(gravatar)
        else:
            self.config_picture = picture

        self._icon = icon

        self.source_type: str | None = None

        self._attributes: dict[str, Any] = {}

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self.config_name or self.host_name or self.dev_id or DEVICE_DEFAULT_NAME

    @property
    def state(self) -> str:
        """Return the state of the device."""
        return self._state

    @property
    def entity_picture(self) -> str | None:
        """Return the picture of the device."""
        return self.config_picture

    @final
    @property
    def state_attributes(self) -> dict[str, StateType]:
        """Return the device state attributes."""
        attributes: dict[str, StateType] = {ATTR_SOURCE_TYPE: self.source_type}

        if self.gps is not None:
            attributes[ATTR_LATITUDE] = self.gps[0]
            attributes[ATTR_LONGITUDE] = self.gps[1]
            attributes[ATTR_GPS_ACCURACY] = self.gps_accuracy

        if self.battery is not None:
            attributes[ATTR_BATTERY] = self.battery

        return attributes

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return device state attributes."""
        return self._attributes

    @property
    def icon(self) -> str | None:
        """Return device icon."""
        return self._icon

    async def async_seen(
        self,
        host_name: str | None = None,
        location_name: str | None = None,
        gps: GPSType | None = None,
        gps_accuracy: int | None = None,
        battery: int | None = None,
        attributes: dict[str, Any] | None = None,
        source_type: str = SOURCE_TYPE_GPS,
        consider_home: timedelta | None = None,
    ) -> None:
        """Mark the device as seen."""
        self.source_type = source_type
        self.last_seen = dt_util.utcnow()
        self.host_name = host_name or self.host_name
        self.location_name = location_name
        self.consider_home = consider_home or self.consider_home

        if battery is not None:
            self.battery = battery
        if attributes is not None:
            self._attributes.update(attributes)

        self.gps = None

        if gps is not None:
            try:
                self.gps = float(gps[0]), float(gps[1])
                self.gps_accuracy = gps_accuracy or 0
            except (ValueError, TypeError, IndexError):
                self.gps = None
                self.gps_accuracy = 0
                LOGGER.warning("Could not parse gps value for %s: %s", self.dev_id, gps)

        await self.async_update()

    def stale(self, now: dt_util.dt.datetime | None = None) -> bool:
        """Return if device state is stale.

        Async friendly.
        """
        return (
            self.last_seen is None
            or (now or dt_util.utcnow()) - self.last_seen > self.consider_home
        )

    def mark_stale(self) -> None:
        """Mark the device state as stale."""
        self._state = STATE_NOT_HOME
        self.gps = None
        self.last_update_home = False

    async def async_update(self) -> None:
        """Update state of entity.

        This method is a coroutine.
        """
        if not self.last_seen:
            return
        if self.location_name:
            self._state = self.location_name
        elif self.gps is not None and self.source_type == SOURCE_TYPE_GPS:
            zone_state = zone.async_active_zone(
                self.opp, self.gps[0], self.gps[1], self.gps_accuracy
            )
            if zone_state is None:
                self._state = STATE_NOT_HOME
            elif zone_state.entity_id == zone.ENTITY_ID_HOME:
                self._state = STATE_HOME
            else:
                self._state = zone_state.name
        elif self.stale():
            self.mark_stale()
        else:
            self._state = STATE_HOME
            self.last_update_home = True

    async def async_added_to_opp(self) -> None:
        """Add an entity."""
        await super().async_added_to_opp()
        state = await self.async_get_last_state()
        if not state:
            return
        self._state = state.state
        self.last_update_home = state.state == STATE_HOME
        self.last_seen = dt_util.utcnow()

        for attribute, var in (
            (ATTR_SOURCE_TYPE, "source_type"),
            (ATTR_GPS_ACCURACY, "gps_accuracy"),
            (ATTR_BATTERY, "battery"),
        ):
            if attribute in state.attributes:
                setattr(self, var, state.attributes[attribute])

        if ATTR_LONGITUDE in state.attributes:
            self.gps = (
                state.attributes[ATTR_LATITUDE],
                state.attributes[ATTR_LONGITUDE],
            )


class DeviceScanner:
    """Device scanner object."""

    opp: OpenPeerPower | None = None

    def scan_devices(self) -> list[str]:
        """Scan for devices."""
        raise NotImplementedError()

    async def async_scan_devices(self) -> list[str]:
        """Scan for devices."""
        assert self.opp is not None, "opp should be set by async_setup_scanner_platform"
        return await self.opp.async_add_executor_job(self.scan_devices)

    def get_device_name(self, device: str) -> str | None:
        """Get the name of a device."""
        raise NotImplementedError()

    async def async_get_device_name(self, device: str) -> str | None:
        """Get the name of a device."""
        assert self.opp is not None, "opp should be set by async_setup_scanner_platform"
        return await self.opp.async_add_executor_job(self.get_device_name, device)

    def get_extra_attributes(self, device: str) -> dict:
        """Get the extra attributes of a device."""
        raise NotImplementedError()

    async def async_get_extra_attributes(self, device: str) -> dict:
        """Get the extra attributes of a device."""
        assert self.opp is not None, "opp should be set by async_setup_scanner_platform"
        return await self.opp.async_add_executor_job(self.get_extra_attributes, device)


async def async_load_config(
    path: str, opp: OpenPeerPower, consider_home: timedelta
) -> list[Device]:
    """Load devices from YAML configuration file.

    This method is a coroutine.
    """
    dev_schema = vol.Schema(
        {
            vol.Required(CONF_NAME): cv.string,
            vol.Optional(CONF_ICON, default=None): vol.Any(None, cv.icon),
            vol.Optional("track", default=False): cv.boolean,
            vol.Optional(CONF_MAC, default=None): vol.Any(
                None, vol.All(cv.string, vol.Upper)
            ),
            vol.Optional("gravatar", default=None): vol.Any(None, cv.string),
            vol.Optional("picture", default=None): vol.Any(None, cv.string),
            vol.Optional(CONF_CONSIDER_HOME, default=consider_home): vol.All(
                cv.time_period, cv.positive_timedelta
            ),
        }
    )
    result: list[Device] = []
    try:
        devices = await opp.async_add_executor_job(load_yaml_config_file, path)
    except OpenPeerPowerError as err:
        LOGGER.error("Unable to load %s: %s", path, str(err))
        return []
    except FileNotFoundError:
        return []

    for dev_id, device in devices.items():
        # Deprecated option. We just ignore it to avoid breaking change
        device.pop("vendor", None)
        device.pop("hide_if_away", None)
        try:
            device = dev_schema(device)
            device["dev_id"] = cv.slugify(dev_id)
        except vol.Invalid as exp:
            async_log_exception(exp, dev_id, devices, opp)
        else:
            result.append(Device(opp, **device))
    return result


def update_config(path: str, dev_id: str, device: Device) -> None:
    """Add device to YAML configuration file."""
    with open(path, "a") as out:
        device_config = {
            device.dev_id: {
                ATTR_NAME: device.name,
                ATTR_MAC: device.mac,
                ATTR_ICON: device.icon,
                "picture": device.config_picture,
                "track": device.track,
            }
        }
        out.write("\n")
        out.write(dump(device_config))


def get_gravatar_for_email(email: str) -> str:
    """Return an 80px Gravatar for the given email address.

    Async friendly.
    """

    return (
        f"https://www.gravatar.com/avatar/"
        f"{hashlib.md5(email.encode('utf-8').lower()).hexdigest()}.jpg?s=80&d=wavatar"
    )
