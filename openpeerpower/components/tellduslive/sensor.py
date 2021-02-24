"""Support for Tellstick Net/Telstick Live sensors."""
from openpeerpower.components import sensor, tellduslive
from openpeerpower.const import (
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_ILLUMINANCE,
    DEVICE_CLASS_TEMPERATURE,
    LENGTH_MILLIMETERS,
    LIGHT_LUX,
    PERCENTAGE,
    POWER_WATT,
    PRECIPITATION_MILLIMETERS_PER_HOUR,
    SPEED_METERS_PER_SECOND,
    TEMP_CELSIUS,
    UV_INDEX,
)
from openpeerpower.helpers.dispatcher import async_dispatcher_connect

from .entry import TelldusLiveEntity

SENSOR_TYPE_TEMPERATURE = "temp"
SENSOR_TYPE_HUMIDITY = "humidity"
SENSOR_TYPE_RAINRATE = "rrate"
SENSOR_TYPE_RAINTOTAL = "rtot"
SENSOR_TYPE_WINDDIRECTION = "wdir"
SENSOR_TYPE_WINDAVERAGE = "wavg"
SENSOR_TYPE_WINDGUST = "wgust"
SENSOR_TYPE_UV = "uv"
SENSOR_TYPE_WATT = "watt"
SENSOR_TYPE_LUMINANCE = "lum"
SENSOR_TYPE_DEW_POINT = "dewp"
SENSOR_TYPE_BAROMETRIC_PRESSURE = "barpress"

SENSOR_TYPES = {
    SENSOR_TYPE_TEMPERATURE: [
        "Temperature",
        TEMP_CELSIUS,
        None,
        DEVICE_CLASS_TEMPERATURE,
    ],
    SENSOR_TYPE_HUMIDITY: ["Humidity", PERCENTAGE, None, DEVICE_CLASS_HUMIDITY],
    SENSOR_TYPE_RAINRATE: [
        "Rain rate",
        PRECIPITATION_MILLIMETERS_PER_HOUR,
        "mdi:water",
        None,
    ],
    SENSOR_TYPE_RAINTOTAL: ["Rain total", LENGTH_MILLIMETERS, "mdi:water", None],
    SENSOR_TYPE_WINDDIRECTION: ["Wind direction", "", "", None],
    SENSOR_TYPE_WINDAVERAGE: ["Wind average", SPEED_METERS_PER_SECOND, "", None],
    SENSOR_TYPE_WINDGUST: ["Wind gust", SPEED_METERS_PER_SECOND, "", None],
    SENSOR_TYPE_UV: ["UV", UV_INDEX, "", None],
    SENSOR_TYPE_WATT: ["Power", POWER_WATT, "", None],
    SENSOR_TYPE_LUMINANCE: ["Luminance", LIGHT_LUX, None, DEVICE_CLASS_ILLUMINANCE],
    SENSOR_TYPE_DEW_POINT: ["Dew Point", TEMP_CELSIUS, None, DEVICE_CLASS_TEMPERATURE],
    SENSOR_TYPE_BAROMETRIC_PRESSURE: ["Barometric Pressure", "kPa", "", None],
}


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up tellduslive sensors dynamically."""

    async def async_discover_sensor(device_id):
        """Discover and add a discovered sensor."""
        client = opp.data[tellduslive.DOMAIN]
        async_add_entities([TelldusLiveSensor(client, device_id)])

    async_dispatcher_connect(
        opp,
        tellduslive.TELLDUS_DISCOVERY_NEW.format(sensor.DOMAIN, tellduslive.DOMAIN),
        async_discover_sensor,
    )


class TelldusLiveSensor(TelldusLiveEntity):
    """Representation of a Telldus Live sensor."""

    @property
    def device_id(self):
        """Return id of the device."""
        return self._id[0]

    @property
    def _type(self):
        """Return the type of the sensor."""
        return self._id[1]

    @property
    def _value(self):
        """Return value of the sensor."""
        return self.device.value(*self._id[1:])

    @property
    def _value_as_temperature(self):
        """Return the value as temperature."""
        return round(float(self._value), 1)

    @property
    def _value_as_luminance(self):
        """Return the value as luminance."""
        return round(float(self._value), 1)

    @property
    def _value_as_humidity(self):
        """Return the value as humidity."""
        return int(round(float(self._value)))

    @property
    def name(self):
        """Return the name of the sensor."""
        return "{} {}".format(super().name, self.quantity_name or "").strip()

    @property
    def state(self):
        """Return the state of the sensor."""
        if not self.available:
            return None
        if self._type == SENSOR_TYPE_TEMPERATURE:
            return self._value_as_temperature
        if self._type == SENSOR_TYPE_HUMIDITY:
            return self._value_as_humidity
        if self._type == SENSOR_TYPE_LUMINANCE:
            return self._value_as_luminance
        return self._value

    @property
    def quantity_name(self):
        """Name of quantity."""
        return SENSOR_TYPES[self._type][0] if self._type in SENSOR_TYPES else None

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return SENSOR_TYPES[self._type][1] if self._type in SENSOR_TYPES else None

    @property
    def icon(self):
        """Return the icon."""
        return SENSOR_TYPES[self._type][2] if self._type in SENSOR_TYPES else None

    @property
    def device_class(self):
        """Return the device class."""
        return SENSOR_TYPES[self._type][3] if self._type in SENSOR_TYPES else None

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return "{}-{}-{}".format(*self._id)
