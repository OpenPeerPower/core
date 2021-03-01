"""Support for Solax inverter via local API."""
import asyncio
from datetime import timedelta

from solax import real_time_api
from solax.inverter import InverterError
import voluptuous as vol

from openpeerpower.components.sensor import PLATFORM_SCHEMA
from openpeerpower.const import CONF_IP_ADDRESS, CONF_PORT, TEMP_CELSIUS
from openpeerpower.exceptions import PlatformNotReady
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.entity import Entity
from openpeerpower.helpers.event import async_track_time_interval

DEFAULT_PORT = 80

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_IP_ADDRESS): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    }
)

SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_platform(opp, config, async_add_entities, discovery_info=None):
    """Platform setup."""
    api = await real_time_api(config[CONF_IP_ADDRESS], config[CONF_PORT])
    endpoint = RealTimeDataEndpoint(opp, api)
    resp = await api.get_data()
    serial = resp.serial_number
    opp.async_add_job(endpoint.async_refresh)
    async_track_time_interval(opp, endpoint.async_refresh, SCAN_INTERVAL)
    devices = []
    for sensor, (idx, unit) in api.inverter.sensor_map().items():
        if unit == "C":
            unit = TEMP_CELSIUS
        uid = f"{serial}-{idx}"
        devices.append(Inverter(uid, serial, sensor, unit))
    endpoint.sensors = devices
    async_add_entities(devices)


class RealTimeDataEndpoint:
    """Representation of a Sensor."""

    def __init__(self, opp, api):
        """Initialize the sensor."""
        self.opp = opp
        self.api = api
        self.ready = asyncio.Event()
        self.sensors = []

    async def async_refresh(self, now=None):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Open Peer Power.
        """
        try:
            api_response = await self.api.get_data()
            self.ready.set()
        except InverterError as err:
            if now is not None:
                self.ready.clear()
                return
            raise PlatformNotReady from err
        data = api_response.data
        for sensor in self.sensors:
            if sensor.key in data:
                sensor.value = data[sensor.key]
                sensor.async_schedule_update_op_state()


class Inverter(Entity):
    """Class for a sensor."""

    def __init__(self, uid, serial, key, unit):
        """Initialize an inverter sensor."""
        self.uid = uid
        self.serial = serial
        self.key = key
        self.value = None
        self.unit = unit

    @property
    def state(self):
        """State of this inverter attribute."""
        return self.value

    @property
    def unique_id(self):
        """Return unique id."""
        return self.uid

    @property
    def name(self):
        """Name of this inverter attribute."""
        return f"Solax {self.serial} {self.key}"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self.unit

    @property
    def should_poll(self):
        """No polling needed."""
        return False
