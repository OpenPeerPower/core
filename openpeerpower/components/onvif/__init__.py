"""The ONVIF integration."""
import asyncio

from onvif.exceptions import ONVIFAuthError, ONVIFError, ONVIFTimeoutError

from openpeerpower.components.ffmpeg import CONF_EXTRA_ARGUMENTS
from openpeerpower.config_entries import SOURCE_IMPORT, ConfigEntry
from openpeerpower.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    EVENT_OPENPEERPOWER_STOP,
    HTTP_BASIC_AUTHENTICATION,
    HTTP_DIGEST_AUTHENTICATION,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import config_per_platform

from .const import (
    CONF_RTSP_TRANSPORT,
    CONF_SNAPSHOT_AUTH,
    DEFAULT_ARGUMENTS,
    DEFAULT_NAME,
    DEFAULT_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_USERNAME,
    DOMAIN,
    RTSP_TRANS_PROTOCOLS,
)
from .device import ONVIFDevice


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the ONVIF component."""
    # Import from yaml
    configs = {}
    for p_type, p_config in config_per_platform(config, "camera"):
        if p_type != DOMAIN:
            continue

        config = p_config.copy()
        if config[CONF_HOST] not in configs:
            configs[config[CONF_HOST]] = {
                CONF_HOST: config[CONF_HOST],
                CONF_NAME: config.get(CONF_NAME, DEFAULT_NAME),
                CONF_PASSWORD: config.get(CONF_PASSWORD, DEFAULT_PASSWORD),
                CONF_PORT: config.get(CONF_PORT, DEFAULT_PORT),
                CONF_USERNAME: config.get(CONF_USERNAME, DEFAULT_USERNAME),
            }

    for conf in configs.values():
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=conf
            )
        )

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up ONVIF from a config entry."""
    if DOMAIN not in opp.data:
        opp.data[DOMAIN] = {}

    if not entry.options:
        await async_populate_options(opp, entry)

    device = ONVIFDevice(opp, entry)

    if not await device.async_setup():
        await device.device.close()
        return False

    if not device.available:
        raise ConfigEntryNotReady()

    if not entry.data.get(CONF_SNAPSHOT_AUTH):
        await async_populate_snapshot_auth(opp, device, entry)

    opp.data[DOMAIN][entry.unique_id] = device

    platforms = ["camera"]

    if device.capabilities.events:
        platforms += ["binary_sensor", "sensor"]

    for platform in platforms:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, device.async_stop)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""

    device = opp.data[DOMAIN][entry.unique_id]
    platforms = ["camera"]

    if device.capabilities.events and device.events.started:
        platforms += ["binary_sensor", "sensor"]
        await device.events.async_stop()

    return all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in platforms
            ]
        )
    )


async def _get_snapshot_auth(device):
    """Determine auth type for snapshots."""
    if not device.capabilities.snapshot or not (device.username and device.password):
        return HTTP_DIGEST_AUTHENTICATION

    try:
        snapshot = await device.device.get_snapshot(device.profiles[0].token)

        if snapshot:
            return HTTP_DIGEST_AUTHENTICATION
        return HTTP_BASIC_AUTHENTICATION
    except (ONVIFAuthError, ONVIFTimeoutError):
        return HTTP_BASIC_AUTHENTICATION
    except ONVIFError:
        return HTTP_DIGEST_AUTHENTICATION


async def async_populate_snapshot_auth(opp, device, entry):
    """Check if digest auth for snapshots is possible."""
    auth = await _get_snapshot_auth(device)
    new_data = {**entry.data, CONF_SNAPSHOT_AUTH: auth}
    opp.config_entries.async_update_entry(entry, data=new_data)


async def async_populate_options(opp, entry):
    """Populate default options for device."""
    options = {
        CONF_EXTRA_ARGUMENTS: DEFAULT_ARGUMENTS,
        CONF_RTSP_TRANSPORT: RTSP_TRANS_PROTOCOLS[0],
    }

    opp.config_entries.async_update_entry(entry, options=options)
