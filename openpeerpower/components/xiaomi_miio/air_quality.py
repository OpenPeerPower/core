"""Support for Xiaomi Mi Air Quality Monitor (PM2.5)."""
import logging

from miio import AirQualityMonitor, AirQualityMonitorCGDN1, DeviceException
import voluptuous as vol

from openpeerpower.components.air_quality import PLATFORM_SCHEMA, AirQualityEntity
from openpeerpower.config_entries import SOURCE_IMPORT
from openpeerpower.const import CONF_HOST, CONF_NAME, CONF_TOKEN
import openpeerpower.helpers.config_validation as cv

from .const import (
    CONF_DEVICE,
    CONF_FLOW_TYPE,
    CONF_MODEL,
    DOMAIN,
    MODEL_AIRQUALITYMONITOR_B1,
    MODEL_AIRQUALITYMONITOR_CGDN1,
    MODEL_AIRQUALITYMONITOR_S1,
    MODEL_AIRQUALITYMONITOR_V1,
)
from .device import XiaomiMiioEntity

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Xiaomi Miio Air Quality Monitor"

ATTR_CO2E = "carbon_dioxide_equivalent"
ATTR_TVOC = "total_volatile_organic_compounds"
ATTR_TEMP = "temperature"
ATTR_HUM = "humidity"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_TOKEN): vol.All(cv.string, vol.Length(min=32, max=32)),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)

PROP_TO_ATTR = {
    "carbon_dioxide_equivalent": ATTR_CO2E,
    "total_volatile_organic_compounds": ATTR_TVOC,
    "temperature": ATTR_TEMP,
    "humidity": ATTR_HUM,
}


class AirMonitorB1(XiaomiMiioEntity, AirQualityEntity):
    """Air Quality class for Xiaomi cgllc.airmonitor.b1 device."""

    def __init__(self, name, device, entry, unique_id):
        """Initialize the entity."""
        super().__init__(name, device, entry, unique_id)

        self._icon = "mdi:cloud"
        self._available = None
        self._air_quality_index = None
        self._carbon_dioxide = None
        self._carbon_dioxide_equivalent = None
        self._particulate_matter_2_5 = None
        self._total_volatile_organic_compounds = None
        self._temperature = None
        self._humidity = None

    async def async_update(self):
        """Fetch state from the miio device."""
        try:
            state = await self.opp.async_add_executor_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)
            self._carbon_dioxide_equivalent = state.co2e
            self._particulate_matter_2_5 = round(state.pm25, 1)
            self._total_volatile_organic_compounds = round(state.tvoc, 3)
            self._temperature = round(state.temperature, 2)
            self._humidity = round(state.humidity, 2)
            self._available = True
        except DeviceException as ex:
            self._available = False
            _LOGGER.error("Got exception while fetching the state: %s", ex)

    @property
    def icon(self):
        """Return the icon to use for device if any."""
        return self._icon

    @property
    def available(self):
        """Return true when state is known."""
        return self._available

    @property
    def air_quality_index(self):
        """Return the Air Quality Index (AQI)."""
        return self._air_quality_index

    @property
    def carbon_dioxide(self):
        """Return the CO2 (carbon dioxide) level."""
        return self._carbon_dioxide

    @property
    def carbon_dioxide_equivalent(self):
        """Return the CO2e (carbon dioxide equivalent) level."""
        return self._carbon_dioxide_equivalent

    @property
    def particulate_matter_2_5(self):
        """Return the particulate matter 2.5 level."""
        return self._particulate_matter_2_5

    @property
    def total_volatile_organic_compounds(self):
        """Return the total volatile organic compounds."""
        return self._total_volatile_organic_compounds

    @property
    def temperature(self):
        """Return the current temperature."""
        return self._temperature

    @property
    def humidity(self):
        """Return the current humidity."""
        return self._humidity

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = {}

        for prop, attr in PROP_TO_ATTR.items():
            value = getattr(self, prop)
            if value is not None:
                data[attr] = value

        return data


