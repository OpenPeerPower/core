"""The Bosch Smart Home Controller integration."""
import logging

from boschshcpy import SHCSession
from boschshcpy.exceptions import SHCAuthenticationError, SHCConnectionError

from openpeerpower.components.zeroconf import async_get_instance
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST, EVENT_OPENPEERPOWER_STOP
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from openpeerpower.helpers import device_registry as dr

from .const import (
    CONF_SSL_CERTIFICATE,
    CONF_SSL_KEY,
    DATA_POLLING_HANDLER,
    DATA_SESSION,
    DOMAIN,
)

PLATFORMS = ["binary_sensor", "sensor"]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up Bosch SHC from a config entry."""
    data = entry.data

    zeroconf = await async_get_instance(opp)
    try:
        session = await opp.async_add_executor_job(
            SHCSession,
            data[CONF_HOST],
            data[CONF_SSL_CERTIFICATE],
            data[CONF_SSL_KEY],
            False,
            zeroconf,
        )
    except SHCAuthenticationError as err:
        raise ConfigEntryAuthFailed from err
    except SHCConnectionError as err:
        raise ConfigEntryNotReady from err

    shc_info = session.information
    if shc_info.updateState.name == "UPDATE_AVAILABLE":
        _LOGGER.warning("Please check for software updates in the Bosch Smart Home App")

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = {
        DATA_SESSION: session,
    }

    device_registry = dr.async_get(opp)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, dr.format_mac(shc_info.unique_id))},
        identifiers={(DOMAIN, shc_info.unique_id)},
        manufacturer="Bosch",
        name=entry.title,
        model="SmartHomeController",
        sw_version=shc_info.version,
    )

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    async def stop_polling(event):
        """Stop polling service."""
        await opp.async_add_executor_job(session.stop_polling)

    await opp.async_add_executor_job(session.start_polling)
    opp.data[DOMAIN][entry.entry_id][
        DATA_POLLING_HANDLER
    ] = opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, stop_polling)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    session: SHCSession = opp.data[DOMAIN][entry.entry_id][DATA_SESSION]

    opp.data[DOMAIN][entry.entry_id][DATA_POLLING_HANDLER]()
    opp.data[DOMAIN][entry.entry_id].pop(DATA_POLLING_HANDLER)
    await opp.async_add_executor_job(session.stop_polling)

    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
