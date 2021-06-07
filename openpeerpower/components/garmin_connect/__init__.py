"""The Garmin Connect integration."""
from datetime import date
import logging

from garminconnect_aio import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.util import Throttle

from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up Garmin Connect from a config entry."""

    websession = async_get_clientsession(opp)
    username: str = entry.data[CONF_USERNAME]
    password: str = entry.data[CONF_PASSWORD]

    garmin_client = Garmin(websession, username, password)

    try:
        await garmin_client.login()
    except (
        GarminConnectAuthenticationError,
        GarminConnectTooManyRequestsError,
    ) as err:
        _LOGGER.error("Error occurred during Garmin Connect login request: %s", err)
        return False
    except (GarminConnectConnectionError) as err:
        _LOGGER.error(
            "Connection error occurred during Garmin Connect login request: %s", err
        )
        raise ConfigEntryNotReady from err
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Unknown error occurred during Garmin Connect login request")
        return False

    garmin_data = GarminConnectData(opp, garmin_client)
    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = garmin_data

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class GarminConnectData:
    """Define an object to hold sensor data."""

    def __init__(self, opp, client):
        """Initialize."""
        self.opp = opp
        self.client = client
        self.data = None

    @Throttle(DEFAULT_UPDATE_INTERVAL)
    async def async_update(self):
        """Update data via API wrapper."""
        today = date.today()

        try:
            summary = await self.client.get_user_summary(today.isoformat())
            body = await self.client.get_body_composition(today.isoformat())

            self.data = {
                **summary,
                **body["totalAverage"],
            }
            self.data["nextAlarm"] = await self.client.get_device_alarms()
        except (
            GarminConnectAuthenticationError,
            GarminConnectTooManyRequestsError,
            GarminConnectConnectionError,
        ) as err:
            _LOGGER.error(
                "Error occurred during Garmin Connect update requests: %s", err
            )
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception(
                "Unknown error occurred during Garmin Connect update requests"
            )
