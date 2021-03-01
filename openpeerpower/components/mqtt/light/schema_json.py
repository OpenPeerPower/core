"""Support for MQTT JSON lights."""
import json
import logging

import voluptuous as vol

from openpeerpower.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_EFFECT,
    ATTR_FLASH,
    ATTR_HS_COLOR,
    ATTR_TRANSITION,
    ATTR_WHITE_VALUE,
    FLASH_LONG,
    FLASH_SHORT,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    SUPPORT_COLOR_TEMP,
    SUPPORT_EFFECT,
    SUPPORT_FLASH,
    SUPPORT_TRANSITION,
    SUPPORT_WHITE_VALUE,
    LightEntity,
)
from openpeerpower.const import (
    CONF_BRIGHTNESS,
    CONF_COLOR_TEMP,
    CONF_DEVICE,
    CONF_EFFECT,
    CONF_HS,
    CONF_NAME,
    CONF_OPTIMISTIC,
    CONF_RGB,
    CONF_UNIQUE_ID,
    CONF_WHITE_VALUE,
    CONF_XY,
    STATE_ON,
)
from openpeerpower.core import callback
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.restore_state import RestoreEntity
from openpeerpower.helpers.typing import ConfigType
import openpeerpower.util.color as color_util

from .. import CONF_COMMAND_TOPIC, CONF_QOS, CONF_RETAIN, CONF_STATE_TOPIC, subscription
from ... import mqtt
from ..debug_info import log_messages
from ..mixins import (
    MQTT_AVAILABILITY_SCHEMA,
    MQTT_ENTITY_DEVICE_INFO_SCHEMA,
    MQTT_JSON_ATTRS_SCHEMA,
    MqttEntity,
)
from .schema import MQTT_LIGHT_SCHEMA_SCHEMA
from .schema_basic import CONF_BRIGHTNESS_SCALE

_LOGGER = logging.getLogger(__name__)

DOMAIN = "mqtt_json"

DEFAULT_BRIGHTNESS = False
DEFAULT_COLOR_TEMP = False
DEFAULT_EFFECT = False
DEFAULT_FLASH_TIME_LONG = 10
DEFAULT_FLASH_TIME_SHORT = 2
DEFAULT_NAME = "MQTT JSON Light"
DEFAULT_OPTIMISTIC = False
DEFAULT_RGB = False
DEFAULT_WHITE_VALUE = False
DEFAULT_XY = False
DEFAULT_HS = False
DEFAULT_BRIGHTNESS_SCALE = 255

CONF_EFFECT_LIST = "effect_list"

CONF_FLASH_TIME_LONG = "flash_time_long"
CONF_FLASH_TIME_SHORT = "flash_time_short"

CONF_MAX_MIREDS = "max_mireds"
CONF_MIN_MIREDS = "min_mireds"

# Stealing some of these from the base MQTT configs.
PLATFORM_SCHEMA_JSON = (
    mqtt.MQTT_RW_PLATFORM_SCHEMA.extend(
        {
            vol.Optional(CONF_BRIGHTNESS, default=DEFAULT_BRIGHTNESS): cv.boolean,
            vol.Optional(
                CONF_BRIGHTNESS_SCALE, default=DEFAULT_BRIGHTNESS_SCALE
            ): vol.All(vol.Coerce(int), vol.Range(min=1)),
            vol.Optional(CONF_COLOR_TEMP, default=DEFAULT_COLOR_TEMP): cv.boolean,
            vol.Optional(CONF_DEVICE): MQTT_ENTITY_DEVICE_INFO_SCHEMA,
            vol.Optional(CONF_EFFECT, default=DEFAULT_EFFECT): cv.boolean,
            vol.Optional(CONF_EFFECT_LIST): vol.All(cv.ensure_list, [cv.string]),
            vol.Optional(
                CONF_FLASH_TIME_LONG, default=DEFAULT_FLASH_TIME_LONG
            ): cv.positive_int,
            vol.Optional(
                CONF_FLASH_TIME_SHORT, default=DEFAULT_FLASH_TIME_SHORT
            ): cv.positive_int,
            vol.Optional(CONF_HS, default=DEFAULT_HS): cv.boolean,
            vol.Optional(CONF_MAX_MIREDS): cv.positive_int,
            vol.Optional(CONF_MIN_MIREDS): cv.positive_int,
            vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
            vol.Optional(CONF_OPTIMISTIC, default=DEFAULT_OPTIMISTIC): cv.boolean,
            vol.Optional(CONF_QOS, default=mqtt.DEFAULT_QOS): vol.All(
                vol.Coerce(int), vol.In([0, 1, 2])
            ),
            vol.Optional(CONF_RETAIN, default=mqtt.DEFAULT_RETAIN): cv.boolean,
            vol.Optional(CONF_RGB, default=DEFAULT_RGB): cv.boolean,
            vol.Optional(CONF_STATE_TOPIC): mqtt.valid_subscribe_topic,
            vol.Optional(CONF_UNIQUE_ID): cv.string,
            vol.Optional(CONF_WHITE_VALUE, default=DEFAULT_WHITE_VALUE): cv.boolean,
            vol.Optional(CONF_XY, default=DEFAULT_XY): cv.boolean,
        }
    )
    .extend(MQTT_AVAILABILITY_SCHEMA.schema)
    .extend(MQTT_JSON_ATTRS_SCHEMA.schema)
    .extend(MQTT_LIGHT_SCHEMA_SCHEMA.schema)
)


