"""Constants for Daikin."""
from openpeerpower.const import (
    CONF_DEVICE_CLASS,
    CONF_ICON,
    CONF_NAME,
    CONF_TYPE,
    CONF_UNIT_OF_MEASUREMENT,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_TEMPERATURE,
    ENERGY_KILO_WATT_HOUR,
    PERCENTAGE,
    POWER_KILO_WATT,
    TEMP_CELSIUS,
)

DOMAIN = "daikin"

ATTR_TARGET_TEMPERATURE = "target_temperature"
ATTR_INSIDE_TEMPERATURE = "inside_temperature"
ATTR_OUTSIDE_TEMPERATURE = "outside_temperature"
ATTR_TOTAL_POWER = "total_power"
ATTR_COOL_ENERGY = "cool_energy"
ATTR_HEAT_ENERGY = "heat_energy"
ATTR_HUMIDITY = "humidity"
ATTR_TARGET_HUMIDITY = "target_humidity"

ATTR_STATE_ON = "on"
ATTR_STATE_OFF = "off"

SENSOR_TYPE_TEMPERATURE = "temperature"
SENSOR_TYPE_HUMIDITY = "humidity"
SENSOR_TYPE_POWER = "power"
SENSOR_TYPE_ENERGY = "energy"

SENSOR_TYPES = {
    ATTR_INSIDE_TEMPERATURE: {
        CONF_NAME: "Inside Temperature",
        CONF_TYPE: SENSOR_TYPE_TEMPERATURE,
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
    },
    ATTR_OUTSIDE_TEMPERATURE: {
        CONF_NAME: "Outside Temperature",
        CONF_TYPE: SENSOR_TYPE_TEMPERATURE,
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
    },
    ATTR_HUMIDITY: {
        CONF_NAME: "Humidity",
        CONF_TYPE: SENSOR_TYPE_HUMIDITY,
        CONF_DEVICE_CLASS: DEVICE_CLASS_HUMIDITY,
        CONF_UNIT_OF_MEASUREMENT: PERCENTAGE,
    },
    ATTR_TARGET_HUMIDITY: {
        CONF_NAME: "Target Humidity",
        CONF_TYPE: SENSOR_TYPE_HUMIDITY,
        CONF_DEVICE_CLASS: DEVICE_CLASS_HUMIDITY,
        CONF_UNIT_OF_MEASUREMENT: PERCENTAGE,
    },
    ATTR_TOTAL_POWER: {
        CONF_NAME: "Total Power Consumption",
        CONF_TYPE: SENSOR_TYPE_POWER,
        CONF_DEVICE_CLASS: DEVICE_CLASS_POWER,
        CONF_UNIT_OF_MEASUREMENT: POWER_KILO_WATT,
    },
    ATTR_COOL_ENERGY: {
        CONF_NAME: "Cool Energy Consumption",
        CONF_TYPE: SENSOR_TYPE_ENERGY,
        CONF_ICON: "mdi:snowflake",
        CONF_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR,
    },
    ATTR_HEAT_ENERGY: {
        CONF_NAME: "Heat Energy Consumption",
        CONF_TYPE: SENSOR_TYPE_ENERGY,
        CONF_ICON: "mdi:fire",
        CONF_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR,
    },
}

CONF_UUID = "uuid"

KEY_MAC = "mac"
KEY_IP = "ip"

TIMEOUT = 60
