"""The foscam component."""
import asyncio

from libpyfoscam import FoscamCamera

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers.entity_registry import async_migrate_entries

from .config_flow import DEFAULT_RTSP_PORT
from .const import CONF_RTSP_PORT, DOMAIN, LOGGER, SERVICE_PTZ, SERVICE_PTZ_PRESET

PLATFORMS = ["camera"]


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the foscam component."""
    opp.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up foscam from a config entry."""
    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    opp.data[DOMAIN][entry.entry_id] = entry.data

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

        if not opp.data[DOMAIN]:
            opp.services.async_remove(domain=DOMAIN, service=SERVICE_PTZ)
            opp.services.async_remove(domain=DOMAIN, service=SERVICE_PTZ_PRESET)

    return unload_ok


async def async_migrate_entry(opp, config_entry: ConfigEntry):
    """Migrate old entry."""
    LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        # Change unique id
        @callback
        def update_unique_id(entry):
            return {"new_unique_id": config_entry.entry_id}

        await async_migrate_entries(opp, config_entry.entry_id, update_unique_id)

        config_entry.unique_id = None

        # Get RTSP port from the camera or use the fallback one and store it in data
        camera = FoscamCamera(
            config_entry.data[CONF_HOST],
            config_entry.data[CONF_PORT],
            config_entry.data[CONF_USERNAME],
            config_entry.data[CONF_PASSWORD],
            verbose=False,
        )

        ret, response = await opp.async_add_executor_job(camera.get_port_info)

        rtsp_port = DEFAULT_RTSP_PORT

        if ret != 0:
            rtsp_port = response.get("rtspPort") or response.get("mediaPort")

        config_entry.data = {**config_entry.data, CONF_RTSP_PORT: rtsp_port}

        # Change entry version
        config_entry.version = 2

    LOGGER.info("Migration to version %s successful", config_entry.version)

    return True
