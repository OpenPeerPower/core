"""Support for Opp.io."""
import asyncio
from datetime import timedelta
import logging
import os
from typing import Any, Dict, List, Optional

import voluptuous as vol

from openpeerpower.auth.const import GROUP_ID_ADMIN
from openpeerpower.components.openpeerpower import SERVICE_CHECK_CONFIG
import openpeerpower.config as conf_util
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import (
    ATTR_NAME,
    ATTR_SERVICE,
    EVENT_CORE_CONFIG_UPDATE,
    SERVICE_OPENPEERPOWER_RESTART,
    SERVICE_OPENPEERPOWER_STOP,
)
from openpeerpower.core import DOMAIN as OPP_DOMAIN, Config, OpenPeerPower, callback
from openpeerpower.exceptions import OpenPeerPowerError
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.device_registry import DeviceRegistry, async_get_registry
from openpeerpower.helpers.typing import OpenPeerPowerType
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator
from openpeerpower.loader import bind_opp
from openpeerpower.util.dt import utcnow

from .addon_panel import async_setup_addon_panel
from .auth import async_setup_auth_view
from .const import (
    ATTR_ADDON,
    ATTR_ADDONS,
    ATTR_DISCOVERY,
    ATTR_FOLDERS,
    ATTR_INPUT,
    ATTR_OPENPEERPOWER,
    ATTR_PASSWORD,
    ATTR_REPOSITORY,
    ATTR_SLUG,
    ATTR_SNAPSHOT,
    ATTR_URL,
    ATTR_VERSION,
    DOMAIN,
)
from .discovery import async_setup_discovery_view
from .handler import OppIO, OppioAPIError, api_data
from .http import OppIOView
from .ingress import async_setup_ingress_view
from .websocket_api import async_load_websocket_api

_LOGGER = logging.getLogger(__name__)


STORAGE_KEY = DOMAIN
STORAGE_VERSION = 1
PLATFORMS = ["binary_sensor", "sensor"]

CONF_FRONTEND_REPO = "development_repo"

CONFIG_SCHEMA = vol.Schema(
    {vol.Optional(DOMAIN): vol.Schema({vol.Optional(CONF_FRONTEND_REPO): cv.isdir})},
    extra=vol.ALLOW_EXTRA,
)


DATA_CORE_INFO = "oppio_core_info"
DATA_HOST_INFO = "oppio_host_info"
DATA_INFO = "oppio_info"
DATA_OS_INFO = "oppio_os_info"
DATA_SUPERVISOR_INFO = "oppio_supervisor_info"
OPPIO_UPDATE_INTERVAL = timedelta(minutes=55)

ADDONS_COORDINATOR = "oppio_addons_coordinator"

SERVICE_ADDON_START = "addon_start"
SERVICE_ADDON_STOP = "addon_stop"
SERVICE_ADDON_RESTART = "addon_restart"
SERVICE_ADDON_UPDATE = "addon_update"
SERVICE_ADDON_STDIN = "addon_stdin"
SERVICE_HOST_SHUTDOWN = "host_shutdown"
SERVICE_HOST_REBOOT = "host_reboot"
SERVICE_SNAPSHOT_FULL = "snapshot_full"
SERVICE_SNAPSHOT_PARTIAL = "snapshot_partial"
SERVICE_RESTORE_FULL = "restore_full"
SERVICE_RESTORE_PARTIAL = "restore_partial"


SCHEMA_NO_DATA = vol.Schema({})

SCHEMA_ADDON = vol.Schema({vol.Required(ATTR_ADDON): cv.string})

SCHEMA_ADDON_STDIN = SCHEMA_ADDON.extend(
    {vol.Required(ATTR_INPUT): vol.Any(dict, cv.string)}
)

SCHEMA_SNAPSHOT_FULL = vol.Schema(
    {vol.Optional(ATTR_NAME): cv.string, vol.Optional(ATTR_PASSWORD): cv.string}
)

SCHEMA_SNAPSHOT_PARTIAL = SCHEMA_SNAPSHOT_FULL.extend(
    {
        vol.Optional(ATTR_FOLDERS): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(ATTR_ADDONS): vol.All(cv.ensure_list, [cv.string]),
    }
)

