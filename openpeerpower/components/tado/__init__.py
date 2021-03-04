"""Support for the (unofficial) Tado API."""
import asyncio
from datetime import timedelta
import logging

from PyTado.interface import Tado
from requests import RequestException
import requests.exceptions

from openpeerpower.components.climate.const import PRESET_AWAY, PRESET_HOME
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.dispatcher import dispatcher_send
from openpeerpower.helpers.event import async_track_time_interval
from openpeerpower.util import Throttle

from .const import (
    CONF_FALLBACK,
    DATA,
    DOMAIN,
    INSIDE_TEMPERATURE_MEASUREMENT,
    SIGNAL_TADO_UPDATE_RECEIVED,
    TEMP_OFFSET,
    UPDATE_LISTENER,
    UPDATE_TRACK,
)

_LOGGER = logging.getLogger(__name__)


PLATFORMS = ["binary_sensor", "sensor", "climate", "water_heater"]

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=4)
SCAN_INTERVAL = timedelta(minutes=5)

CONFIG_SCHEMA = cv.deprecated(DOMAIN)


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the Tado component."""

    opp.data.setdefault(DOMAIN, {})

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Tado from a config entry."""

    _async_import_options_from_data_if_missing(opp, entry)

    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    fallback = entry.options.get(CONF_FALLBACK, True)

    tadoconnector = TadoConnector(opp, username, password, fallback)

    try:
        await opp.async_add_executor_job(tadoconnector.setup)
    except KeyError:
        _LOGGER.error("Failed to login to tado")
        return False
    except RuntimeError as exc:
        _LOGGER.error("Failed to setup tado: %s", exc)
        return ConfigEntryNotReady
    except requests.exceptions.Timeout as ex:
        raise ConfigEntryNotReady from ex
    except requests.exceptions.HTTPError as ex:
        if ex.response.status_code > 400 and ex.response.status_code < 500:
            _LOGGER.error("Failed to login to tado: %s", ex)
            return False
        raise ConfigEntryNotReady from ex

    # Do first update
    await opp.async_add_executor_job(tadoconnector.update)

    # Poll for updates in the background
    update_track = async_track_time_interval(
        opp,
        lambda now: tadoconnector.update(),
        SCAN_INTERVAL,
    )

    update_listener = entry.add_update_listener(_async_update_listener)

    opp.data[DOMAIN][entry.entry_id] = {
        DATA: tadoconnector,
        UPDATE_TRACK: update_track,
        UPDATE_LISTENER: update_listener,
    }

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


@callback
def _async_import_options_from_data_if_missing(opp: OpenPeerPower, entry: ConfigEntry):
    options = dict(entry.options)
    if CONF_FALLBACK not in options:
        options[CONF_FALLBACK] = entry.data.get(CONF_FALLBACK, True)
        opp.config_entries.async_update_entry(entry, options=options)


async def _async_update_listener(opp: OpenPeerPower, entry: ConfigEntry):
    """Handle options update."""
    await opp.config_entries.async_reload(entry.entry_id)


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

    opp.data[DOMAIN][entry.entry_id][UPDATE_TRACK]()
    opp.data[DOMAIN][entry.entry_id][UPDATE_LISTENER]()

    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class TadoConnector:
    """An object to store the Tado data."""

    def __init__(self, opp, username, password, fallback):
        """Initialize Tado Connector."""
        self.opp = opp
        self._username = username
        self._password = password
        self._fallback = fallback

        self.home_id = None
        self.tado = None
        self.zones = None
        self.devices = None
        self.data = {
            "device": {},
            "zone": {},
        }

    @property
    def fallback(self):
        """Return fallback flag to Smart Schedule."""
        return self._fallback

    def setup(self):
        """Connect to Tado and fetch the zones."""
        self.tado = Tado(self._username, self._password)
        self.tado.setDebugging(True)
        # Load zones and devices
        self.zones = self.tado.getZones()
        self.devices = self.tado.getDevices()
        self.home_id = self.tado.getMe()["homes"][0]["id"]

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update the registered zones."""
        for device in self.devices:
            self.update_sensor("device", device["shortSerialNo"])
        for zone in self.zones:
            self.update_sensor("zone", zone["id"])

    def update_sensor(self, sensor_type, sensor):
        """Update the internal data from Tado."""
        _LOGGER.debug("Updating %s %s", sensor_type, sensor)
        try:
            if sensor_type == "device":
                data = self.tado.getDeviceInfo(sensor)
                if (
                    INSIDE_TEMPERATURE_MEASUREMENT
                    in data["characteristics"]["capabilities"]
                ):
                    data[TEMP_OFFSET] = self.tado.getDeviceInfo(sensor, TEMP_OFFSET)
            elif sensor_type == "zone":
                data = self.tado.getZoneState(sensor)
            else:
                _LOGGER.debug("Unknown sensor: %s", sensor_type)
                return
        except RuntimeError:
            _LOGGER.error(
                "Unable to connect to Tado while updating %s %s",
                sensor_type,
                sensor,
            )
            return

        self.data[sensor_type][sensor] = data

        _LOGGER.debug(
            "Dispatching update to %s %s %s: %s",
            self.home_id,
            sensor_type,
            sensor,
            data,
        )
        dispatcher_send(
            self.opp,
            SIGNAL_TADO_UPDATE_RECEIVED.format(self.home_id, sensor_type, sensor),
        )

    def get_capabilities(self, zone_id):
        """Return the capabilities of the devices."""
        return self.tado.getCapabilities(zone_id)

    def reset_zone_overlay(self, zone_id):
        """Reset the zone back to the default operation."""
        self.tado.resetZoneOverlay(zone_id)
        self.update_sensor("zone", zone_id)

    def set_presence(
        self,
        presence=PRESET_HOME,
    ):
        """Set the presence to home or away."""
        if presence == PRESET_AWAY:
            self.tado.setAway()
        elif presence == PRESET_HOME:
            self.tado.setHome()

    def set_zone_overlay(
        self,
        zone_id=None,
        overlay_mode=None,
        temperature=None,
        duration=None,
        device_type="HEATING",
        mode=None,
        fan_speed=None,
        swing=None,
    ):
        """Set a zone overlay."""
        _LOGGER.debug(
            "Set overlay for zone %s: overlay_mode=%s, temp=%s, duration=%s, type=%s, mode=%s fan_speed=%s swing=%s",
            zone_id,
            overlay_mode,
            temperature,
            duration,
            device_type,
            mode,
            fan_speed,
            swing,
        )

        try:
            self.tado.setZoneOverlay(
                zone_id,
                overlay_mode,
                temperature,
                duration,
                device_type,
                "ON",
                mode,
                fanSpeed=fan_speed,
                swing=swing,
            )

        except RequestException as exc:
            _LOGGER.error("Could not set zone overlay: %s", exc)

        self.update_sensor("zone", zone_id)

    def set_zone_off(self, zone_id, overlay_mode, device_type="HEATING"):
        """Set a zone to off."""
        try:
            self.tado.setZoneOverlay(
                zone_id, overlay_mode, None, None, device_type, "OFF"
            )
        except RequestException as exc:
            _LOGGER.error("Could not set zone overlay: %s", exc)

        self.update_sensor("zone", zone_id)

    def set_temperature_offset(self, device_id, offset):
        """Set temperature offset of device."""
        try:
            self.tado.setTempOffset(device_id, offset)
        except RequestException as exc:
            _LOGGER.error("Could not set temperature offset: %s", exc)
