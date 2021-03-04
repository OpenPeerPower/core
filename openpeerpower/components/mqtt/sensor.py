"""Support for MQTT sensors."""
from datetime import timedelta
import functools
from typing import Optional

import voluptuous as vol

from openpeerpower.components import sensor
from openpeerpower.components.sensor import DEVICE_CLASSES_SCHEMA
from openpeerpower.const import (
    CONF_DEVICE,
    CONF_DEVICE_CLASS,
    CONF_FORCE_UPDATE,
    CONF_ICON,
    CONF_NAME,
    CONF_UNIQUE_ID,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_VALUE_TEMPLATE,
)
from openpeerpower.core import callback
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.entity import Entity
from openpeerpower.helpers.event import async_track_point_in_utc_time
from openpeerpower.helpers.reload import async_setup_reload_service
from openpeerpower.helpers.typing import ConfigType, OpenPeerPowerType
from openpeerpower.util import dt as dt_util

from . import CONF_QOS, CONF_STATE_TOPIC, DOMAIN, PLATFORMS, subscription
from .. import mqtt
from .debug_info import log_messages
from .mixins import (
    MQTT_AVAILABILITY_SCHEMA,
    MQTT_ENTITY_DEVICE_INFO_SCHEMA,
    MQTT_JSON_ATTRS_SCHEMA,
    MqttAvailability,
    MqttEntity,
    async_setup_entry_helper,
)

CONF_EXPIRE_AFTER = "expire_after"

DEFAULT_NAME = "MQTT Sensor"
DEFAULT_FORCE_UPDATE = False
PLATFORM_SCHEMA = (
    mqtt.MQTT_RO_PLATFORM_SCHEMA.extend(
        {
            vol.Optional(CONF_DEVICE): MQTT_ENTITY_DEVICE_INFO_SCHEMA,
            vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
            vol.Optional(CONF_EXPIRE_AFTER): cv.positive_int,
            vol.Optional(CONF_FORCE_UPDATE, default=DEFAULT_FORCE_UPDATE): cv.boolean,
            vol.Optional(CONF_ICON): cv.icon,
            vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
            vol.Optional(CONF_UNIQUE_ID): cv.string,
            vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
        }
    )
    .extend(MQTT_AVAILABILITY_SCHEMA.schema)
    .extend(MQTT_JSON_ATTRS_SCHEMA.schema)
)


async def async_setup_platform(
    opp: OpenPeerPowerType, config: ConfigType, async_add_entities, discovery_info=None
):
    """Set up MQTT sensors through configuration.yaml."""
    await async_setup_reload_service(opp, DOMAIN, PLATFORMS)
    await _async_setup_entity(opp, async_add_entities, config)


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up MQTT sensors dynamically through MQTT discovery."""
    setup = functools.partial(
        _async_setup_entity, opp, async_add_entities, config_entry=config_entry
    )
    await async_setup_entry_helper(opp, sensor.DOMAIN, setup, PLATFORM_SCHEMA)


async def _async_setup_entity(
    opp, async_add_entities, config: ConfigType, config_entry=None, discovery_data=None
):
    """Set up MQTT sensor."""
    async_add_entities([MqttSensor(opp, config, config_entry, discovery_data)])


class MqttSensor(MqttEntity, Entity):
    """Representation of a sensor that can be updated using MQTT."""

    def __init__(self, opp, config, config_entry, discovery_data):
        """Initialize the sensor."""
        self._state = None
        self._expiration_trigger = None

        expire_after = config.get(CONF_EXPIRE_AFTER)
        if expire_after is not None and expire_after > 0:
            self._expired = True
        else:
            self._expired = None

        MqttEntity.__init__(self, opp, config, config_entry, discovery_data)

    @staticmethod
    def config_schema():
        """Return the config schema."""
        return PLATFORM_SCHEMA

    def _setup_from_config(self, config):
        """(Re)Setup the entity."""
        self._config = config
        template = self._config.get(CONF_VALUE_TEMPLATE)
        if template is not None:
            template.opp = self.opp

    async def _subscribe_topics(self):
        """(Re)Subscribe to topics."""

        @callback
        @log_messages(self.opp, self.entity_id)
        def message_received(msg):
            """Handle new MQTT messages."""
            payload = msg.payload
            # auto-expire enabled?
            expire_after = self._config.get(CONF_EXPIRE_AFTER)
            if expire_after is not None and expire_after > 0:
                # When expire_after is set, and we receive a message, assume device is not expired since it has to be to receive the message
                self._expired = False

                # Reset old trigger
                if self._expiration_trigger:
                    self._expiration_trigger()
                    self._expiration_trigger = None

                # Set new trigger
                expiration_at = dt_util.utcnow() + timedelta(seconds=expire_after)

                self._expiration_trigger = async_track_point_in_utc_time(
                    self.opp, self._value_is_expired, expiration_at
                )

            template = self._config.get(CONF_VALUE_TEMPLATE)
            if template is not None:
                payload = template.async_render_with_possible_json_value(
                    payload, self._state
                )
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

    @callback
    def _value_is_expired(self, *_):
        """Triggered when value is expired."""
        self._expiration_trigger = None
        self._expired = True
        self.async_write_op_state()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._config[CONF_NAME]

    @property
    def unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        return self._config.get(CONF_UNIT_OF_MEASUREMENT)

    @property
    def force_update(self):
        """Force update."""
        return self._config[CONF_FORCE_UPDATE]

    @property
    def state(self):
        """Return the state of the entity."""
        return self._state

    @property
    def icon(self):
        """Return the icon."""
        return self._config.get(CONF_ICON)

    @property
    def device_class(self) -> Optional[str]:
        """Return the device class of the sensor."""
        return self._config.get(CONF_DEVICE_CLASS)

    @property
    def available(self) -> bool:
        """Return true if the device is available and value has not expired."""
        expire_after = self._config.get(CONF_EXPIRE_AFTER)
        return MqttAvailability.available.fget(self) and (
            expire_after is None or not self._expired
        )