SCHEMA_RESTORE_FULL = vol.Schema(
    {vol.Required(ATTR_SNAPSHOT): cv.slug, vol.Optional(ATTR_PASSWORD): cv.string}
)

SCHEMA_RESTORE_PARTIAL = SCHEMA_RESTORE_FULL.extend(
    {
        vol.Optional(ATTR_OPENPEERPOWER): cv.boolean,
        vol.Optional(ATTR_FOLDERS): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(ATTR_ADDONS): vol.All(cv.ensure_list, [cv.string]),
    }
)


MAP_SERVICE_API = {
    SERVICE_ADDON_START: ("/addons/{addon}/start", SCHEMA_ADDON, 60, False),
    SERVICE_ADDON_STOP: ("/addons/{addon}/stop", SCHEMA_ADDON, 60, False),
    SERVICE_ADDON_RESTART: ("/addons/{addon}/restart", SCHEMA_ADDON, 60, False),
    SERVICE_ADDON_UPDATE: ("/addons/{addon}/update", SCHEMA_ADDON, 60, False),
    SERVICE_ADDON_STDIN: ("/addons/{addon}/stdin", SCHEMA_ADDON_STDIN, 60, False),
    SERVICE_HOST_SHUTDOWN: ("/host/shutdown", SCHEMA_NO_DATA, 60, False),
    SERVICE_HOST_REBOOT: ("/host/reboot", SCHEMA_NO_DATA, 60, False),
    SERVICE_SNAPSHOT_FULL: ("/snapshots/new/full", SCHEMA_SNAPSHOT_FULL, 300, True),
    SERVICE_SNAPSHOT_PARTIAL: (
        "/snapshots/new/partial",
        SCHEMA_SNAPSHOT_PARTIAL,
        300,
        True,
    ),
    SERVICE_RESTORE_FULL: (
        "/snapshots/{snapshot}/restore/full",
        SCHEMA_RESTORE_FULL,
        300,
        True,
    ),
    SERVICE_RESTORE_PARTIAL: (
        "/snapshots/{snapshot}/restore/partial",
        SCHEMA_RESTORE_PARTIAL,
        300,
        True,
    ),
}


@bind_opp
async def async_get_addon_info(opp: OpenPeerPowerType, slug: str) -> dict:
    """Return add-on info.

    The caller of the function should handle OppioAPIError.
    """
    oppio = opp.data[DOMAIN]
    return await oppio.get_addon_info(slug)


@bind_opp
@api_data
async def async_install_addon(opp: OpenPeerPowerType, slug: str) -> dict:
    """Install add-on.

    The caller of the function should handle OppioAPIError.
    """
    oppio = opp.data[DOMAIN]
    command = f"/addons/{slug}/install"
    return await oppio.send_command(command, timeout=None)


@bind_opp
@api_data
async def async_uninstall_addon(opp: OpenPeerPowerType, slug: str) -> dict:
    """Uninstall add-on.

    The caller of the function should handle OppioAPIError.
    """
    oppio = opp.data[DOMAIN]
    command = f"/addons/{slug}/uninstall"
    return await oppio.send_command(command, timeout=60)


@bind_opp
@api_data
async def async_update_addon(opp: OpenPeerPowerType, slug: str) -> dict:
    """Update add-on.

    The caller of the function should handle OppioAPIError.
    """
    oppio = opp.data[DOMAIN]
    command = f"/addons/{slug}/update"
    return await oppio.send_command(command, timeout=None)


@bind_opp
@api_data
async def async_start_addon(opp: OpenPeerPowerType, slug: str) -> dict:
    """Start add-on.

    The caller of the function should handle OppioAPIError.
    """
    oppio = opp.data[DOMAIN]
    command = f"/addons/{slug}/start"
    return await oppio.send_command(command, timeout=60)


@bind_opp
@api_data
async def async_stop_addon(opp: OpenPeerPowerType, slug: str) -> dict:
    """Stop add-on.

    The caller of the function should handle OppioAPIError.
    """
    oppio = opp.data[DOMAIN]
    command = f"/addons/{slug}/stop"
    return await oppio.send_command(command, timeout=60)


