"""Representation of a Hue remote firing events for button presses."""
import logging

from aiohue.sensors import TYPE_ZGP_SWITCH, TYPE_ZLL_ROTARY, TYPE_ZLL_SWITCH

from openpeerpower.const import CONF_EVENT, CONF_ID, CONF_UNIQUE_ID
from openpeerpower.core import callback
from openpeerpower.util import slugify

from .sensor_device import GenericHueDevice

_LOGGER = logging.getLogger(__name__)

CONF_HUE_EVENT = "hue_event"
CONF_LAST_UPDATED = "last_updated"

EVENT_NAME_FORMAT = "{}"


class HueEvent(GenericHueDevice):
    """When you want signals instead of entities.

    Stateless sensors such as remotes are expected to generate an event
    instead of a sensor entity in opp.
    """

    def __init__(self, sensor, name, bridge, primary_sensor=None):
        """Register callback that will be used for signals."""
        super().__init__(sensor, name, bridge, primary_sensor)
        self.device_registry_id = None

        self.event_id = slugify(self.sensor.name)
        # Use the aiohue sensor 'state' dict to detect new remote presses
        self._last_state = dict(self.sensor.state)

        # Register callback in coordinator and add job to remove it on bridge reset.
        self.bridge.reset_jobs.append(
            self.bridge.sensor_manager.coordinator.async_add_listener(
                self.async_update_callback
            )
        )
        _LOGGER.debug("Hue event created: %s", self.event_id)

    @callback
    def async_update_callback(self):
        """Fire the event if reason is that state is updated."""
        if self.sensor.state == self._last_state:
            return

        # Extract the press code as state
        if hasattr(self.sensor, "rotaryevent"):
            state = self.sensor.rotaryevent
        else:
            state = self.sensor.buttonevent

        self._last_state = dict(self.sensor.state)

        # Fire event
        data = {
            CONF_ID: self.event_id,
            CONF_UNIQUE_ID: self.unique_id,
            CONF_EVENT: state,
            CONF_LAST_UPDATED: self.sensor.lastupdated,
        }
        self.bridge.opp.bus.async_fire(CONF_HUE_EVENT, data)

    async def async_update_device_registry(self):
        """Update device registry."""
        device_registry = (
            await self.bridge.opp.helpers.device_registry.async_get_registry()
        )

        entry = device_registry.async_get_or_create(
            config_entry_id=self.bridge.config_entry.entry_id, **self.device_info
        )
        self.device_registry_id = entry.id
        _LOGGER.debug(
            "Event registry with entry_id: %s and device_id: %s",
            self.device_registry_id,
            self.device_id,
        )


EVENT_CONFIG_MAP = {
    TYPE_ZGP_SWITCH: {"name_format": EVENT_NAME_FORMAT, "class": HueEvent},
    TYPE_ZLL_SWITCH: {"name_format": EVENT_NAME_FORMAT, "class": HueEvent},
    TYPE_ZLL_ROTARY: {"name_format": EVENT_NAME_FORMAT, "class": HueEvent},
}
