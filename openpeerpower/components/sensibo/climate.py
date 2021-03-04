"""Support for Sensibo wifi-enabled home thermostats."""

import asyncio
import logging

import aiohttp
import async_timeout
import pysensibo
import voluptuous as vol

from openpeerpower.components.climate import PLATFORM_SCHEMA, ClimateEntity
from openpeerpower.components.climate.const import (
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_SWING_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_STATE,
    ATTR_TEMPERATURE,
    CONF_API_KEY,
    CONF_ID,
    STATE_ON,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from openpeerpower.exceptions import PlatformNotReady
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.util.temperature import convert as convert_temperature

from .const import DOMAIN as SENSIBO_DOMAIN

_LOGGER = logging.getLogger(__name__)

ALL = ["all"]
TIMEOUT = 10

SERVICE_ASSUME_STATE = "assume_state"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_ID, default=ALL): vol.All(cv.ensure_list, [cv.string]),
    }
)

ASSUME_STATE_SCHEMA = vol.Schema(
    {vol.Optional(ATTR_ENTITY_ID): cv.entity_ids, vol.Required(ATTR_STATE): cv.string}
)

_FETCH_FIELDS = ",".join(
    [
        "room{name}",
        "measurements",
        "remoteCapabilities",
        "acState",
        "connectionStatus{isAlive}",
        "temperatureUnit",
    ]
)
_INITIAL_FETCH_FIELDS = f"id,{_FETCH_FIELDS}"

FIELD_TO_FLAG = {
    "fanLevel": SUPPORT_FAN_MODE,
    "swing": SUPPORT_SWING_MODE,
    "targetTemperature": SUPPORT_TARGET_TEMPERATURE,
}

SENSIBO_TO_HA = {
    "cool": HVAC_MODE_COOL,
    "heat": HVAC_MODE_HEAT,
    "fan": HVAC_MODE_FAN_ONLY,
    "auto": HVAC_MODE_HEAT_COOL,
    "dry": HVAC_MODE_DRY,
}

HA_TO_SENSIBO = {value: key for key, value in SENSIBO_TO_HA.items()}


async def async_setup_platform(opp, config, async_add_entities, discovery_info=None):
    """Set up Sensibo devices."""
    client = pysensibo.SensiboClient(
        config[CONF_API_KEY], session=async_get_clientsession(opp), timeout=TIMEOUT
    )
    devices = []
    try:
        for dev in await client.async_get_devices(_INITIAL_FETCH_FIELDS):
            if config[CONF_ID] == ALL or dev["id"] in config[CONF_ID]:
                devices.append(
                    SensiboClimate(client, dev, opp.config.units.temperature_unit)
                )
    except (
        aiohttp.client_exceptions.ClientConnectorError,
        asyncio.TimeoutError,
        pysensibo.SensiboError,
    ) as err:
        _LOGGER.exception("Failed to connect to Sensibo servers")
        raise PlatformNotReady from err

    if not devices:
        return

    async_add_entities(devices)

    async def async_assume_state(service):
        """Set state according to external service call.."""
        entity_ids = service.data.get(ATTR_ENTITY_ID)
        if entity_ids:
            target_climate = [
                device for device in devices if device.entity_id in entity_ids
            ]
        else:
            target_climate = devices

        update_tasks = []
        for climate in target_climate:
            await climate.async_assume_state(service.data.get(ATTR_STATE))
            update_tasks.append(climate.async_update_op_state(True))

        if update_tasks:
            await asyncio.wait(update_tasks)

    opp.services.async_register(
        SENSIBO_DOMAIN,
        SERVICE_ASSUME_STATE,
        async_assume_state,
        schema=ASSUME_STATE_SCHEMA,
    )