@bind_opp
@api_data
async def async_set_addon_options(
    opp: OpenPeerPowerType, slug: str, options: dict
) -> dict:
    """Set add-on options.

    The caller of the function should handle OppioAPIError.
    """
    oppio = opp.data[DOMAIN]
    command = f"/addons/{slug}/options"
    return await oppio.send_command(command, payload=options)


@bind_opp
async def async_get_addon_discovery_info(
    opp: OpenPeerPowerType, slug: str
) -> Optional[dict]:
    """Return discovery data for an add-on."""
    oppio = opp.data[DOMAIN]
    data = await oppio.retrieve_discovery_messages()
    discovered_addons = data[ATTR_DISCOVERY]
    return next((addon for addon in discovered_addons if addon["addon"] == slug), None)


@bind_opp
@api_data
async def async_create_snapshot(
    opp: OpenPeerPowerType, payload: dict, partial: bool = False
) -> dict:
    """Create a full or partial snapshot.

    The caller of the function should handle OppioAPIError.
    """
    oppio = opp.data[DOMAIN]
    snapshot_type = "partial" if partial else "full"
    command = f"/snapshots/new/{snapshot_type}"
    return await oppio.send_command(command, payload=payload, timeout=None)


@callback
@bind_opp
def get_info(opp):
    """Return generic information from Supervisor.

    Async friendly.
    """
    return opp.data.get(DATA_INFO)


@callback
@bind_opp
def get_host_info(opp):
    """Return generic host information.

    Async friendly.
    """
    return opp.data.get(DATA_HOST_INFO)


@callback
@bind_opp
def get_supervisor_info(opp):
    """Return Supervisor information.

    Async friendly.
    """
    return opp.data.get(DATA_SUPERVISOR_INFO)


@callback
@bind_opp
def get_os_info(opp):
    """Return OS information.

    Async friendly.
    """
    return opp.data.get(DATA_OS_INFO)


@callback
@bind_opp
def get_core_info(opp):
    """Return Open Peer Power Core information from Supervisor.

    Async friendly.
    """
    return opp.data.get(DATA_CORE_INFO)


@callback
@bind_opp
def is_oppio(opp):
    """Return true if Opp.io is loaded.

    Async friendly.
    """
    return DOMAIN in opp.config.components


@callback
def get_supervisor_ip():
    """Return the supervisor ip address."""
    if "SUPERVISOR" not in os.environ:
        return None
    return os.environ["SUPERVISOR"].partition(":")[0]


