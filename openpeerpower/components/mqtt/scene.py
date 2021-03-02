"""Support for MQTT scenes."""
import functools

import voluptuous as vol

from openpeerpower.components import scene
from openpeerpower.components.scene import Scene
from openpeerpower.const import CONF_ICON, CONF_NAME, CONF_PAYLOAD_ON, CONF_UNIQUE_ID
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.reload import async_setup_reload_service
from openpeerpower.helpers.typing import ConfigType, OpenPeerPowerType

from . import CONF_COMMAND_TOPIC, CONF_QOS, CONF_RETAIN, DOMAIN, PLATFORMS
from .. import mqtt
from .mixins import (
    MQTT_AVAILABILITY_SCHEMA,
    MqttAvailability,
    MqttDiscoveryUpdate,
    async_setup_entry_helper,
)

DEFAULT_NAME = "MQTT Scene"
DEFAULT_RETAIN = False

PLATFORM_SCHEMA = mqtt.MQTT_BASE_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_COMMAND_TOPIC): mqtt.valid_publish_topic,
        vol.Optional(CONF_ICON): cv.icon,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_PAYLOAD_ON): cv.string,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Optional(CONF_RETAIN, default=DEFAULT_RETAIN): cv.boolean,
    }
).extend(MQTT_AVAILABILITY_SCHEMA.schema)


async def async_setup_platform(
    opp: OpenPeerPowerType, config: ConfigType, async_add_entities, discovery_info=None
):
    """Set up MQTT scene through configuration.yaml."""
    await async_setup_reload_service(opp, DOMAIN, PLATFORMS)
    await _async_setup_entity(async_add_entities, config)


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up MQTT scene dynamically through MQTT discovery."""
    setup = functools.partial(
        _async_setup_entity, async_add_entities, config_entry=config_entry
    )
    await async_setup_entry_helper(opp, scene.DOMAIN, setup, PLATFORM_SCHEMA)


async def _async_setup_entity(
    async_add_entities, config, config_entry=None, discovery_data=None
):
    """Set up the MQTT scene."""
    async_add_entities([MqttScene(config, config_entry, discovery_data)])


class MqttScene(
    MqttAvailability,
    MqttDiscoveryUpdate,
    Scene,
):
    """Representation of a scene that can be activated using MQTT."""

    def __init__(self, config, config_entry, discovery_data):
        """Initialize the MQTT scene."""
        self._state = False
        self._sub_state = None

        self._unique_id = config.get(CONF_UNIQUE_ID)

        # Load config
        self._setup_from_config(config)

        MqttAvailability.__init__(self, config)
        MqttDiscoveryUpdate.__init__(self, discovery_data, self.discovery_update)

    async def async_added_to_opp(self):
        """Subscribe to MQTT events."""
        await super().async_added_to_opp()

    async def discovery_update(self, discovery_payload):
        """Handle updated discovery message."""
        config = PLATFORM_SCHEMA(discovery_payload)
        self._setup_from_config(config)
        await self.availability_discovery_update(config)
        self.async_write_op_state()

    def _setup_from_config(self, config):
        """(Re)Setup the entity."""
        self._config = config

    async def async_will_remove_from_opp(self):
        """Unsubscribe when removed."""
        await MqttAvailability.async_will_remove_from_opp(self)
        await MqttDiscoveryUpdate.async_will_remove_from_opp(self)

    @property
    def name(self):
        """Return the name of the scene."""
        return self._config[CONF_NAME]

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    def icon(self):
        """Return the icon."""
        return self._config.get(CONF_ICON)

    async def async_activate(self, **kwargs):
        """Activate the scene.

        This method is a coroutine.
        """
        mqtt.async_publish(
            self.opp,
            self._config[CONF_COMMAND_TOPIC],
            self._config[CONF_PAYLOAD_ON],
            self._config[CONF_QOS],
            self._config[CONF_RETAIN],
        )
