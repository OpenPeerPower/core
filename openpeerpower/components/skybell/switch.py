"""Switch support for the Skybell HD Doorbell."""
import voluptuous as vol

from openpeerpower.components.switch import PLATFORM_SCHEMA, SwitchEntity
from openpeerpower.const import CONF_ENTITY_NAMESPACE, CONF_MONITORED_CONDITIONS
import openpeerpower.helpers.config_validation as cv

from . import DEFAULT_ENTITY_NAMESPACE, DOMAIN as SKYBELL_DOMAIN, SkybellDevice

# Switch types: Name
SWITCH_TYPES = {
    "do_not_disturb": ["Do Not Disturb"],
    "motion_sensor": ["Motion Sensor"],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(
            CONF_ENTITY_NAMESPACE, default=DEFAULT_ENTITY_NAMESPACE
        ): cv.string,
        vol.Required(CONF_MONITORED_CONDITIONS, default=[]): vol.All(
            cv.ensure_list, [vol.In(SWITCH_TYPES)]
        ),
    }
)


def setup_platform(opp, config, add_entities, discovery_info=None):
    """Set up the platform for a Skybell device."""
    skybell = opp.data.get(SKYBELL_DOMAIN)

    sensors = []
    for switch_type in config.get(CONF_MONITORED_CONDITIONS):
        for device in skybell.get_devices():
            sensors.append(SkybellSwitch(device, switch_type))

    add_entities(sensors, True)


class SkybellSwitch(SkybellDevice, SwitchEntity):
    """A switch implementation for Skybell devices."""

    def __init__(self, device, switch_type):
        """Initialize a light for a Skybell device."""
        super().__init__(device)
        self._switch_type = switch_type
        self._name = "{} {}".format(
            self._device.name, SWITCH_TYPES[self._switch_type][0]
        )

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    def turn_on(self, **kwargs):
        """Turn on the switch."""
        setattr(self._device, self._switch_type, True)

    def turn_off(self, **kwargs):
        """Turn off the switch."""
        setattr(self._device, self._switch_type, False)

    @property
    def is_on(self):
        """Return true if device is on."""
        return getattr(self._device, self._switch_type)
