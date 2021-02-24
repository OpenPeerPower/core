"""Support for Homekit sensors."""
from aiohomekit.model.characteristics import CharacteristicsTypes
from aiohomekit.model.services import ServicesTypes

from openpeerpower.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_ILLUMINANCE,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_TEMPERATURE,
    LIGHT_LUX,
    PERCENTAGE,
    TEMP_CELSIUS,
)
from openpeerpower.core import callback

from . import KNOWN_DEVICES, CharacteristicEntity, HomeKitEntity

HUMIDITY_ICON = "mdi:water-percent"
TEMP_C_ICON = "mdi:thermometer"
BRIGHTNESS_ICON = "mdi:brightness-6"
CO2_ICON = "mdi:molecule-co2"


SIMPLE_SENSOR = {
    CharacteristicsTypes.Vendor.EVE_ENERGY_WATT: {
        "name": "Real Time Energy",
        "device_class": DEVICE_CLASS_POWER,
        "unit": "watts",
        "icon": "mdi:chart-line",
    },
    CharacteristicsTypes.Vendor.KOOGEEK_REALTIME_ENERGY: {
        "name": "Real Time Energy",
        "device_class": DEVICE_CLASS_POWER,
        "unit": "watts",
        "icon": "mdi:chart-line",
    },
}


class HomeKitHumiditySensor(HomeKitEntity):
    """Representation of a Homekit humidity sensor."""

    def get_characteristic_types(self):
        """Define the homekit characteristics the entity is tracking."""
        return [CharacteristicsTypes.RELATIVE_HUMIDITY_CURRENT]

    @property
    def device_class(self) -> str:
        """Return the device class of the sensor."""
        return DEVICE_CLASS_HUMIDITY

    @property
    def name(self):
        """Return the name of the device."""
        return f"{super().name} Humidity"

    @property
    def icon(self):
        """Return the sensor icon."""
        return HUMIDITY_ICON

    @property
    def unit_of_measurement(self):
        """Return units for the sensor."""
        return PERCENTAGE

    @property
    def state(self):
        """Return the current humidity."""
        return self.service.value(CharacteristicsTypes.RELATIVE_HUMIDITY_CURRENT)


class HomeKitTemperatureSensor(HomeKitEntity):
    """Representation of a Homekit temperature sensor."""

    def get_characteristic_types(self):
        """Define the homekit characteristics the entity is tracking."""
        return [CharacteristicsTypes.TEMPERATURE_CURRENT]

    @property
    def device_class(self) -> str:
        """Return the device class of the sensor."""
        return DEVICE_CLASS_TEMPERATURE

    @property
    def name(self):
        """Return the name of the device."""
        return f"{super().name} Temperature"

    @property
    def icon(self):
        """Return the sensor icon."""
        return TEMP_C_ICON

    @property
    def unit_of_measurement(self):
        """Return units for the sensor."""
        return TEMP_CELSIUS

    @property
    def state(self):
        """Return the current temperature in Celsius."""
        return self.service.value(CharacteristicsTypes.TEMPERATURE_CURRENT)


class HomeKitLightSensor(HomeKitEntity):
    """Representation of a Homekit light level sensor."""

    def get_characteristic_types(self):
        """Define the homekit characteristics the entity is tracking."""
        return [CharacteristicsTypes.LIGHT_LEVEL_CURRENT]

    @property
    def device_class(self) -> str:
        """Return the device class of the sensor."""
        return DEVICE_CLASS_ILLUMINANCE

    @property
    def name(self):
        """Return the name of the device."""
        return f"{super().name} Light Level"

    @property
    def icon(self):
        """Return the sensor icon."""
        return BRIGHTNESS_ICON

    @property
    def unit_of_measurement(self):
        """Return units for the sensor."""
        return LIGHT_LUX

    @property
    def state(self):
        """Return the current light level in lux."""
        return self.service.value(CharacteristicsTypes.LIGHT_LEVEL_CURRENT)


class HomeKitCarbonDioxideSensor(HomeKitEntity):
    """Representation of a Homekit Carbon Dioxide sensor."""

    def get_characteristic_types(self):
        """Define the homekit characteristics the entity is tracking."""
        return [CharacteristicsTypes.CARBON_DIOXIDE_LEVEL]

    @property
    def name(self):
        """Return the name of the device."""
        return f"{super().name} CO2"

    @property
    def icon(self):
        """Return the sensor icon."""
        return CO2_ICON

    @property
    def unit_of_measurement(self):
        """Return units for the sensor."""
        return CONCENTRATION_PARTS_PER_MILLION

    @property
    def state(self):
        """Return the current CO2 level in ppm."""
        return self.service.value(CharacteristicsTypes.CARBON_DIOXIDE_LEVEL)


