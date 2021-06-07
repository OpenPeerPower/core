"""The foscam component."""

from libpyfoscam import FoscamCamera

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers.entity_registry import async_migrate_entries

from .config_flow import DEFAULT_RTSP_PORT
from .const import CONF_RTSP_PORT, DOMAIN, LOGGER, SERVICE_PTZ, SERVICE_PTZ_PRESET

PLATFORMS = ["camera"]


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up foscam from a config entry."""
    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = entry.data

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

        if not opp.data[DOMAIN]:
            opp.services.async_remove(domain=DOMAIN, service=SERVICE_PTZ)
            opp.services.async_remove(domain=DOMAIN, service=SERVICE_PTZ_PRESET)

    return unload_ok


async def async_migrate_entry(opp, entry: ConfigEntry):
    """Migrate old entry."""
    LOGGER.debug("Migrating from version %s", entry.version)

    if entry.version == 1:
        # Change unique id
        @callback
        def update_unique_id(entry):
            return {"new_unique_id": entry.entry_id}

        await async_migrate_entries(opp, entry.entry_id, update_unique_id)

        entry.unique_id = None

        # Get RTSP port from the camera or use the fallback one and store it in data
        camera = FoscamCamera(
            entry.data[CONF_HOST],
            entry.data[CONF_PORT],
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
            verbose=False,
        )

        ret, response = await opp.async_add_executor_job(camera.get_port_info)

        rtsp_port = DEFAULT_RTSP_PORT

        if ret != 0:
            rtsp_port = response.get("rtspPort") or response.get("mediaPort")

        entry.data = {**entry.data, CONF_RTSP_PORT: rtsp_port}

        # Change entry version
        entry.version = 2

    LOGGER.info("Migration to version %s successful", entry.version)

    return True
