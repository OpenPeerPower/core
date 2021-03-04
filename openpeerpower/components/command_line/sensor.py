"""Allows to configure custom shell commands to turn a value for a sensor."""
from collections.abc import Mapping
from datetime import timedelta
import json
import logging

import voluptuous as vol

from openpeerpower.components.sensor import PLATFORM_SCHEMA
from openpeerpower.const import (
    CONF_COMMAND,
    CONF_NAME,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_VALUE_TEMPLATE,
    STATE_UNKNOWN,
)
from openpeerpower.exceptions import TemplateError
from openpeerpower.helpers import template
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.entity import Entity
from openpeerpower.helpers.reload import setup_reload_service

from . import check_output_or_log
from .const import CONF_COMMAND_TIMEOUT, DEFAULT_TIMEOUT, DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

CONF_JSON_ATTRIBUTES = "json_attributes"

DEFAULT_NAME = "Command Sensor"

SCAN_INTERVAL = timedelta(seconds=60)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_COMMAND): cv.string,
        vol.Optional(CONF_COMMAND_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
        vol.Optional(CONF_JSON_ATTRIBUTES): cv.ensure_list_csv,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
        vol.Optional(CONF_VALUE_TEMPLATE): cv.template,
    }
)


def setup_platform(opp, config, add_entities, discovery_info=None):
    """Set up the Command Sensor."""

    setup_reload_service(opp, DOMAIN, PLATFORMS)

    name = config.get(CONF_NAME)
    command = config.get(CONF_COMMAND)
    unit = config.get(CONF_UNIT_OF_MEASUREMENT)
    value_template = config.get(CONF_VALUE_TEMPLATE)
    command_timeout = config.get(CONF_COMMAND_TIMEOUT)
    if value_template is not None:
        value_template.opp = opp
    json_attributes = config.get(CONF_JSON_ATTRIBUTES)
    data = CommandSensorData(opp, command, command_timeout)

    add_entities(
        [CommandSensor(opp, data, name, unit, value_template, json_attributes)], True
    )


class CommandSensor(Entity):
    """Representation of a sensor that is using shell commands."""

    def __init__(
        self, opp, data, name, unit_of_measurement, value_template, json_attributes
    ):
        """Initialize the sensor."""
        self._opp = opp
        self.data = data
        self._attributes = None
        self._json_attributes = json_attributes
        self._name = name
        self._state = None
        self._unit_of_measurement = unit_of_measurement
        self._value_template = value_template

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._unit_of_measurement

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    def update(self):
        """Get the latest data and updates the state."""
        self.data.update()
        value = self.data.value

        if self._json_attributes:
            self._attributes = {}
            if value:
                try:
                    json_dict = json.loads(value)
                    if isinstance(json_dict, Mapping):
                        self._attributes = {
                            k: json_dict[k]
                            for k in self._json_attributes
                            if k in json_dict
                        }
                    else:
                        _LOGGER.warning("JSON result was not a dictionary")
                except ValueError:
                    _LOGGER.warning("Unable to parse output as JSON: %s", value)
            else:
                _LOGGER.warning("Empty reply found when expecting JSON data")

        if value is None:
            value = STATE_UNKNOWN
        elif self._value_template is not None:
            self._state = self._value_template.render_with_possible_json_value(
                value, STATE_UNKNOWN
            )
        else:
            self._state = value


class CommandSensorData:
    """The class for handling the data retrieval."""

    def __init__(self, opp, command, command_timeout):
        """Initialize the data object."""
        self.value = None
        self.opp = opp
        self.command = command
        self.timeout = command_timeout

    def update(self):
        """Get the latest data with a shell command."""
        command = self.command

        if " " not in command:
            prog = command
            args = None
            args_compiled = None
        else:
            prog, args = command.split(" ", 1)
            args_compiled = template.Template(args, self.opp)

        if args_compiled:
            try:
                args_to_render = {"arguments": args}
                rendered_args = args_compiled.render(args_to_render)
            except TemplateError as ex:
                _LOGGER.exception("Error rendering command template: %s", ex)
                return
        else:
            rendered_args = None

        if rendered_args == args:
            # No template used. default behavior
            pass
        else:
            # Template used. Construct the string used in the shell
            command = f"{prog} {rendered_args}"

        _LOGGER.debug("Running command: %s", command)
        self.value = check_output_or_log(command, self.timeout)
