"""Support for monitoring if a sensor value is below/above a threshold."""
import logging

import voluptuous as vol

from openpeerpower.components.binary_sensor import (
    DEVICE_CLASSES_SCHEMA,
    PLATFORM_SCHEMA,
    BinarySensorEntity,
)
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    CONF_DEVICE_CLASS,
    CONF_ENTITY_ID,
    CONF_NAME,
    STATE_UNKNOWN,
)
from openpeerpower.core import callback
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.event import async_track_state_change_event

_LOGGER = logging.getLogger(__name__)

ATTR_HYSTERESIS = "hysteresis"
ATTR_LOWER = "lower"
ATTR_POSITION = "position"
ATTR_SENSOR_VALUE = "sensor_value"
ATTR_TYPE = "type"
ATTR_UPPER = "upper"

CONF_HYSTERESIS = "hysteresis"
CONF_LOWER = "lower"
CONF_UPPER = "upper"

DEFAULT_NAME = "Threshold"
DEFAULT_HYSTERESIS = 0.0

POSITION_ABOVE = "above"
POSITION_BELOW = "below"
POSITION_IN_RANGE = "in_range"
POSITION_UNKNOWN = "unknown"

TYPE_LOWER = "lower"
TYPE_RANGE = "range"
TYPE_UPPER = "upper"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_HYSTERESIS, default=DEFAULT_HYSTERESIS): vol.Coerce(float),
        vol.Optional(CONF_LOWER): vol.Coerce(float),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_UPPER): vol.Coerce(float),
    }
)


async def async_setup_platform(opp, config, async_add_entities, discovery_info=None):
    """Set up the Threshold sensor."""
    entity_id = config.get(CONF_ENTITY_ID)
    name = config.get(CONF_NAME)
    lower = config.get(CONF_LOWER)
    upper = config.get(CONF_UPPER)
    hysteresis = config.get(CONF_HYSTERESIS)
    device_class = config.get(CONF_DEVICE_CLASS)

    async_add_entities(
        [ThresholdSensor(opp, entity_id, name, lower, upper, hysteresis, device_class)],
    )


class ThresholdSensor(BinarySensorEntity):
    """Representation of a Threshold sensor."""

    def __init__(self, opp, entity_id, name, lower, upper, hysteresis, device_class):
        """Initialize the Threshold sensor."""
        self._opp = opp
        self._entity_id = entity_id
        self._name = name
        self._threshold_lower = lower
        self._threshold_upper = upper
        self._hysteresis = hysteresis
        self._device_class = device_class

        self._state_position = POSITION_UNKNOWN
        self._state = None
        self.sensor_value = None

        @callback
        def async_threshold_sensor_state_listener(event):
            """Handle sensor state changes."""
            new_state = event.data.get("new_state")
            if new_state is None:
                return

            try:
                self.sensor_value = (
                    None if new_state.state == STATE_UNKNOWN else float(new_state.state)
                )
            except (ValueError, TypeError):
                self.sensor_value = None
                _LOGGER.warning("State is not numerical")

            self._update_state()
            self.async_write_op_state()

        async_track_state_change_event(
            opp, [entity_id], async_threshold_sensor_state_listener
        )

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return true if sensor is on."""
        return self._state

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def device_class(self):
        """Return the sensor class of the sensor."""
        return self._device_class

    @property
    def threshold_type(self):
        """Return the type of threshold this sensor represents."""
        if self._threshold_lower is not None and self._threshold_upper is not None:
            return TYPE_RANGE
        if self._threshold_lower is not None:
            return TYPE_LOWER
        if self._threshold_upper is not None:
            return TYPE_UPPER

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            ATTR_ENTITY_ID: self._entity_id,
            ATTR_HYSTERESIS: self._hysteresis,
            ATTR_LOWER: self._threshold_lower,
            ATTR_POSITION: self._state_position,
            ATTR_SENSOR_VALUE: self.sensor_value,
            ATTR_TYPE: self.threshold_type,
            ATTR_UPPER: self._threshold_upper,
        }

    @callback
    def _update_state(self):
        """Update the state."""

        def below(threshold):
            """Determine if the sensor value is below a threshold."""
            return self.sensor_value < (threshold - self._hysteresis)

        def above(threshold):
            """Determine if the sensor value is above a threshold."""
            return self.sensor_value > (threshold + self._hysteresis)

        if self.sensor_value is None:
            self._state_position = POSITION_UNKNOWN
            self._state = False

        elif self.threshold_type == TYPE_LOWER:
            if below(self._threshold_lower):
                self._state_position = POSITION_BELOW
                self._state = True
            elif above(self._threshold_lower):
                self._state_position = POSITION_ABOVE
                self._state = False

        elif self.threshold_type == TYPE_UPPER:
            if above(self._threshold_upper):
                self._state_position = POSITION_ABOVE
                self._state = True
            elif below(self._threshold_upper):
                self._state_position = POSITION_BELOW
                self._state = False

        elif self.threshold_type == TYPE_RANGE:
            if below(self._threshold_lower):
                self._state_position = POSITION_BELOW
                self._state = False
            if above(self._threshold_upper):
                self._state_position = POSITION_ABOVE
                self._state = False
            elif above(self._threshold_lower) and below(self._threshold_upper):
                self._state_position = POSITION_IN_RANGE
                self._state = True
