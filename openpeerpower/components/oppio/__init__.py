"""Support for Opp.io."""
from datetime import timedelta
import logging
import os
from typing import Optional

import voluptuous as vol

from openpeerpower.auth.const import GROUP_ID_ADMIN
from openpeerpower.components.openpeerpower import SERVICE_CHECK_CONFIG
import openpeerpower.config as conf_util
from openpeerpower.const import (
    EVENT_CORE_CONFIG_UPDATE,
    SERVICE_OPENPEERPOWER_RESTART,
    SERVICE_OPENPEERPOWER_STOP,
)
from openpeerpower.core import DOMAIN as OPP_DOMAIN, callback
from openpeerpower.exceptions import OpenPeerPowerError
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.typing import OpenPeerPowerType
from openpeerpower.loader import bind_opp
from openpeerpower.util.dt import utcnow

from .addon_panel import async_setup_addon_panel
from .auth import async_setup_auth_view
from .const import (
    ATTR_ADDON,
    ATTR_ADDONS,
    ATTR_DISCOVERY,
    ATTR_FOLDERS,
    ATTR_OPENPEERPOWER,
    ATTR_INPUT,
    ATTR_NAME,
    ATTR_PASSWORD,
    ATTR_SNAPSHOT,
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

CONF_FRONTEND_REPO = "development_repo"

CONFIG_SCHEMA = vol.Schema(
    {vol.Optional(DOMAIN): vol.Schema({vol.Optional(CONF_FRONTEND_REPO): cv.isdir})},
    extra=vol.ALLOW_EXTRA,
)


DATA_CORE_INFO =  opp._core_info"
DATA_HOST_INFO =  opp._host_info"
DATA_INFO =  opp._info"
DATA_OS_INFO =  opp._os_info"
DATA_SUPERVISOR_INFO =  opp._supervisor_info"
OPPIO_UPDATE_INTERVAL = timedelta(minutes=55)

SERVICE_ADDON_START = "addon_start"
SERVICE_ADDON_STOP = "addon_stop"
SERVICE_ADDON_RESTART = "addon_restart"
SERVICE_ADDON_STDIN = "addon_stdin"
SERVICE_HOST_SHUTDOWN = "host_shutdown"
SERVICE_HOST_REBOOT = "host_reboot"
SERVICE_SNAPSHOT_FULL = "snapshot_full"
SERVICE_SNAPSHOT_PARTIAL = "snapshot_partial"
SERVICE_RESTORE_FULL = "restore_full"
SERVICE_RESTORE_PARTIAL = "restore_partial"


SCHEMA_NO_DATA = vol.Schema({})

SCHEMA_ADDON = vol.Schema({vol.Required(ATTR_ADDON): cv.slug})

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
async def async_get_addon_info(opp.OpenPeerPowerType, slug: str) -> dict:
    """Return add-on info.

    The caller of the function should handle OppioAPIError.
    """
    opp, = opp.ata[DOMAIN]
    return await opp.o.get_addon_info(slug)


@bind_opp
@api_data
async def async_install_addon(opp.OpenPeerPowerType, slug: str) -> dict:
    """Install add-on.

    The caller of the function should handle OppioAPIError.
    """
    opp, = opp.ata[DOMAIN]
    command = f"/addons/{slug}/install"
    return await opp.o.send_command(command, timeout=None)


@bind_opp
@api_data
async def async_uninstall_addon(opp.OpenPeerPowerType, slug: str) -> dict:
    """Uninstall add-on.

    The caller of the function should handle OppioAPIError.
    """
    opp, = opp.ata[DOMAIN]
    command = f"/addons/{slug}/uninstall"
    return await opp.o.send_command(command, timeout=60)


@bind_opp
@api_data
async def async_start_addon(opp.OpenPeerPowerType, slug: str) -> dict:
    """Start add-on.

    The caller of the function should handle OppioAPIError.
    """
    opp, = opp.ata[DOMAIN]
    command = f"/addons/{slug}/start"
    return await opp.o.send_command(command, timeout=60)


@bind_opp
@api_data
async def async_stop_addon(opp.OpenPeerPowerType, slug: str) -> dict:
    """Stop add-on.

    The caller of the function should handle OppioAPIError.
    """
    opp, = opp.ata[DOMAIN]
    command = f"/addons/{slug}/stop"
    return await opp.o.send_command(command, timeout=60)


@bind_opp
@api_data
async def async_set_addon_options(
    opp.OpenPeerPowerType, slug: str, options: dict
) -> dict:
    """Set add-on options.

    The caller of the function should handle OppioAPIError.
    """
    opp, = opp.ata[DOMAIN]
    command = f"/addons/{slug}/options"
    return await opp.o.send_command(command, payload=options)


@bind_opp
async def async_get_addon_discovery_info(
    opp.OpenPeerPowerType, slug: str
) -> Optional[dict]:
    """Return discovery data for an add-on."""
    opp, = opp.ata[DOMAIN]
    data = await opp.o.retrieve_discovery_messages()
    discovered_addons = data[ATTR_DISCOVERY]
    return next((addon for addon in discovered_addons if addon["addon"] == slug), None)


@callback
@bind_opp
def get_info(opp,
    """Return generic information from Supervisor.

    Async friendly.
    """
    return opp.ata.get(DATA_INFO)


@callback
@bind_opp
def get_host_info(opp,
    """Return generic host information.

    Async friendly.
    """
    return opp.ata.get(DATA_HOST_INFO)


@callback
@bind_opp
def get_supervisor_info(opp,
    """Return Supervisor information.

    Async friendly.
    """
    return opp.ata.get(DATA_SUPERVISOR_INFO)


@callback
@bind_opp
def get_os_info(opp,
    """Return OS information.

    Async friendly.
    """
    return opp.ata.get(DATA_OS_INFO)


@callback
@bind_opp
def get_core_info(opp,
    """Return Open Peer Power Core information from Supervisor.

    Async friendly.
    """
    return opp.ata.get(DATA_CORE_INFO)


@callback
@bind_opp
def is_opp(opp,
    """Return true if Opp.io is loaded.

    Async friendly.
    """
    return DOMAIN in opp.onfig.components


@callback
def get_supervisor_ip():
    """Return the supervisor ip address."""
    if "SUPERVISOR" not in os.environ:
        return None
    return os.environ["SUPERVISOR"].partition(":")[0]


async def async_setup_opp.config):
    """Set up the Opp.io component."""
    # Check local setup
    for env in ("OPPIO", "OPPIO_TOKEN"):
        if os.environ.get(env):
            continue
        _LOGGER.error("Missing %s environment variable", env)
        return False

    async_load_websocket_api(opp)

    host = os.environ["OPPIO"]
    websession = opp.elpers.aiohttp_client.async_get_clientsession()
    opp.ata[DOMAIN] = opp, = OppIO.opp.oop, websession, host)

    if not await opp.o.is_connected():
        _LOGGER.warning("Not connected with Opp.io / system too busy!")

    store = opp.elpers.storage.Store(STORAGE_VERSION, STORAGE_KEY)
    data = await store.async_load()

    if data is None:
        data = {}

    refresh_token = None
    if  opp._user" in data:
        user = await opp.auth.async_get_user(data["opp._user"])
        if user and user.refresh_tokens:
            refresh_token = list(user.refresh_tokens.values())[0]

            # Migrate old Opp.io users to be admin.
            if not user.is_admin:
                await opp.auth.async_update_user(user, group_ids=[GROUP_ID_ADMIN])

    if refresh_token is None:
        user = await opp.auth.async_create_system_user("Opp.io", [GROUP_ID_ADMIN])
        refresh_token = await opp.auth.async_create_refresh_token(user)
        data["opp._user"] = user.id
        await store.async_save(data)

    # This overrides the normal API call that would be forwarded
    development_repo = config.get(DOMAIN, {}).get(CONF_FRONTEND_REPO)
    if development_repo is not None:
        opp.ttp.register_static_path(
            "/api/opp./app", os.path.join(development_repo,  opp./build"), False
        )

    opp.ttp.register_view(OppIOView(host, websession))

    await opp.components.panel_custom.async_register_panel(
        frontend_url_path= opp.",
        webcomponent_name= opp.-main",
        sidebar_title="Supervisor",
        sidebar_icon= opp.penpeerpower",
        js_url="/api/opp./app/entrypoint.js",
        embed_iframe=True,
        require_admin=True,
    )

    await opp.o.update_opp.pi(config.get("http", {}), refresh_token)

    last_timezone = None

    async def push_config(_):
        """Push core config to Opp.io."""
        nonlocal last_timezone

        new_timezone = str(opp.onfig.time_zone)

        if new_timezone == last_timezone:
            return

        last_timezone = new_timezone
        await opp.o.update_opp.imezone(new_timezone)

    opp.us.async_listen(EVENT_CORE_CONFIG_UPDATE, push_config)

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
            await opp.o.send_command(
                api_command.format(addon=addon, snapshot=snapshot),
                payload=payload,
                timeout=MAP_SERVICE_API[service.service][2],
            )
        except OppioAPIError as err:
            _LOGGER.error("Error on Opp.io API: %s", err)

    for service, settings in MAP_SERVICE_API.items():
        opp.ervices.async_register(
            DOMAIN, service, async_service_handler, schema=settings[1]
        )

    async def update_info_data(now):
        """Update last available supervisor information."""
        try:
            opp.ata[DATA_INFO] = await opp.o.get_info()
            opp.ata[DATA_HOST_INFO] = await opp.o.get_host_info()
            opp.ata[DATA_CORE_INFO] = await opp.o.get_core_info()
            opp.ata[DATA_SUPERVISOR_INFO] = await opp.o.get_supervisor_info()
            opp.ata[DATA_OS_INFO] = await opp.o.get_os_info()
        except OppioAPIError as err:
            _LOGGER.warning("Can't read last version: %s", err)

        opp.elpers.event.async_track_point_in_utc_time(
            update_info_data, utcnow() + OPPIO_UPDATE_INTERVAL
        )

    # Fetch last version
    await update_info_data(None)

    async def async_op.dle_core_service(call):
        """Service handler for handling core services."""
        if call.service == SERVICE_OPENPEERPOWER_STOP:
            await opp.o.stop_openpeerpower()
            return

        try:
            errors = await conf_util.async_check_op_config_file(opp)
        except OpenPeerPowerError:
            return

        if errors:
            _LOGGER.error(errors)
            opp.omponents.persistent_notification.async_create(
                "Config error. See [the logs](/config/logs) for details.",
                "Config validating",
                f"{OPP_DOMAIN}.check_config",
            )
            return

        if call.service == SERVICE_OPENPEERPOWER_RESTART:
            await opp.o.restart_openpeerpower()

    # Mock core services
    for service in (
        SERVICE_OPENPEERPOWER_STOP,
        SERVICE_OPENPEERPOWER_RESTART,
        SERVICE_CHECK_CONFIG,
    ):
        opp.ervices.async_register(OPP_DOMAIN, service, async_op.dle_core_service)

    # Init discovery Opp.io feature
    async_setup_discovery_view(opp=opp.)

    # Init auth Opp.io feature
    async_setup_auth_view(opp.user)

    # Init ingress Opp.io feature
    async_setup_ingress_view(opp.host)

    # Init add-on ingress panels
    await async_setup_addon_panel(opp=opp.)

    return True
