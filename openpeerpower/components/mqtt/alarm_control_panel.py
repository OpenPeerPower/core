"""This platform enables the possibility to control a MQTT alarm."""
import functools
import logging
import re

import voluptuous as vol

import openpeerpower.components.alarm_control_panel as alarm
from openpeerpower.components.alarm_control_panel.const import (
    SUPPORT_ALARM_ARM_AWAY,
    SUPPORT_ALARM_ARM_CUSTOM_BYPASS,
    SUPPORT_ALARM_ARM_HOME,
    SUPPORT_ALARM_ARM_NIGHT,
)
from openpeerpower.const import (
    CONF_CODE,
    CONF_DEVICE,
    CONF_NAME,
    CONF_UNIQUE_ID,
    CONF_VALUE_TEMPLATE,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_CUSTOM_BYPASS,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMING,
    STATE_ALARM_DISARMED,
    STATE_ALARM_DISARMING,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
)
from openpeerpower.core import callback
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.reload import async_setup_reload_service
from openpeerpower.helpers.typing import ConfigType, OpenPeerPowerType

from . import (
    CONF_COMMAND_TOPIC,
    CONF_QOS,
    CONF_RETAIN,
    CONF_STATE_TOPIC,
    DOMAIN,
    PLATFORMS,
    subscription,
)
from .. import mqtt
from .debug_info import log_messages
from .mixins import (
    MQTT_AVAILABILITY_SCHEMA,
    MQTT_ENTITY_DEVICE_INFO_SCHEMA,
    MQTT_JSON_ATTRS_SCHEMA,
    MqttEntity,
    async_setup_entry_helper,
)

_LOGGER = logging.getLogger(__name__)

CONF_CODE_ARM_REQUIRED = "code_arm_required"
CONF_CODE_DISARM_REQUIRED = "code_disarm_required"
CONF_PAYLOAD_DISARM = "payload_disarm"
CONF_PAYLOAD_ARM_HOME = "payload_arm_home"
CONF_PAYLOAD_ARM_AWAY = "payload_arm_away"
CONF_PAYLOAD_ARM_NIGHT = "payload_arm_night"
CONF_PAYLOAD_ARM_CUSTOM_BYPASS = "payload_arm_custom_bypass"
CONF_COMMAND_TEMPLATE = "command_template"

DEFAULT_COMMAND_TEMPLATE = "{{action}}"
DEFAULT_ARM_NIGHT = "ARM_NIGHT"
DEFAULT_ARM_AWAY = "ARM_AWAY"
DEFAULT_ARM_HOME = "ARM_HOME"
DEFAULT_ARM_CUSTOM_BYPASS = "ARM_CUSTOM_BYPASS"
DEFAULT_DISARM = "DISARM"
DEFAULT_NAME = "MQTT Alarm"
PLATFORM_SCHEMA = (
    mqtt.MQTT_BASE_PLATFORM_SCHEMA.extend(
        {
            vol.Optional(CONF_CODE): cv.string,
            vol.Optional(CONF_CODE_ARM_REQUIRED, default=True): cv.boolean,
            vol.Optional(CONF_CODE_DISARM_REQUIRED, default=True): cv.boolean,
            vol.Optional(
                CONF_COMMAND_TEMPLATE, default=DEFAULT_COMMAND_TEMPLATE
            ): cv.template,
            vol.Required(CONF_COMMAND_TOPIC): mqtt.valid_publish_topic,
            vol.Optional(CONF_DEVICE): MQTT_ENTITY_DEVICE_INFO_SCHEMA,
            vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
            vol.Optional(CONF_PAYLOAD_ARM_AWAY, default=DEFAULT_ARM_AWAY): cv.string,
            vol.Optional(CONF_PAYLOAD_ARM_HOME, default=DEFAULT_ARM_HOME): cv.string,
            vol.Optional(CONF_PAYLOAD_ARM_NIGHT, default=DEFAULT_ARM_NIGHT): cv.string,
            vol.Optional(
                CONF_PAYLOAD_ARM_CUSTOM_BYPASS, default=DEFAULT_ARM_CUSTOM_BYPASS
            ): cv.string,
            vol.Optional(CONF_PAYLOAD_DISARM, default=DEFAULT_DISARM): cv.string,
            vol.Optional(CONF_RETAIN, default=mqtt.DEFAULT_RETAIN): cv.boolean,
            vol.Required(CONF_STATE_TOPIC): mqtt.valid_subscribe_topic,
            vol.Optional(CONF_UNIQUE_ID): cv.string,
            vol.Optional(CONF_VALUE_TEMPLATE): cv.template,
        }
    )
    .extend(MQTT_AVAILABILITY_SCHEMA.schema)
    .extend(MQTT_JSON_ATTRS_SCHEMA.schema)
)


