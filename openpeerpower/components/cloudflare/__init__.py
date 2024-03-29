"""Update the IP addresses of your Cloudflare DNS records."""
from __future__ import annotations

from datetime import timedelta
import logging

from pycfdns import CloudflareUpdater
from pycfdns.exceptions import (
    CloudflareAuthenticationException,
    CloudflareConnectionException,
    CloudflareException,
)

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_API_TOKEN, CONF_ZONE
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.event import async_track_time_interval

from .const import (
    CONF_RECORDS,
    DATA_UNDO_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    SERVICE_UPDATE_RECORDS,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.deprecated(DOMAIN)


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up Cloudflare from a config entry."""
    cfupdate = CloudflareUpdater(
        async_get_clientsession(opp),
        entry.data[CONF_API_TOKEN],
        entry.data[CONF_ZONE],
        entry.data[CONF_RECORDS],
    )

    try:
        zone_id = await cfupdate.get_zone_id()
    except CloudflareAuthenticationException:
        _LOGGER.error("API access forbidden. Please reauthenticate")
        return False
    except CloudflareConnectionException as error:
        raise ConfigEntryNotReady from error

    async def update_records(now):
        """Set up recurring update."""
        try:
            await _async_update_cloudflare(cfupdate, zone_id)
        except CloudflareException as error:
            _LOGGER.error("Error updating zone %s: %s", entry.data[CONF_ZONE], error)

    async def update_records_service(call):
        """Set up service for manual trigger."""
        try:
            await _async_update_cloudflare(cfupdate, zone_id)
        except CloudflareException as error:
            _LOGGER.error("Error updating zone %s: %s", entry.data[CONF_ZONE], error)

    update_interval = timedelta(minutes=DEFAULT_UPDATE_INTERVAL)
    undo_interval = async_track_time_interval(opp, update_records, update_interval)

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = {
        DATA_UNDO_UPDATE_INTERVAL: undo_interval,
    }

    opp.services.async_register(DOMAIN, SERVICE_UPDATE_RECORDS, update_records_service)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload Cloudflare config entry."""
    opp.data[DOMAIN][entry.entry_id][DATA_UNDO_UPDATE_INTERVAL]()
    opp.data[DOMAIN].pop(entry.entry_id)

    return True


async def _async_update_cloudflare(cfupdate: CloudflareUpdater, zone_id: str):
    _LOGGER.debug("Starting update for zone %s", cfupdate.zone)

    records = await cfupdate.get_record_info(zone_id)
    _LOGGER.debug("Records: %s", records)

    await cfupdate.update_records(zone_id, records)
    _LOGGER.debug("Update for zone %s is complete", cfupdate.zone)