async def async_setup(opp: OpenPeerPower, config: Config) -> bool:
    """Set up the Opp.io component."""
    # Check local setup
    for env in ("OPPIO", "OPPIO_TOKEN"):
        if os.environ.get(env):
            continue
        _LOGGER.error("Missing %s environment variable", env)
        if config_entries := opp.config_entries.async_entries(DOMAIN):
            opp.async_create_task(
                opp.config_entries.async_remove(config_entries[0].entry_id)
            )
        return False

    async_load_websocket_api(opp)

    host = os.environ["OPPIO"]
    websession = opp.helpers.aiohttp_client.async_get_clientsession()
    opp.data[DOMAIN] = oppio = OppIO(opp.loop, websession, host)

    if not await oppio.is_connected():
        _LOGGER.warning("Not connected with Opp.io / system too busy!")

    store = opp.helpers.storage.Store(STORAGE_VERSION, STORAGE_KEY)
    data = await store.async_load()

    if data is None:
        data = {}

    refresh_token = None
    if "oppio_user" in data:
        user = await opp.auth.async_get_user(data["oppio_user"])
        if user and user.refresh_tokens:
            refresh_token = list(user.refresh_tokens.values())[0]

            # Migrate old Opp.io users to be admin.
            if not user.is_admin:
                await opp.auth.async_update_user(user, group_ids=[GROUP_ID_ADMIN])

    if refresh_token is None:
        user = await opp.auth.async_create_system_user("Opp.io", [GROUP_ID_ADMIN])
        refresh_token = await opp.auth.async_create_refresh_token(user)
        data["oppio_user"] = user.id
        await store.async_save(data)

    # This overrides the normal API call that would be forwarded
    development_repo = config.get(DOMAIN, {}).get(CONF_FRONTEND_REPO)
    if development_repo is not None:
        opp.http.register_static_path(
            "/api/oppio/app", os.path.join(development_repo, "oppio/build"), False
        )

    opp.http.register_view(OppIOView(host, websession))

    await opp.components.panel_custom.async_register_panel(
        frontend_url_path="oppio",
        webcomponent_name="oppio-main",
        sidebar_title="Supervisor",
        sidebar_icon="opp:open-peer-power",
        js_url="/api/oppio/app/entrypoint.js",
        embed_iframe=True,
        require_admin=True,
    )

    await oppio.update_opp_api(config.get("http", {}), refresh_token)

    last_timezone = None

    async def push_config(_):
        """Push core config to Opp.io."""
        nonlocal last_timezone

        new_timezone = str(opp.config.time_zone)

        if new_timezone == last_timezone:
            return

        last_timezone = new_timezone
        await oppio.update_opp_timezone(new_timezone)

    opp.bus.async_listen(EVENT_CORE_CONFIG_UPDATE, push_config)

    await push_config(None)

    async def async_service_handler(service):
        """Handle service calls for Opp.io."""
        api_command = MAP_SERVICE_API[service.service][0]
        data = service.data.copy()
        addon = data.pop(ATTR_ADDON, None)
        snapshot = data.pop(ATTR_SNAPSHOT, None)
        payload = None

        # Pass data to Opp.io API
        if service.service == SERVICE_ADDON_STDIN:
            payload = data[ATTR_INPUT]
        elif MAP_SERVICE_API[service.service][3]:
            payload = data

        # Call API
        try:
            await oppio.send_command(
                api_command.format(addon=addon, snapshot=snapshot),
                payload=payload,
                timeout=MAP_SERVICE_API[service.service][2],
            )
        except OppioAPIError as err:
            _LOGGER.error("Error on Opp.io API: %s", err)

    for service, settings in MAP_SERVICE_API.items():
        opp.services.async_register(
            DOMAIN, service, async_service_handler, schema=settings[1]
        )

    async def update_info_data(now):
        """Update last available supervisor information."""
        try:
            opp.data[DATA_INFO] = await oppio.get_info()
            opp.data[DATA_HOST_INFO] = await oppio.get_host_info()
            opp.data[DATA_CORE_INFO] = await oppio.get_core_info()
            opp.data[DATA_SUPERVISOR_INFO] = await oppio.get_supervisor_info()
            opp.data[DATA_OS_INFO] = await oppio.get_os_info()
            if ADDONS_COORDINATOR in opp.data:
                await opp.data[ADDONS_COORDINATOR].async_refresh()
        except OppioAPIError as err:
            _LOGGER.warning("Can't read last version: %s", err)

        opp.helpers.event.async_track_point_in_utc_time(
            update_info_data, utcnow() + OPPIO_UPDATE_INTERVAL
        )

    # Fetch last version
    await update_info_data(None)

    async def async_handle_core_service(call):
        """Service handler for handling core services."""
        if call.service == SERVICE_OPENPEERPOWER_STOP:
            await oppio.stop_openpeerpower()
            return

        try:
            errors = await conf_util.async_check_op_config_file(opp)
        except OpenPeerPowerError:
            return

        if errors:
            _LOGGER.error(errors)
            opp.components.persistent_notification.async_create(
                "Config error. See [the logs](/config/logs) for details.",
                "Config validating",
                f"{OPP_DOMAIN}.check_config",
            )
            return

        if call.service == SERVICE_OPENPEERPOWER_RESTART:
            await oppio.restart_openpeerpower()

    # Mock core services
    for service in (
        SERVICE_OPENPEERPOWER_STOP,
        SERVICE_OPENPEERPOWER_RESTART,
        SERVICE_CHECK_CONFIG,
    ):
        opp.services.async_register(OPP_DOMAIN, service, async_handle_core_service)

    # Init discovery Opp.io feature
    async_setup_discovery_view(opp, oppio)

    # Init auth Opp.io feature
    async_setup_auth_view(opp, user)

    # Init ingress Opp.io feature
    async_setup_ingress_view(opp, host)

    # Init add-on ingress panels
    await async_setup_addon_panel(opp, oppio)

    opp.async_create_task(
        opp.config_entries.flow.async_init(DOMAIN, context={"source": "system"})
    )

    return True