class HomeKitBatterySensor(HomeKitEntity):
    """Representation of a Homekit battery sensor."""

    def get_characteristic_types(self):
        """Define the homekit characteristics the entity is tracking."""
        return [
            CharacteristicsTypes.BATTERY_LEVEL,
            CharacteristicsTypes.STATUS_LO_BATT,
            CharacteristicsTypes.CHARGING_STATE,
        ]

    @property
    def device_class(self) -> str:
        """Return the device class of the sensor."""
        return DEVICE_CLASS_BATTERY

    @property
    def name(self):
        """Return the name of the device."""
        return f"{super().name} Battery"

    @property
    def icon(self):
        """Return the sensor icon."""
        if not self.available or self.state is None:
            return "mdi:battery-unknown"

        # This is similar to the logic in helpers.icon, but we have delegated the
        # decision about what mdi:battery-alert is to the device.
        icon = "mdi:battery"
        if self.is_charging and self.state > 10:
            percentage = int(round(self.state / 20 - 0.01)) * 20
            icon += f"-charging-{percentage}"
        elif self.is_charging:
            icon += "-outline"
        elif self.is_low_battery:
            icon += "-alert"
        elif self.state < 95:
            percentage = max(int(round(self.state / 10 - 0.01)) * 10, 10)
            icon += f"-{percentage}"

        return icon

    @property
    def unit_of_measurement(self):
        """Return units for the sensor."""
        return PERCENTAGE

    @property
    def is_low_battery(self):
        """Return true if battery level is low."""
        return self.service.value(CharacteristicsTypes.STATUS_LO_BATT) == 1

    @property
    def is_charging(self):
        """Return true if currently charing."""
        # 0 = not charging
        # 1 = charging
        # 2 = not chargeable
        return self.service.value(CharacteristicsTypes.CHARGING_STATE) == 1

    @property
    def state(self):
        """Return the current battery level percentage."""
        return self.service.value(CharacteristicsTypes.BATTERY_LEVEL)


class SimpleSensor(CharacteristicEntity):
    """
    A simple sensor for a single characteristic.

    This may be an additional secondary entity that is part of another service. An
    example is a switch that has an energy sensor.

    These *have* to have a different unique_id to the normal sensors as there could
    be multiple entities per HomeKit service (this was not previously the case).
    """

    def __init__(
        self,
        conn,
        info,
        char,
        device_class=None,
        unit=None,
        icon=None,
        name=None,
    ):
        """Initialise a secondary HomeKit characteristic sensor."""
        self._device_class = device_class
        self._unit = unit
        self._icon = icon
        self._name = name
        self._char = char

        super().__init__(conn, info)

    def get_characteristic_types(self):
        """Define the homekit characteristics the entity is tracking."""
        return [self._char.type]

    @property
    def device_class(self):
        """Return units for the sensor."""
        return self._device_class

    @property
    def unit_of_measurement(self):
        """Return units for the sensor."""
        return self._unit

    @property
    def icon(self):
        """Return the sensor icon."""
        return self._icon

    @property
    def name(self) -> str:
        """Return the name of the device if any."""
        return f"{super().name} - {self._name}"

    @property
    def state(self):
        """Return the current sensor value."""
        return self._char.value


ENTITY_TYPES = {
    ServicesTypes.HUMIDITY_SENSOR: HomeKitHumiditySensor,
    ServicesTypes.TEMPERATURE_SENSOR: HomeKitTemperatureSensor,
    ServicesTypes.LIGHT_SENSOR: HomeKitLightSensor,
    ServicesTypes.CARBON_DIOXIDE_SENSOR: HomeKitCarbonDioxideSensor,
    ServicesTypes.BATTERY_SERVICE: HomeKitBatterySensor,
}


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up Homekit sensors."""
    hkid = config_entry.data["AccessoryPairingID"]
    conn = opp.data[KNOWN_DEVICES][hkid]

    @callback
    def async_add_service(service):
        entity_class = ENTITY_TYPES.get(service.short_type)
        if not entity_class:
            return False
        info = {"aid": service.accessory.aid, "iid": service.iid}
        async_add_entities([entity_class(conn, info)], True)
        return True

    conn.add_listener(async_add_service)

    @callback
    def async_add_characteristic(char):
        kwargs = SIMPLE_SENSOR.get(char.type)
        if not kwargs:
            return False
        info = {"aid": char.service.accessory.aid, "iid": char.service.iid}
        async_add_entities([SimpleSensor(conn, info, char, **kwargs)], True)

        return True

    conn.add_char_factory(async_add_characteristic)
