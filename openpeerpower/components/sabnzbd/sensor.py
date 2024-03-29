"""Support for monitoring an SABnzbd NZB client."""
from openpeerpower.components.sensor import SensorEntity
from openpeerpower.helpers.dispatcher import async_dispatcher_connect

from . import DATA_SABNZBD, SENSOR_TYPES, SIGNAL_SABNZBD_UPDATED


async def async_setup_platform(opp, config, async_add_entities, discovery_info=None):
    """Set up the SABnzbd sensors."""
    if discovery_info is None:
        return

    sab_api_data = opp.data[DATA_SABNZBD]
    sensors = sab_api_data.sensors
    client_name = sab_api_data.name
    async_add_entities(
        [SabnzbdSensor(sensor, sab_api_data, client_name) for sensor in sensors]
    )


class SabnzbdSensor(SensorEntity):
    """Representation of an SABnzbd sensor."""

    def __init__(self, sensor_type, sabnzbd_api_data, client_name):
        """Initialize the sensor."""
        self._client_name = client_name
        self._field_name = SENSOR_TYPES[sensor_type][2]
        self._name = SENSOR_TYPES[sensor_type][0]
        self._sabnzbd_api = sabnzbd_api_data
        self._state = None
        self._type = sensor_type
        self._unit_of_measurement = SENSOR_TYPES[sensor_type][1]

    async def async_added_to_opp(self):
        """Call when entity about to be added to opp."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.opp, SIGNAL_SABNZBD_UPDATED, self.update_state
            )
        )

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._client_name} {self._name}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def should_poll(self):
        """Don't poll. Will be updated by dispatcher signal."""
        return False

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    def update_state(self, args):
        """Get the latest data and updates the states."""
        self._state = self._sabnzbd_api.get_queue_field(self._field_name)

        if self._type == "speed":
            self._state = round(float(self._state) / 1024, 1)
        elif "size" in self._type:
            self._state = round(float(self._state), 2)

        self.schedule_update_op_state()