class SensiboClimate(ClimateEntity):
    """Representation of a Sensibo device."""

    def __init__(self, client, data, units):
        """Build SensiboClimate.

        client: aiohttp session.
        data: initially-fetched data.
        """
        self._client = client
        self._id = data["id"]
        self._external_state = None
        self._units = units
        self._available = False
        self._do_update(data)

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._supported_features

    def _do_update(self, data):
        self._name = data["room"]["name"]
        self._measurements = data["measurements"]
        self._ac_states = data["acState"]
        self._available = data["connectionStatus"]["isAlive"]
        capabilities = data["remoteCapabilities"]
        self._operations = [SENSIBO_TO_HA[mode] for mode in capabilities["modes"]]
        self._operations.append(HVAC_MODE_OFF)
        self._current_capabilities = capabilities["modes"][self._ac_states["mode"]]
        temperature_unit_key = data.get("temperatureUnit") or self._ac_states.get(
            "temperatureUnit"
        )
        if temperature_unit_key:
            self._temperature_unit = (
                TEMP_CELSIUS if temperature_unit_key == "C" else TEMP_FAHRENHEIT
            )
            self._temperatures_list = (
                self._current_capabilities["temperatures"]
                .get(temperature_unit_key, {})
                .get("values", [])
            )
        else:
            self._temperature_unit = self._units
            self._temperatures_list = []
        self._supported_features = 0
        for key in self._ac_states:
            if key in FIELD_TO_FLAG:
                self._supported_features |= FIELD_TO_FLAG[key]

    @property
    def state(self):
        """Return the current state."""
        return self._external_state or super().state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {"battery": self.current_battery}

    @property
    def temperature_unit(self):
        """Return the unit of measurement which this thermostat uses."""
        return self._temperature_unit

    @property
    def available(self):
        """Return True if entity is available."""
        return self._available

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._ac_states.get("targetTemperature")

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        if self.temperature_unit == self.opp.config.units.temperature_unit:
            # We are working in same units as the a/c unit. Use whole degrees
            # like the API supports.
            return 1
        # Unit conversion is going on. No point to stick to specific steps.
        return None

    @property
    def hvac_mode(self):
        """Return current operation ie. heat, cool, idle."""
        if not self._ac_states["on"]:
            return HVAC_MODE_OFF
        return SENSIBO_TO_HA.get(self._ac_states["mode"])

    @property
    def current_humidity(self):
        """Return the current humidity."""
        return self._measurements["humidity"]

    @property
    def current_battery(self):
        """Return the current battery voltage."""
        return self._measurements.get("batteryVoltage")

    @property
    def current_temperature(self):
        """Return the current temperature."""
        # This field is not affected by temperatureUnit.
        # It is always in C
        return convert_temperature(
            self._measurements["temperature"], TEMP_CELSIUS, self.temperature_unit
        )

    @property
    def hvac_modes(self):
        """List of available operation modes."""
        return self._operations

    @property
    def fan_mode(self):
        """Return the fan setting."""
        return self._ac_states.get("fanLevel")

    @property
    def fan_modes(self):
        """List of available fan modes."""
        return self._current_capabilities.get("fanLevels")

    @property
    def swing_mode(self):
        """Return the fan setting."""
        return self._ac_states.get("swing")

    @property
    def swing_modes(self):
        """List of available swing modes."""
        return self._current_capabilities.get("swing")

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return (
            self._temperatures_list[0] if self._temperatures_list else super().min_temp
        )

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return (
            self._temperatures_list[-1] if self._temperatures_list else super().max_temp
        )

    @property
    def unique_id(self):
        """Return unique ID based on Sensibo ID."""
        return self._id

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        temperature = int(temperature)
        if temperature not in self._temperatures_list:
            # Requested temperature is not supported.
            if temperature == self.target_temperature:
                return
            index = self._temperatures_list.index(self.target_temperature)
            if (
                temperature > self.target_temperature
                and index < len(self._temperatures_list) - 1
            ):
                temperature = self._temperatures_list[index + 1]
            elif temperature < self.target_temperature and index > 0:
                temperature = self._temperatures_list[index - 1]
            else:
                return

        with async_timeout.timeout(TIMEOUT):
            await self._client.async_set_ac_state_property(
                self._id, "targetTemperature", temperature, self._ac_states
            )

    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        with async_timeout.timeout(TIMEOUT):
            await self._client.async_set_ac_state_property(
                self._id, "fanLevel", fan_mode, self._ac_states
            )

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target operation mode."""
        if hvac_mode == HVAC_MODE_OFF:
            with async_timeout.timeout(TIMEOUT):
                await self._client.async_set_ac_state_property(
                    self._id, "on", False, self._ac_states
                )
            return

        # Turn on if not currently on.
        if not self._ac_states["on"]:
            with async_timeout.timeout(TIMEOUT):
                await self._client.async_set_ac_state_property(
                    self._id, "on", True, self._ac_states
                )

        with async_timeout.timeout(TIMEOUT):
            await self._client.async_set_ac_state_property(
                self._id, "mode", HA_TO_SENSIBO[hvac_mode], self._ac_states
            )

    async def async_set_swing_mode(self, swing_mode):
        """Set new target swing operation."""
        with async_timeout.timeout(TIMEOUT):
            await self._client.async_set_ac_state_property(
                self._id, "swing", swing_mode, self._ac_states
            )

    async def async_turn_on(self):
        """Turn Sensibo unit on."""
        with async_timeout.timeout(TIMEOUT):
            await self._client.async_set_ac_state_property(
                self._id, "on", True, self._ac_states
            )

    async def async_turn_off(self):
        """Turn Sensibo unit on."""
        with async_timeout.timeout(TIMEOUT):
            await self._client.async_set_ac_state_property(
                self._id, "on", False, self._ac_states
            )

    async def async_assume_state(self, state):
        """Set external state."""
        change_needed = (state != HVAC_MODE_OFF and not self._ac_states["on"]) or (
            state == HVAC_MODE_OFF and self._ac_states["on"]
        )

        if change_needed:
            with async_timeout.timeout(TIMEOUT):
                await self._client.async_set_ac_state_property(
                    self._id,
                    "on",
                    state != HVAC_MODE_OFF,  # value
                    self._ac_states,
                    True,  # assumed_state
                )

        if state in [STATE_ON, HVAC_MODE_OFF]:
            self._external_state = None
        else:
            self._external_state = state

    async def async_update(self):
        """Retrieve latest state."""
        try:
            with async_timeout.timeout(TIMEOUT):
                data = await self._client.async_get_device(self._id, _FETCH_FIELDS)
                self._do_update(data)
        except (aiohttp.client_exceptions.ClientError, pysensibo.SensiboError):
            _LOGGER.warning("Failed to connect to Sensibo servers")
            self._available = False
