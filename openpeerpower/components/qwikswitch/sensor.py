"""Support for Qwikswitch Sensors."""
import logging

from pyqwikswitch.qwikswitch import SENSORS

from openpeerpower.components.sensor import SensorEntity
from openpeerpower.core import callback

from . import DOMAIN as QWIKSWITCH, QSEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(opp, _, add_entities, discovery_info=None):
    """Add sensor from the main Qwikswitch component."""
    if discovery_info is None:
        return

    qsusb = opp.data[QWIKSWITCH]
    _LOGGER.debug("Setup qwikswitch.sensor %s, %s", qsusb, discovery_info)
    devs = [QSSensor(sensor) for sensor in discovery_info[QWIKSWITCH]]
    add_entities(devs)


class QSSensor(QSEntity, SensorEntity):
    """Sensor based on a Qwikswitch relay/dimmer module."""

    _val = None

    def __init__(self, sensor):
        """Initialize the sensor."""

        super().__init__(sensor["id"], sensor["name"])
        self.channel = sensor["channel"]
        sensor_type = sensor["type"]

        self._decode, self.unit = SENSORS[sensor_type]
        # this cannot happen because it only happens in bool and this should be redirected to binary_sensor
        assert not isinstance(
            self.unit, type
        ), f"boolean sensor id={sensor['id']} name={sensor['name']}"

    @callback
    def update_packet(self, packet):
        """Receive update packet from QSUSB."""
        val = self._decode(packet, channel=self.channel)
        _LOGGER.debug(
            "Update %s (%s:%s) decoded as %s: %s",
            self.entity_id,
            self.qsid,
            self.channel,
            val,
            packet,
        )
        if val is not None:
            self._val = val
            self.async_write_op_state()

    @property
    def state(self):
        """Return the value of the sensor."""
        return str(self._val)

    @property
    def unique_id(self):
        """Return a unique identifier for this sensor."""
        return f"qs{self.qsid}:{self.channel}"

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self.unit