async def async_setup_entity_json(
    opp, config: ConfigType, async_add_entities, config_entry, discovery_data
):
    """Set up a MQTT JSON Light."""
    async_add_entities([MqttLightJson(config, config_entry, discovery_data)])


class MqttLightJson(MqttEntity, LightEntity, RestoreEntity):
    """Representation of a MQTT JSON light."""

    def __init__(self, config, config_entry, discovery_data):
        """Initialize MQTT JSON light."""
        self._state = False
        self._supported_features = 0

        self._topic = None
        self._optimistic = False
        self._brightness = None
        self._color_temp = None
        self._effect = None
        self._hs = None
        self._white_value = None
        self._flash_times = None

        MqttEntity.__init__(self, None, config, config_entry, discovery_data)

    @staticmethod
    def config_schema():
        """Return the config schema."""
        return PLATFORM_SCHEMA_JSON

    def _setup_from_config(self, config):
        """(Re)Setup the entity."""
        self._config = config

        self._topic = {
            key: config.get(key) for key in (CONF_STATE_TOPIC, CONF_COMMAND_TOPIC)
        }
        optimistic = config[CONF_OPTIMISTIC]
        self._optimistic = optimistic or self._topic[CONF_STATE_TOPIC] is None

        self._flash_times = {
            key: config.get(key)
            for key in (CONF_FLASH_TIME_SHORT, CONF_FLASH_TIME_LONG)
        }

        self._supported_features = SUPPORT_TRANSITION | SUPPORT_FLASH
        self._supported_features |= config[CONF_RGB] and SUPPORT_COLOR
        self._supported_features |= config[CONF_BRIGHTNESS] and SUPPORT_BRIGHTNESS
        self._supported_features |= config[CONF_COLOR_TEMP] and SUPPORT_COLOR_TEMP
        self._supported_features |= config[CONF_EFFECT] and SUPPORT_EFFECT
        self._supported_features |= config[CONF_WHITE_VALUE] and SUPPORT_WHITE_VALUE
        self._supported_features |= config[CONF_XY] and SUPPORT_COLOR
        self._supported_features |= config[CONF_HS] and SUPPORT_COLOR

    def _parse_color(self, values):
        try:
            red = int(values["color"]["r"])
            green = int(values["color"]["g"])
            blue = int(values["color"]["b"])

            return color_util.color_RGB_to_hs(red, green, blue)
        except KeyError:
            pass
        except ValueError:
            _LOGGER.warning("Invalid RGB color value received")
            return self._hs

        try:
            x_color = float(values["color"]["x"])
            y_color = float(values["color"]["y"])

            return color_util.color_xy_to_hs(x_color, y_color)
        except KeyError:
            pass
        except ValueError:
            _LOGGER.warning("Invalid XY color value received")
            return self._hs

        try:
            hue = float(values["color"]["h"])
            saturation = float(values["color"]["s"])

            return (hue, saturation)
        except KeyError:
            pass
        except ValueError:
            _LOGGER.warning("Invalid HS color value received")
            return self._hs

        return self._hs

    async def _subscribe_topics(self):
        """(Re)Subscribe to topics."""
        last_state = await self.async_get_last_state()

        @callback
        @log_messages(self.opp, self.entity_id)
        def state_received(msg):
            """Handle new MQTT messages."""
            values = json.loads(msg.payload)

            if values["state"] == "ON":
                self._state = True
            elif values["state"] == "OFF":
                self._state = False

            if self._supported_features and SUPPORT_COLOR and "color" in values:
                if values["color"] is None:
                    self._hs = None
                else:
                    self._hs = self._parse_color(values)

            if self._supported_features and SUPPORT_BRIGHTNESS:
                try:
                    self._brightness = int(
                        values["brightness"]
                        / float(self._config[CONF_BRIGHTNESS_SCALE])
                        * 255
                    )
                except KeyError:
                    pass
                except (TypeError, ValueError):
                    _LOGGER.warning("Invalid brightness value received")

            if self._supported_features and SUPPORT_COLOR_TEMP:
                try:
                    if values["color_temp"] is None:
                        self._color_temp = None
                    else:
                        self._color_temp = int(values["color_temp"])
                except KeyError:
                    pass
                except ValueError:
                    _LOGGER.warning("Invalid color temp value received")

            if self._supported_features and SUPPORT_EFFECT:
                try:
                    self._effect = values["effect"]
                except KeyError:
                    pass

            if self._supported_features and SUPPORT_WHITE_VALUE:
                try:
                    self._white_value = int(values["white_value"])
                except KeyError:
                    pass
                except ValueError:
                    _LOGGER.warning("Invalid white value received")

            self.async_write_op_state()

        if self._topic[CONF_STATE_TOPIC] is not None:
            self._sub_state = await subscription.async_subscribe_topics(
                self.opp,
                self._sub_state,
                {
                    "state_topic": {
                        "topic": self._topic[CONF_STATE_TOPIC],
                        "msg_callback": state_received,
                        "qos": self._config[CONF_QOS],
                    }
                },
            )

        if self._optimistic and last_state:
            self._state = last_state.state == STATE_ON
            if last_state.attributes.get(ATTR_BRIGHTNESS):
                self._brightness = last_state.attributes.get(ATTR_BRIGHTNESS)
            if last_state.attributes.get(ATTR_HS_COLOR):
                self._hs = last_state.attributes.get(ATTR_HS_COLOR)
            if last_state.attributes.get(ATTR_COLOR_TEMP):
                self._color_temp = last_state.attributes.get(ATTR_COLOR_TEMP)
            if last_state.attributes.get(ATTR_EFFECT):
                self._effect = last_state.attributes.get(ATTR_EFFECT)
            if last_state.attributes.get(ATTR_WHITE_VALUE):
                self._white_value = last_state.attributes.get(ATTR_WHITE_VALUE)

    @property
    def brightness(self):
        """Return the brightness of this light between 0..255."""
        return self._brightness

    @property
    def color_temp(self):
        """Return the color temperature in mired."""
        return self._color_temp

    @property
    def min_mireds(self):
        """Return the coldest color_temp that this light supports."""
        return self._config.get(CONF_MIN_MIREDS, super().min_mireds)

    @property
    def max_mireds(self):
        """Return the warmest color_temp that this light supports."""
        return self._config.get(CONF_MAX_MIREDS, super().max_mireds)

    @property
    def effect(self):
        """Return the current effect."""
        return self._effect

    @property
    def effect_list(self):
        """Return the list of supported effects."""
        return self._config.get(CONF_EFFECT_LIST)

    @property
    def hs_color(self):
        """Return the hs color value."""
        return self._hs

    @property
    def white_value(self):
        """Return the white property."""
        return self._white_value

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._config[CONF_NAME]

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    @property
    def assumed_state(self):
        """Return true if we do optimistic updates."""
        return self._optimistic

    @property
    def supported_features(self):
        """Flag supported features."""
        return self._supported_features

    async def async_turn_on(self, **kwargs):
        """Turn the device on.

        This method is a coroutine.
        """
        should_update = False

        message = {"state": "ON"}

        if ATTR_HS_COLOR in kwargs and (
            self._config[CONF_HS] or self._config[CONF_RGB] or self._config[CONF_XY]
        ):
            hs_color = kwargs[ATTR_HS_COLOR]
            message["color"] = {}
            if self._config[CONF_RGB]:
                # If there's a brightness topic set, we don't want to scale the
                # RGB values given using the brightness.
                if self._config[CONF_BRIGHTNESS]:
                    brightness = 255
                else:
                    brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
                rgb = color_util.color_hsv_to_RGB(
                    hs_color[0], hs_color[1], brightness / 255 * 100
                )
                message["color"]["r"] = rgb[0]
                message["color"]["g"] = rgb[1]
                message["color"]["b"] = rgb[2]
            if self._config[CONF_XY]:
                xy_color = color_util.color_hs_to_xy(*kwargs[ATTR_HS_COLOR])
                message["color"]["x"] = xy_color[0]
                message["color"]["y"] = xy_color[1]
            if self._config[CONF_HS]:
                message["color"]["h"] = hs_color[0]
                message["color"]["s"] = hs_color[1]

            if self._optimistic:
                self._hs = kwargs[ATTR_HS_COLOR]
                should_update = True

        if ATTR_FLASH in kwargs:
            flash = kwargs.get(ATTR_FLASH)

            if flash == FLASH_LONG:
                message["flash"] = self._flash_times[CONF_FLASH_TIME_LONG]
            elif flash == FLASH_SHORT:
                message["flash"] = self._flash_times[CONF_FLASH_TIME_SHORT]

        if ATTR_TRANSITION in kwargs:
            message["transition"] = kwargs[ATTR_TRANSITION]

        if ATTR_BRIGHTNESS in kwargs and self._config[CONF_BRIGHTNESS]:
            brightness_normalized = kwargs[ATTR_BRIGHTNESS] / DEFAULT_BRIGHTNESS_SCALE
            brightness_scale = self._config[CONF_BRIGHTNESS_SCALE]
            device_brightness = min(
                round(brightness_normalized * brightness_scale), brightness_scale
            )
            # Make sure the brightness is not rounded down to 0
            device_brightness = max(device_brightness, 1)
            message["brightness"] = device_brightness

            if self._optimistic:
                self._brightness = kwargs[ATTR_BRIGHTNESS]
                should_update = True

        if ATTR_COLOR_TEMP in kwargs:
            message["color_temp"] = int(kwargs[ATTR_COLOR_TEMP])

            if self._optimistic:
                self._color_temp = kwargs[ATTR_COLOR_TEMP]
                should_update = True

        if ATTR_EFFECT in kwargs:
            message["effect"] = kwargs[ATTR_EFFECT]

            if self._optimistic:
                self._effect = kwargs[ATTR_EFFECT]
                should_update = True

        if ATTR_WHITE_VALUE in kwargs:
            message["white_value"] = int(kwargs[ATTR_WHITE_VALUE])

            if self._optimistic:
                self._white_value = kwargs[ATTR_WHITE_VALUE]
                should_update = True

        mqtt.async_publish(
            self.opp,
            self._topic[CONF_COMMAND_TOPIC],
            json.dumps(message),
            self._config[CONF_QOS],
            self._config[CONF_RETAIN],
        )

        if self._optimistic:
            # Optimistically assume that the light has changed state.
            self._state = True
            should_update = True

        if should_update:
            self.async_write_op_state()

    async def async_turn_off(self, **kwargs):
        """Turn the device off.

        This method is a coroutine.
        """
        message = {"state": "OFF"}

        if ATTR_TRANSITION in kwargs:
            message["transition"] = kwargs[ATTR_TRANSITION]

        mqtt.async_publish(
            self.opp,
            self._topic[CONF_COMMAND_TOPIC],
            json.dumps(message),
            self._config[CONF_QOS],
            self._config[CONF_RETAIN],
        )

        if self._optimistic:
            # Optimistically assume that the light has changed state.
            self._state = False
            self.async_write_op_state()
