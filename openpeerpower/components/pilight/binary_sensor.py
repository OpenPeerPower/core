"""Support for Pilight binary sensors."""
import datetime

import voluptuous as vol

from openpeerpower.components import pilight
from openpeerpower.components.binary_sensor import PLATFORM_SCHEMA, BinarySensorEntity
from openpeerpower.const import (
    CONF_DISARM_AFTER_TRIGGER,
    CONF_NAME,
    CONF_PAYLOAD,
    CONF_PAYLOAD_OFF,
    CONF_PAYLOAD_ON,
)
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.event import track_point_in_time
from openpeerpower.util import dt as dt_util

CONF_VARIABLE = "variable"
CONF_RESET_DELAY_SEC = "reset_delay_sec"

DEFAULT_NAME = "Pilight Binary Sensor"
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_VARIABLE): cv.string,
        vol.Required(CONF_PAYLOAD): vol.Schema(dict),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_PAYLOAD_ON, default="on"): vol.Any(
            cv.positive_int, cv.small_float, cv.string
        ),
        vol.Optional(CONF_PAYLOAD_OFF, default="off"): vol.Any(
            cv.positive_int, cv.small_float, cv.string
        ),
        vol.Optional(CONF_DISARM_AFTER_TRIGGER, default=False): cv.boolean,
        vol.Optional(CONF_RESET_DELAY_SEC, default=30): cv.positive_int,
    }
)


def setup_platform.opp, config, add_entities, discovery_info=None):
    """Set up Pilight Binary Sensor."""
    disarm = config.get(CONF_DISARM_AFTER_TRIGGER)
    if disarm:
        add_entities(
            [
                PilightTriggerSensor(
                    opp.opp,
                    name=config.get(CONF_NAME),
                    variable=config.get(CONF_VARIABLE),
                    payload=config.get(CONF_PAYLOAD),
                    on_value=config.get(CONF_PAYLOAD_ON),
                    off_value=config.get(CONF_PAYLOAD_OFF),
                    rst_dly_sec=config.get(CONF_RESET_DELAY_SEC),
                )
            ]
        )
    else:
        add_entities(
            [
                PilightBinarySensor(
                    opp.opp,
                    name=config.get(CONF_NAME),
                    variable=config.get(CONF_VARIABLE),
                    payload=config.get(CONF_PAYLOAD),
                    on_value=config.get(CONF_PAYLOAD_ON),
                    off_value=config.get(CONF_PAYLOAD_OFF),
                )
            ]
        )


class PilightBinarySensor(BinarySensorEntity):
    """Representation of a binary sensor that can be updated using Pilight."""

    def __init__(self, opp, name, variable, payload, on_value, off_value):
        """Initialize the sensor."""
        self._state = False
        self.opp = opp
        self._name = name
        self._variable = variable
        self._payload = payload
        self._on_value = on_value
        self._off_value = off_value

        opp.bus.listen(pilight.EVENT, self._handle_code)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return True if the binary sensor is on."""
        return self._state

    def _handle_code(self, call):
        """Handle received code by the pilight-daemon.

        If the code matches the defined payload
        of this sensor the sensor state is changed accordingly.
        """
        # Check if received code matches defined playoad
        # True if payload is contained in received code dict
        payload_ok = True
        for key in self._payload:
            if key not in call.data:
                payload_ok = False
                continue
            if self._payload[key] != call.data[key]:
                payload_ok = False
        # Read out variable if payload ok
        if payload_ok:
            if self._variable not in call.data:
                return
            value = call.data[self._variable]
            self._state = value == self._on_value
            self.schedule_update_op_state()


class PilightTriggerSensor(BinarySensorEntity):
    """Representation of a binary sensor that can be updated using Pilight."""

    def __init__(
        self, opp, name, variable, payload, on_value, off_value, rst_dly_sec=30
    ):
        """Initialize the sensor."""
        self._state = False
        self.opp = opp
        self._name = name
        self._variable = variable
        self._payload = payload
        self._on_value = on_value
        self._off_value = off_value
        self._reset_delay_sec = rst_dly_sec
        self._delay_after = None
        self.opp = opp

        opp.bus.listen(pilight.EVENT, self._handle_code)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return True if the binary sensor is on."""
        return self._state

    def _reset_state(self, call):
        self._state = False
        self._delay_after = None
        self.schedule_update_op_state()

    def _handle_code(self, call):
        """Handle received code by the pilight-daemon.

        If the code matches the defined payload
        of this sensor the sensor state is changed accordingly.
        """
        # Check if received code matches defined payload
        # True if payload is contained in received code dict
        payload_ok = True
        for key in self._payload:
            if key not in call.data:
                payload_ok = False
                continue
            if self._payload[key] != call.data[key]:
                payload_ok = False
        # Read out variable if payload ok
        if payload_ok:
            if self._variable not in call.data:
                return
            value = call.data[self._variable]
            self._state = value == self._on_value
            if self._delay_after is None:
                self._delay_after = dt_util.utcnow() + datetime.timedelta(
                    seconds=self._reset_delay_sec
                )
                track_point_in_time(self.opp, self._reset_state, self._delay_after)
            self.schedule_update_op_state()