class AirMonitorS1(AirMonitorB1):
    """Air Quality class for Xiaomi cgllc.airmonitor.s1 device."""

    async def async_update(self):
        """Fetch state from the miio device."""
        try:
            state = await self.opp.async_add_executor_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)
            self._carbon_dioxide = state.co2
            self._particulate_matter_2_5 = state.pm25
            self._total_volatile_organic_compounds = state.tvoc
            self._temperature = state.temperature
            self._humidity = state.humidity
            self._available = True
        except DeviceException as ex:
            if self._available:
                self._available = False
                _LOGGER.error("Got exception while fetching the state: %s", ex)


class AirMonitorV1(AirMonitorB1):
    """Air Quality class for Xiaomi cgllc.airmonitor.s1 device."""

    async def async_update(self):
        """Fetch state from the miio device."""
        try:
            state = await self.opp.async_add_executor_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)
            self._air_quality_index = state.aqi
            self._available = True
        except DeviceException as ex:
            if self._available:
                self._available = False
                _LOGGER.error("Got exception while fetching the state: %s", ex)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return None


class AirMonitorCGDN1(XiaomiMiioEntity, AirQualityEntity):
    """Air Quality class for cgllc.airm.cgdn1 device."""

    def __init__(self, name, device, entry, unique_id):
        """Initialize the entity."""
        super().__init__(name, device, entry, unique_id)

        self._icon = "mdi:cloud"
        self._available = None
        self._carbon_dioxide = None
        self._particulate_matter_2_5 = None
        self._particulate_matter_10 = None

    async def async_update(self):
        """Fetch state from the miio device."""
        try:
            state = await self.opp.async_add_executor_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)
            self._carbon_dioxide = state.co2
            self._particulate_matter_2_5 = round(state.pm25, 1)
            self._particulate_matter_10 = round(state.pm10, 1)
            self._available = True
        except DeviceException as ex:
            self._available = False
            _LOGGER.error("Got exception while fetching the state: %s", ex)

    @property
    def icon(self):
        """Return the icon to use for device if any."""
        return self._icon

    @property
    def available(self):
        """Return true when state is known."""
        return self._available

    @property
    def carbon_dioxide(self):
        """Return the CO2 (carbon dioxide) level."""
        return self._carbon_dioxide

    @property
    def particulate_matter_2_5(self):
        """Return the particulate matter 2.5 level."""
        return self._particulate_matter_2_5

    @property
    def particulate_matter_10(self):
        """Return the particulate matter 10 level."""
        return self._particulate_matter_10


DEVICE_MAP = {
    MODEL_AIRQUALITYMONITOR_S1: {
        "device_class": AirQualityMonitor,
        "entity_class": AirMonitorS1,
    },
    MODEL_AIRQUALITYMONITOR_B1: {
        "device_class": AirQualityMonitor,
        "entity_class": AirMonitorB1,
    },
    MODEL_AIRQUALITYMONITOR_V1: {
        "device_class": AirQualityMonitor,
        "entity_class": AirMonitorV1,
    },
    MODEL_AIRQUALITYMONITOR_CGDN1: {
        "device_class": lambda host, token, model: AirQualityMonitorCGDN1(host, token),
        "entity_class": AirMonitorCGDN1,
    },
}


async def async_setup_platform(opp, config, async_add_entities, discovery_info=None):
    """Import Miio configuration from YAML."""
    _LOGGER.warning(
        "Loading Xiaomi Miio Air Quality via platform setup is deprecated. "
        "Please remove it from your configuration"
    )
    opp.async_create_task(
        opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=config,
        )
    )


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up the Xiaomi Air Quality from a config entry."""
    entities = []

    if config_entry.data[CONF_FLOW_TYPE] == CONF_DEVICE:
        host = config_entry.data[CONF_HOST]
        token = config_entry.data[CONF_TOKEN]
        name = config_entry.title
        model = config_entry.data[CONF_MODEL]
        unique_id = config_entry.unique_id

        _LOGGER.debug("Initializing with host %s (token %s...)", host, token[:5])

        if model in DEVICE_MAP:
            device_entry = DEVICE_MAP[model]
            entities.append(
                device_entry["entity_class"](
                    name,
                    device_entry["device_class"](host, token, model=model),
                    config_entry,
                    unique_id,
                )
            )
        else:
            _LOGGER.warning("AirQualityMonitor model '%s' is not yet supported", model)

    async_add_entities(entities, update_before_add=True)
