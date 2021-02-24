"""Platform to retrieve Islamic prayer times information for Open Peer Power."""

from openpeerpower.const import DEVICE_CLASS_TIMESTAMP
from openpeerpower.helpers.dispatcher import async_dispatcher_connect
from openpeerpower.helpers.entity import Entity
import openpeerpower.util.dt as dt_util

from .const import DATA_UPDATED, DOMAIN, PRAYER_TIMES_ICON, SENSOR_TYPES


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up the Islamic prayer times sensor platform."""

    client = opp.data[DOMAIN]

    entities = []
    for sensor_type in SENSOR_TYPES:
        entities.append(IslamicPrayerTimeSensor(sensor_type, client))

    async_add_entities(entities, True)


class IslamicPrayerTimeSensor(Entity):
    """Representation of an Islamic prayer time sensor."""

    def __init__(self, sensor_type, client):
        """Initialize the Islamic prayer time sensor."""
        self.sensor_type = sensor_type
        self.client = client

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self.sensor_type} {SENSOR_TYPES[self.sensor_type]}"

    @property
    def unique_id(self):
        """Return the unique id of the entity."""
        return self.sensor_type

    @property
    def icon(self):
        """Icon to display in the front end."""
        return PRAYER_TIMES_ICON

    @property
    def state(self):
        """Return the state of the sensor."""
        return (
            self.client.prayer_times_info.get(self.sensor_type)
            .astimezone(dt_util.UTC)
            .isoformat()
        )

    @property
    def should_poll(self):
        """Disable polling."""
        return False

    @property
    def device_class(self):
        """Return the device class."""
        return DEVICE_CLASS_TIMESTAMP

    async def async_added_to_opp(self):
        """Handle entity which will be added."""
        self.async_on_remove(
            async_dispatcher_connect(self.opp, DATA_UPDATED, self.async_write_op_state)
        )
