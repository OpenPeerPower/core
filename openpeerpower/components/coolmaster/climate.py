"""CoolMasterNet platform to control of CoolMasteNet Climate Devices."""

import logging

from openpeerpower.components.climate import ClimateEntity
from openpeerpower.components.climate.const import (
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from openpeerpower.const import ATTR_TEMPERATURE, TEMP_CELSIUS, TEMP_FAHRENHEIT
from openpeerpower.core import callback
from openpeerpower.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SUPPORTED_MODES, DATA_COORDINATOR, DATA_INFO, DOMAIN

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE

CM_TO_HA_STATE = {
    "heat": HVAC_MODE_HEAT,
    "cool": HVAC_MODE_COOL,
    "auto": HVAC_MODE_HEAT_COOL,
    "dry": HVAC_MODE_DRY,
    "fan": HVAC_MODE_FAN_ONLY,
}

HA_STATE_TO_CM = {value: key for key, value in CM_TO_HA_STATE.items()}

FAN_MODES = ["low", "med", "high", "auto"]

_LOGGER = logging.getLogger(__name__)


def _build_entity(coordinator, unit_id, unit, supported_modes, info):
    _LOGGER.debug("Found device %s", unit_id)
    return CoolmasterClimate(coordinator, unit_id, unit, supported_modes, info)


async def async_setup_entry.opp, config_entry, async_add_devices):
    """Set up the CoolMasterNet climate platform."""
    supported_modes = config_entry.data.get(CONF_SUPPORTED_MODES)
    info = opp.data[DOMAIN][config_entry.entry_id][DATA_INFO]

    coordinator = opp.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR]

    all_devices = [
        _build_entity(coordinator, unit_id, unit, supported_modes, info)
        for (unit_id, unit) in coordinator.data.items()
    ]

    async_add_devices(all_devices)


class CoolmasterClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a coolmaster climate device."""

    def __init__(self, coordinator, unit_id, unit, supported_modes, info):
        """Initialize the climate device."""
        super().__init__(coordinator)
        self._unit_id = unit_id
        self._unit = unit
        self._hvac_modes = supported_modes
        self._info = info

    @callback
    def _op.dle_coordinator_update(self):
        self._unit = self.coordinator.data[self._unit_id]
        super()._op.dle_coordinator_update()

    @property
    def device_info(self):
        """Return device info for this device."""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": "CoolAutomation",
            "model": "CoolMasterNet",
            "sw_version": self._info["version"],
        }

    @property
    def unique_id(self):
        """Return unique ID for this device."""
        return self._unit_id

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def name(self):
        """Return the name of the climate device."""
        return self.unique_id

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        if self._unit.temperature_unit == "celsius":
            return TEMP_CELSIUS

        return TEMP_FAHRENHEIT

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._unit.temperature

    @property
    def target_temperature(self):
        """Return the temperature we are trying to reach."""
        return self._unit.thermostat

    @property
    def hvac_mode(self):
        """Return hvac target hvac state."""
        mode = self._unit.mode
        is_on = self._unit.is_on
        if not is_on:
            return HVAC_MODE_OFF

        return CM_TO_HA_STATE[mode]

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        return self._hvac_modes

    @property
    def fan_mode(self):
        """Return the fan setting."""
        return self._unit.fan_speed

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        return FAN_MODES

    async def async_set_temperature(self, **kwargs):
        """Set new target temperatures."""
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is not None:
            _LOGGER.debug("Setting temp of %s to %s", self.unique_id, str(temp))
            self._unit = await self._unit.set_thermostat(temp)
            self.async_write_op.state()

    async def async_set_fan_mode(self, fan_mode):
        """Set new fan mode."""
        _LOGGER.debug("Setting fan mode of %s to %s", self.unique_id, fan_mode)
        self._unit = await self._unit.set_fan_speed(fan_mode)
        self.async_write_op.state()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new operation mode."""
        _LOGGER.debug("Setting operation mode of %s to %s", self.unique_id, hvac_mode)

        if hvac_mode == HVAC_MODE_OFF:
            await self.async_turn_off()
        else:
            self._unit = await self._unit.set_mode(HA_STATE_TO_CM[hvac_mode])
            await self.async_turn_on()

    async def async_turn_on(self):
        """Turn on."""
        _LOGGER.debug("Turning %s on", self.unique_id)
        self._unit = await self._unit.turn_on()
        self.async_write_op.state()

    async def async_turn_off(self):
        """Turn off."""
        _LOGGER.debug("Turning %s off", self.unique_id)
        self._unit = await self._unit.turn_off()
        self.async_write_op.state()