async def async_setup_platform(
    opp: OpenPeerPowerType, config: ConfigType, async_add_entities, discovery_info=None
):
    """Set up MQTT alarm control panel through configuration.yaml."""
    await async_setup_reload_service(opp, DOMAIN, PLATFORMS)
    await _async_setup_entity(opp, async_add_entities, config)


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up MQTT alarm control panel dynamically through MQTT discovery."""
    setup = functools.partial(
        _async_setup_entity, opp, async_add_entities, config_entry=config_entry
    )
    await async_setup_entry_helper(opp, alarm.DOMAIN, setup, PLATFORM_SCHEMA)


async def _async_setup_entity(
    opp, async_add_entities, config, config_entry=None, discovery_data=None
):
    """Set up the MQTT Alarm Control Panel platform."""
    async_add_entities([MqttAlarm(opp, config, config_entry, discovery_data)])


class MqttAlarm(MqttEntity, alarm.AlarmControlPanelEntity):
    """Representation of a MQTT alarm status."""

    def __init__(self, opp, config, config_entry, discovery_data):
        """Init the MQTT Alarm Control Panel."""
        self._state = None

        MqttEntity.__init__(self, opp, config, config_entry, discovery_data)

    @staticmethod
    def config_schema():
        """Return the config schema."""
        return PLATFORM_SCHEMA

    def _setup_from_config(self, config):
        self._config = config
        value_template = self._config.get(CONF_VALUE_TEMPLATE)
        if value_template is not None:
            value_template.opp = self.opp
        command_template = self._config[CONF_COMMAND_TEMPLATE]
        command_template.opp = self.opp

    async def _subscribe_topics(self):
        """(Re)Subscribe to topics."""

        @callback
        @log_messages(self.opp, self.entity_id)
        def message_received(msg):
            """Run when new MQTT message has been received."""
            payload = msg.payload
            value_template = self._config.get(CONF_VALUE_TEMPLATE)
            if value_template is not None:
                payload = value_template.async_render_with_possible_json_value(
                    msg.payload, self._state
                )
            if payload not in (
                STATE_ALARM_DISARMED,
                STATE_ALARM_ARMED_HOME,
                STATE_ALARM_ARMED_AWAY,
                STATE_ALARM_ARMED_NIGHT,
                STATE_ALARM_ARMED_CUSTOM_BYPASS,
                STATE_ALARM_PENDING,
                STATE_ALARM_ARMING,
                STATE_ALARM_DISARMING,
                STATE_ALARM_TRIGGERED,
            ):
                _LOGGER.warning("Received unexpected payload: %s", msg.payload)
                return
            self._state = payload
            self.async_write_op_state()

        self._sub_state = await subscription.async_subscribe_topics(
            self.opp,
            self._sub_state,
            {
                "state_topic": {
                    "topic": self._config[CONF_STATE_TOPIC],
                    "msg_callback": message_received,
                    "qos": self._config[CONF_QOS],
                }
            },
        )

    @property
    def name(self):
        """Return the name of the device."""
        return self._config[CONF_NAME]

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return (
            SUPPORT_ALARM_ARM_HOME
            | SUPPORT_ALARM_ARM_AWAY
            | SUPPORT_ALARM_ARM_NIGHT
            | SUPPORT_ALARM_ARM_CUSTOM_BYPASS
        )

    @property
    def code_format(self):
        """Return one or more digits/characters."""
        code = self._config.get(CONF_CODE)
        if code is None:
            return None
        if isinstance(code, str) and re.search("^\\d+$", code):
            return alarm.FORMAT_NUMBER
        return alarm.FORMAT_TEXT

    @property
    def code_arm_required(self):
        """Whether the code is required for arm actions."""
        code_required = self._config.get(CONF_CODE_ARM_REQUIRED)
        return code_required

    async def async_alarm_disarm(self, code=None):
        """Send disarm command.

        This method is a coroutine.
        """
        code_required = self._config[CONF_CODE_DISARM_REQUIRED]
        if code_required and not self._validate_code(code, "disarming"):
            return
        payload = self._config[CONF_PAYLOAD_DISARM]
        self._publish(code, payload)

    async def async_alarm_arm_home(self, code=None):
        """Send arm home command.

        This method is a coroutine.
        """
        code_required = self._config[CONF_CODE_ARM_REQUIRED]
        if code_required and not self._validate_code(code, "arming home"):
            return
        action = self._config[CONF_PAYLOAD_ARM_HOME]
        self._publish(code, action)

    async def async_alarm_arm_away(self, code=None):
        """Send arm away command.

        This method is a coroutine.
        """
        code_required = self._config[CONF_CODE_ARM_REQUIRED]
        if code_required and not self._validate_code(code, "arming away"):
            return
        action = self._config[CONF_PAYLOAD_ARM_AWAY]
        self._publish(code, action)

    async def async_alarm_arm_night(self, code=None):
        """Send arm night command.

        This method is a coroutine.
        """
        code_required = self._config[CONF_CODE_ARM_REQUIRED]
        if code_required and not self._validate_code(code, "arming night"):
            return
        action = self._config[CONF_PAYLOAD_ARM_NIGHT]
        self._publish(code, action)

    async def async_alarm_arm_custom_bypass(self, code=None):
        """Send arm custom bypass command.

        This method is a coroutine.
        """
        code_required = self._config[CONF_CODE_ARM_REQUIRED]
        if code_required and not self._validate_code(code, "arming custom bypass"):
            return
        action = self._config[CONF_PAYLOAD_ARM_CUSTOM_BYPASS]
        self._publish(code, action)

    def _publish(self, code, action):
        """Publish via mqtt."""
        command_template = self._config[CONF_COMMAND_TEMPLATE]
        values = {"action": action, "code": code}
        payload = command_template.async_render(**values, parse_result=False)
        mqtt.async_publish(
            self.opp,
            self._config[CONF_COMMAND_TOPIC],
            payload,
            self._config[CONF_QOS],
            self._config[CONF_RETAIN],
        )

    def _validate_code(self, code, state):
        """Validate given code."""
        conf_code = self._config.get(CONF_CODE)
        check = conf_code is None or code == conf_code
        if not check:
            _LOGGER.warning("Wrong code entered for %s", state)
        return check
