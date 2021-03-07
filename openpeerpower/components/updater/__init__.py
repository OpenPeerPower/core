"""Support to check for available updates."""
import asyncio
from datetime import timedelta
import logging

import async_timeout
from awesomeversion import AwesomeVersion
from distro import linux_distribution
import voluptuous as vol

from openpeerpower.const import __version__ as current_version
from openpeerpower.helpers import discovery, update_coordinator
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
import openpeerpower.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

ATTR_RELEASE_NOTES = "release_notes"
ATTR_NEWEST_VERSION = "newest_version"

CONF_REPORTING = "reporting"
CONF_COMPONENT_REPORTING = "include_used_components"

DOMAIN = "updater"

UPDATER_URL = "https://updater.openpeerpower.io/"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: {
            vol.Optional(CONF_REPORTING, default=True): cv.boolean,
            vol.Optional(CONF_COMPONENT_REPORTING, default=False): cv.boolean,
        }
    },
    extra=vol.ALLOW_EXTRA,
)

RESPONSE_SCHEMA = vol.Schema(
    {vol.Required("version"): cv.string, vol.Required("release-notes"): cv.url}
)


class Updater:
    """Updater class for data exchange."""

    def __init__(self, update_available: bool, newest_version: str, release_notes: str):
        """Initialize attributes."""
        self.update_available = update_available
        self.release_notes = release_notes
        self.newest_version = newest_version


async def async_setup(opp, config):
    """Set up the updater component."""
    if "dev" in current_version:
        # This component only makes sense in release versions
        _LOGGER.info("Running on 'dev', only analytics will be submitted")

    conf = config.get(DOMAIN, {})
    if conf.get(CONF_REPORTING):
        huuid = await opp.helpers.instance_id.async_get()
    else:
        huuid = None

    include_components = conf.get(CONF_COMPONENT_REPORTING)

    async def check_new_version() -> Updater:
        """Check if a new version is available and report if one is."""
        newest, release_notes = await get_newest_version(opp, huuid, include_components)

        _LOGGER.debug("Fetched version %s: %s", newest, release_notes)

        # Skip on dev
        if "dev" in current_version:
            return Updater(False, "", "")

        # Load data from Supervisor
        if opp.components.oppio.is_oppio():
            core_info = opp.components.oppio.get_core_info()
            newest = core_info["version_latest"]

        # Validate version
        update_available = False
        if AwesomeVersion(newest) > AwesomeVersion(current_version):
            _LOGGER.debug(
                "The latest available version of Open Peer Power is %s", newest
            )
            update_available = True
        elif AwesomeVersion(newest) == AwesomeVersion(current_version):
            _LOGGER.debug(
                "You are on the latest version (%s) of Open Peer Power", newest
            )
        elif AwesomeVersion(newest) < AwesomeVersion(current_version):
            _LOGGER.debug(
                "Local version (%s) is newer than the latest available version (%s)",
                current_version,
                newest,
            )

        _LOGGER.debug("Update available: %s", update_available)

        return Updater(update_available, newest, release_notes)

    coordinator = opp.data[DOMAIN] = update_coordinator.DataUpdateCoordinator[Updater](
        opp,
        _LOGGER,
        name="Open Peer Power update",
        update_method=check_new_version,
        update_interval=timedelta(days=1),
    )

    # This can take up to 15s which can delay startup
    asyncio.create_task(coordinator.async_refresh())

    opp.async_create_task(
        discovery.async_load_platform(opp, "binary_sensor", DOMAIN, {}, config)
    )

    return True


async def get_newest_version(opp, huuid, include_components):
    """Get the newest Open Peer Power version."""
    if huuid:
        info_object = await opp.helpers.system_info.async_get_system_info()

        if include_components:
            info_object["components"] = list(opp.config.components)

        linux_dist = await opp.async_add_executor_job(linux_distribution, False)
        info_object["distribution"] = linux_dist[0]
        info_object["os_version"] = linux_dist[1]

        info_object["huuid"] = huuid
    else:
        info_object = {}

    session = async_get_clientsession(opp)

    with async_timeout.timeout(30):
        req = await session.post(UPDATER_URL, json=info_object)

    _LOGGER.info(
        (
            "Submitted analytics to Open Peer Power servers. "
            "Information submitted includes %s"
        ),
        info_object,
    )

    try:
        res = await req.json()
    except ValueError as err:
        raise update_coordinator.UpdateFailed(
            "Received invalid JSON from Open Peer Power Update"
        ) from err

    try:
        res = RESPONSE_SCHEMA(res)
        return res["version"], res["release-notes"]
    except vol.Invalid as err:
        raise update_coordinator.UpdateFailed(
            f"Got unexpected response: {err}"
        ) from err
