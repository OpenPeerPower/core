"""Sensor platform for Advantage Air integration."""
import voluptuous as vol

from openpeerpower.const import PERCENTAGE
from openpeerpower.helpers import config_validation as cv, entity_platform

from .const import ADVANTAGE_AIR_STATE_OPEN, DOMAIN as ADVANTAGE_AIR_DOMAIN
from .entity import AdvantageAirEntity

ADVANTAGE_AIR_SET_COUNTDOWN_VALUE = "minutes"
ADVANTAGE_AIR_SET_COUNTDOWN_UNIT = "min"
ADVANTAGE_AIR_SERVICE_SET_TIME_TO = "set_time_to"

PARALLEL_UPDATES = 0


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up AdvantageAir sensor platform."""

    instance = opp.data[ADVANTAGE_AIR_DOMAIN][config_entry.entry_id]

    entities = []
    for ac_key, ac_device in instance["coordinator"].data["aircons"].items():
        entities.append(AdvantageAirTimeTo(instance, ac_key, "On"))
        entities.append(AdvantageAirTimeTo(instance, ac_key, "Off"))
        for zone_key, zone in ac_device["zones"].items():
            # Only show damper sensors when zone is in temperature control
            if zone["type"] != 0:
                entities.append(AdvantageAirZoneVent(instance, ac_key, zone_key))
            # Only show wireless signal strength sensors when using wireless sensors
            if zone["rssi"] > 0:
                entities.append(AdvantageAirZoneSignal(instance, ac_key, zone_key))
    async_add_entities(entities)

    platform = entity_platform.current_platform.get()
    platform.async_register_entity_service(
        ADVANTAGE_AIR_SERVICE_SET_TIME_TO,
        {vol.Required("minutes"): cv.positive_int},
        "set_time_to",
    )


class AdvantageAirTimeTo(AdvantageAirEntity):
    """Representation of Advantage Air timer control."""

    def __init__(self, instance, ac_key, action):
        """Initialize the Advantage Air timer control."""
        super().__init__(instance, ac_key)
        self.action = action
        self._time_key = f"countDownTo{self.action}"

    @property
    def name(self):
        """Return the name."""
        return f'{self._ac["name"]} Time To {self.action}'

    @property
    def unique_id(self):
        """Return a unique id."""
        return f'{self.coordinator.data["system"]["rid"]}-{self.ac_key}-timeto{self.action}'

    @property
    def state(self):
        """Return the current value."""
        return self._ac[self._time_key]

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return ADVANTAGE_AIR_SET_COUNTDOWN_UNIT

    @property
    def icon(self):
        """Return a representative icon of the timer."""
        if self._ac[self._time_key] > 0:
            return "mdi:timer-outline"
        return "mdi:timer-off-outline"

    async def set_time_to(self, **kwargs):
        """Set the timer value."""
        value = min(720, max(0, int(kwargs[ADVANTAGE_AIR_SET_COUNTDOWN_VALUE])))
        await self.async_change({self.ac_key: {"info": {self._time_key: value}}})


class AdvantageAirZoneVent(AdvantageAirEntity):
    """Representation of Advantage Air Zone Vent Sensor."""

    @property
    def name(self):
        """Return the name."""
        return f'{self._zone["name"]} Vent'

    @property
    def unique_id(self):
        """Return a unique id."""
        return f'{self.coordinator.data["system"]["rid"]}-{self.ac_key}-{self.zone_key}-vent'

    @property
    def state(self):
        """Return the current value of the air vent."""
        if self._zone["state"] == ADVANTAGE_AIR_STATE_OPEN:
            return self._zone["value"]
        return 0

    @property
    def unit_of_measurement(self):
        """Return the percent sign."""
        return PERCENTAGE

    @property
    def icon(self):
        """Return a representative icon."""
        if self._zone["state"] == ADVANTAGE_AIR_STATE_OPEN:
            return "mdi:fan"
        return "mdi:fan-off"


class AdvantageAirZoneSignal(AdvantageAirEntity):
    """Representation of Advantage Air Zone wireless signal sensor."""

    @property
    def name(self):
        """Return the name."""
        return f'{self._zone["name"]} Signal'

    @property
    def unique_id(self):
        """Return a unique id."""
        return f'{self.coordinator.data["system"]["rid"]}-{self.ac_key}-{self.zone_key}-signal'

    @property
    def state(self):
        """Return the current value of the wireless signal."""
        return self._zone["rssi"]

    @property
    def unit_of_measurement(self):
        """Return the percent sign."""
        return PERCENTAGE

    @property
    def icon(self):
        """Return a representative icon."""
        if self._zone["rssi"] >= 80:
            return "mdi:wifi-strength-4"
        if self._zone["rssi"] >= 60:
            return "mdi:wifi-strength-3"
        if self._zone["rssi"] >= 40:
            return "mdi:wifi-strength-2"
        if self._zone["rssi"] >= 20:
            return "mdi:wifi-strength-1"
        return "mdi:wifi-strength-outline"