async def async_setup_entry(opp: OpenPeerPower, config_entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    dev_reg = await async_get_registry(opp)
    coordinator = OppioDataUpdateCoordinator(opp, config_entry, dev_reg)
    opp.data[ADDONS_COORDINATOR] = coordinator
    await coordinator.async_refresh()

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    return True


async def async_unload_entry(opp: OpenPeerPowerType, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(config_entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    # Pop add-on data
    opp.data.pop(ADDONS_COORDINATOR, None)

    return unload_ok


@callback
def async_register_addons_in_dev_reg(
    entry_id: str, dev_reg: DeviceRegistry, addons: List[Dict[str, Any]]
) -> None:
    """Register addons in the device registry."""
    for addon in addons:
        params = {
            "config_entry_id": entry_id,
            "identifiers": {(DOMAIN, addon[ATTR_SLUG])},
            "model": "Open Peer Power Add-on",
            "sw_version": addon[ATTR_VERSION],
            "name": addon[ATTR_NAME],
            "entry_type": ATTR_SERVICE,
        }
        if manufacturer := addon.get(ATTR_REPOSITORY) or addon.get(ATTR_URL):
            params["manufacturer"] = manufacturer
        dev_reg.async_get_or_create(**params)


@callback
def async_register_os_in_dev_reg(
    entry_id: str, dev_reg: DeviceRegistry, os_dict: Dict[str, Any]
) -> None:
    """Register OS in the device registry."""
    params = {
        "config_entry_id": entry_id,
        "identifiers": {(DOMAIN, "OS")},
        "manufacturer": "Open Peer Power",
        "model": "Open Peer Power Operating System",
        "sw_version": os_dict[ATTR_VERSION],
        "name": "Open Peer Power Operating System",
        "entry_type": ATTR_SERVICE,
    }
    dev_reg.async_get_or_create(**params)


@callback
def async_remove_addons_from_dev_reg(
    dev_reg: DeviceRegistry, addons: List[Dict[str, Any]]
) -> None:
    """Remove addons from the device registry."""
    for addon_slug in addons:
        if dev := dev_reg.async_get_device({(DOMAIN, addon_slug)}):
            dev_reg.async_remove_device(dev.id)


class OppioDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to retrieve Opp.io status."""

    def __init__(
        self, opp: OpenPeerPower, config_entry: ConfigEntry, dev_reg: DeviceRegistry
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            opp,
            _LOGGER,
            name=DOMAIN,
            update_method=self._async_update_data,
        )
        self.data = {}
        self.entry_id = config_entry.entry_id
        self.dev_reg = dev_reg
        self.is_opp_os = "oppos" in get_info(self.opp)

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data via library."""
        new_data = {}
        addon_data = get_supervisor_info(self.opp)

        new_data["addons"] = {
            addon[ATTR_SLUG]: addon for addon in addon_data.get("addons", [])
        }
        if self.is_opp_os:
            new_data["os"] = get_os_info(self.opp)

        # If this is the initial refresh, register all addons and return the dict
        if not self.data:
            async_register_addons_in_dev_reg(
                self.entry_id, self.dev_reg, new_data["addons"].values()
            )
            if self.is_opp_os:
                async_register_os_in_dev_reg(
                    self.entry_id, self.dev_reg, new_data["os"]
                )
            return new_data

        # Remove add-ons that are no longer installed from device registry
        if removed_addons := list(set(self.data["addons"]) - set(new_data["addons"])):
            async_remove_addons_from_dev_reg(self.dev_reg, removed_addons)

        # If there are new add-ons, we should reload the config entry so we can
        # create new devices and entities. We can return an empty dict because
        # coordinator will be recreated.
        if list(set(new_data["addons"]) - set(self.data["addons"])):
            self.opp.async_create_task(
                self.opp.config_entries.async_reload(self.entry_id)
            )
            return {}

        return new_data
