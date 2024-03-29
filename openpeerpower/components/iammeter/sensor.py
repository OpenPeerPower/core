"""Support for iammeter via local API."""
import asyncio
from datetime import timedelta
import logging

import async_timeout
from iammeter import real_time_api
from iammeter.power_meter import IamMeterError
import voluptuous as vol

from openpeerpower.components.sensor import PLATFORM_SCHEMA, SensorEntity
from openpeerpower.const import CONF_HOST, CONF_NAME, CONF_PORT
from openpeerpower.exceptions import PlatformNotReady
from openpeerpower.helpers import debounce
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_PORT = 80
DEFAULT_DEVICE_NAME = "IamMeter"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_DEVICE_NAME): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    }
)

SCAN_INTERVAL = timedelta(seconds=30)
PLATFORM_TIMEOUT = 8


async def async_setup_platform(opp, config, async_add_entities, discovery_info=None):
    """Platform setup."""
    config_host = config[CONF_HOST]
    config_port = config[CONF_PORT]
    config_name = config[CONF_NAME]
    try:
        with async_timeout.timeout(PLATFORM_TIMEOUT):
            api = await real_time_api(config_host, config_port)
    except (IamMeterError, asyncio.TimeoutError) as err:
        _LOGGER.error("Device is not ready")
        raise PlatformNotReady from err

    async def async_update_data():
        try:
            with async_timeout.timeout(PLATFORM_TIMEOUT):
                return await api.get_data()
        except (IamMeterError, asyncio.TimeoutError) as err:
            raise UpdateFailed from err

    coordinator = DataUpdateCoordinator(
        opp,
        _LOGGER,
        name=DEFAULT_DEVICE_NAME,
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
        request_refresh_debouncer=debounce.Debouncer(
            opp, _LOGGER, cooldown=0.3, immediate=True
        ),
    )
    await coordinator.async_refresh()
    entities = []
    for sensor_name, (row, idx, unit) in api.iammeter.sensor_map().items():
        serial_number = api.iammeter.serial_number
        uid = f"{serial_number}-{row}-{idx}"
        entities.append(IamMeter(coordinator, uid, sensor_name, unit, config_name))
    async_add_entities(entities)


class IamMeter(CoordinatorEntity, SensorEntity):
    """Class for a sensor."""

    def __init__(self, coordinator, uid, sensor_name, unit, dev_name):
        """Initialize an iammeter sensor."""
        super().__init__(coordinator)
        self.uid = uid
        self.sensor_name = sensor_name
        self.unit = unit
        self.dev_name = dev_name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data.data[self.sensor_name]

    @property
    def unique_id(self):
        """Return unique id."""
        return self.uid

    @property
    def name(self):
        """Name of this iammeter attribute."""
        return f"{self.dev_name} {self.sensor_name}"

    @property
    def icon(self):
        """Icon for each sensor."""
        return "mdi:flash"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self.unit
