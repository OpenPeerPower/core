"""Support for deCONZ climate devices."""
from typing import Optional

from pydeconz.sensor import Thermostat

from openpeerpower.components.climate import DOMAIN, ClimateEntity
from openpeerpower.components.climate.const import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_OFF,
    FAN_ON,
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    PRESET_BOOST,
    PRESET_COMFORT,
    PRESET_ECO,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from openpeerpower.const import ATTR_TEMPERATURE, TEMP_CELSIUS
from openpeerpower.core import callback
from openpeerpower.helpers.dispatcher import async_dispatcher_connect

from .const import ATTR_LOCKED, ATTR_OFFSET, ATTR_VALVE, NEW_SENSOR
from .deconz_device import DeconzDevice
from .gateway import get_gateway_from_config_entry

DECONZ_FAN_SMART = "smart"

FAN_MODE_TO_DECONZ = {
    DECONZ_FAN_SMART: "smart",
    FAN_AUTO: "auto",
    FAN_HIGH: "high",
    FAN_MEDIUM: "medium",
    FAN_LOW: "low",
    FAN_ON: "on",
    FAN_OFF: "off",
}

DECONZ_TO_FAN_MODE = {value: key for key, value in FAN_MODE_TO_DECONZ.items()}

HVAC_MODE_TO_DECONZ = {
    HVAC_MODE_AUTO: "auto",
    HVAC_MODE_COOL: "cool",
    HVAC_MODE_HEAT: "heat",
    HVAC_MODE_OFF: "off",
}

DECONZ_PRESET_AUTO = "auto"
DECONZ_PRESET_COMPLEX = "complex"
DECONZ_PRESET_HOLIDAY = "holiday"
DECONZ_PRESET_MANUAL = "manual"

PRESET_MODE_TO_DECONZ = {
    DECONZ_PRESET_AUTO: "auto",
    PRESET_BOOST: "boost",
    PRESET_COMFORT: "comfort",
    DECONZ_PRESET_COMPLEX: "complex",
    PRESET_ECO: "eco",
    DECONZ_PRESET_HOLIDAY: "holiday",
    DECONZ_PRESET_MANUAL: "manual",
}

DECONZ_TO_PRESET_MODE = {value: key for key, value in PRESET_MODE_TO_DECONZ.items()}


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up the deCONZ climate devices.

    Thermostats are based on the same device class as sensors in deCONZ.
    """
    gateway = get_gateway_from_config_entry(opp, config_entry)
    gateway.entities[DOMAIN] = set()

    @callback
    def async_add_climate(sensors=gateway.api.sensors.values()):
        """Add climate devices from deCONZ."""
        entities = []

        for sensor in sensors:

            if (
                sensor.type in Thermostat.ZHATYPE
                and sensor.uniqueid not in gateway.entities[DOMAIN]
                and (
                    gateway.option_allow_clip_sensor
                    or not sensor.type.startswith("CLIP")
                )
            ):
                entities.append(DeconzThermostat(sensor, gateway))

        if entities:
            async_add_entities(entities)

    gateway.listeners.append(
        async_dispatcher_connect(
            opp, gateway.async_signal_new_device(NEW_SENSOR), async_add_climate
        )
    )

    async_add_climate()


class DeconzThermostat(DeconzDevice, ClimateEntity):
    """Representation of a deCONZ thermostat."""

    TYPE = DOMAIN

    def __init__(self, device, gateway):
        """Set up thermostat device."""
        super().__init__(device, gateway)

        self._hvac_mode_to_deconz = dict(HVAC_MODE_TO_DECONZ)
        if "mode" not in device.raw["config"]:
            self._hvac_mode_to_deconz = {
                HVAC_MODE_HEAT: True,
                HVAC_MODE_OFF: False,
            }
        elif "coolsetpoint" not in device.raw["config"]:
            self._hvac_mode_to_deconz.pop(HVAC_MODE_COOL)
        self._deconz_to_hvac_mode = {
            value: key for key, value in self._hvac_mode_to_deconz.items()
        }

        self._features = SUPPORT_TARGET_TEMPERATURE

        if "fanmode" in device.raw["config"]:
            self._features |= SUPPORT_FAN_MODE

        if "preset" in device.raw["config"]:
            self._features |= SUPPORT_PRESET_MODE

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._features

    # Fan control

    @property
    def fan_mode(self) -> str:
        """Return fan operation."""
        return DECONZ_TO_FAN_MODE.get(
            self._device.fanmode, FAN_ON if self._device.state_on else FAN_OFF
        )

    @property
    def fan_modes(self) -> list:
        """Return the list of available fan operation modes."""
        return list(FAN_MODE_TO_DECONZ)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        if fan_mode not in FAN_MODE_TO_DECONZ:
            raise ValueError(f"Unsupported fan mode {fan_mode}")

        data = {"fanmode": FAN_MODE_TO_DECONZ[fan_mode]}

        await self._device.async_set_config(data)

    # HVAC control

    @property
    def hvac_mode(self):
        """Return hvac operation ie. heat, cool mode.

        Need to be one of HVAC_MODE_*.
        """
        return self._deconz_to_hvac_mode.get(
            self._device.mode,
            HVAC_MODE_HEAT if self._device.state_on else HVAC_MODE_OFF,
        )

    @property
    def hvac_modes(self) -> list:
        """Return the list of available hvac operation modes."""
        return list(self._hvac_mode_to_deconz)

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        """Set new target hvac mode."""
        if hvac_mode not in self._hvac_mode_to_deconz:
            raise ValueError(f"Unsupported HVAC mode {hvac_mode}")

        data = {"mode": self._hvac_mode_to_deconz[hvac_mode]}
        if len(self._hvac_mode_to_deconz) == 2:  # Only allow turn on and off thermostat
            data = {"on": self._hvac_mode_to_deconz[hvac_mode]}

        await self._device.async_set_config(data)

    # Preset control

    @property
    def preset_mode(self) -> Optional[str]:
        """Return preset mode."""
        return DECONZ_TO_PRESET_MODE.get(self._device.preset)

    @property
    def preset_modes(self) -> list:
        """Return the list of available preset modes."""
        return list(PRESET_MODE_TO_DECONZ)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if preset_mode not in PRESET_MODE_TO_DECONZ:
            raise ValueError(f"Unsupported preset mode {preset_mode}")

        data = {"preset": PRESET_MODE_TO_DECONZ[preset_mode]}

        await self._device.async_set_config(data)

    # Temperature control

    @property
    def current_temperature(self) -> float:
        """Return the current temperature."""
        return self._device.temperature

    @property
    def target_temperature(self) -> float:
        """Return the target temperature."""
        if self._device.mode == "cool":
            return self._device.coolsetpoint
        return self._device.heatsetpoint

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if ATTR_TEMPERATURE not in kwargs:
            raise ValueError(f"Expected attribute {ATTR_TEMPERATURE}")

        data = {"heatsetpoint": kwargs[ATTR_TEMPERATURE] * 100}
        if self._device.mode == "cool":
            data = {"coolsetpoint": kwargs[ATTR_TEMPERATURE] * 100}

        await self._device.async_set_config(data)

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def device_state_attributes(self):
        """Return the state attributes of the thermostat."""
        attr = {}

        if self._device.offset:
            attr[ATTR_OFFSET] = self._device.offset

        if self._device.valve is not None:
            attr[ATTR_VALVE] = self._device.valve

        if self._device.locked is not None:
            attr[ATTR_LOCKED] = self._device.locked

        return attr
