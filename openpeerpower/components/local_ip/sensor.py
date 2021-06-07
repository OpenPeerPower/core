"""Sensor platform for local_ip."""

from openpeerpower.components.sensor import SensorEntity
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_NAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.entity_platform import AddEntitiesCallback
from openpeerpower.util import get_local_ip

from .const import DOMAIN, SENSOR


async def async_setup_entry(
    opp: OpenPeerPower,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the platform from config_entry."""
    name = entry.data.get(CONF_NAME) or DOMAIN
    async_add_entities([IPSensor(name)], True)


class IPSensor(SensorEntity):
    """A simple sensor."""

    _attr_unique_id = SENSOR
    _attr_icon = "mdi:ip"

    def __init__(self, name: str) -> None:
        """Initialize the sensor."""
        self._attr_name = name

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        self._attr_state = get_local_ip()
