"""Support for RFXtrx sensors."""
import logging

from RFXtrx import ControlEvent, SensorEvent

from openpeerpower.components.sensor import (
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_SIGNAL_STRENGTH,
    DEVICE_CLASS_TEMPERATURE,
)
from openpeerpower.const import (
    CONF_DEVICES,
    DEVICE_CLASS_CURRENT,
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_PRESSURE,
    DEVICE_CLASS_VOLTAGE,
)
from openpeerpower.core import callback

from . import (
    CONF_DATA_BITS,
    DATA_TYPES,
    RfxtrxEntity,
    connect_auto_add,
    get_device_id,
    get_rfx_object,
)
from .const import ATTR_EVENT

_LOGGER = logging.getLogger(__name__)


def _battery_convert(value):
    """Battery is given as a value between 0 and 9."""
    if value is None:
        return None
    return (value + 1) * 10


def _rssi_convert(value):
    """Rssi is given as dBm value."""
    if value is None:
        return None
    return f"{value*8-120}"


DEVICE_CLASSES = {
    "Barometer": DEVICE_CLASS_PRESSURE,
    "Battery numeric": DEVICE_CLASS_BATTERY,
    "Current Ch. 1": DEVICE_CLASS_CURRENT,
    "Current Ch. 2": DEVICE_CLASS_CURRENT,
    "Current Ch. 3": DEVICE_CLASS_CURRENT,
    "Energy usage": DEVICE_CLASS_POWER,
    "Humidity": DEVICE_CLASS_HUMIDITY,
    "Rssi numeric": DEVICE_CLASS_SIGNAL_STRENGTH,
    "Temperature": DEVICE_CLASS_TEMPERATURE,
    "Total usage": DEVICE_CLASS_ENERGY,
    "Voltage": DEVICE_CLASS_VOLTAGE,
}


CONVERT_FUNCTIONS = {
    "Battery numeric": _battery_convert,
    "Rssi numeric": _rssi_convert,
}


async def async_setup_entry(
    opp,
    config_entry,
    async_add_entities,
):
    """Set up platform."""
    discovery_info = config_entry.data
    data_ids = set()

    def supported(event):
        return isinstance(event, (ControlEvent, SensorEvent))

    entities = []
    for packet_id, entity_info in discovery_info[CONF_DEVICES].items():
        event = get_rfx_object(packet_id)
        if event is None:
            _LOGGER.error("Invalid device: %s", packet_id)
            continue
        if not supported(event):
            continue

        device_id = get_device_id(
            event.device, data_bits=entity_info.get(CONF_DATA_BITS)
        )
        for data_type in set(event.values) & set(DATA_TYPES):
            data_id = (*device_id, data_type)
            if data_id in data_ids:
                continue
            data_ids.add(data_id)

            entity = RfxtrxSensor(event.device, device_id, data_type)
            entities.append(entity)

    async_add_entities(entities)

    @callback
    def sensor_update(event, device_id):
        """Handle sensor updates from the RFXtrx gateway."""
        if not supported(event):
            return

        for data_type in set(event.values) & set(DATA_TYPES):
            data_id = (*device_id, data_type)
            if data_id in data_ids:
                continue
            data_ids.add(data_id)

            _LOGGER.info(
                "Added sensor (Device ID: %s Class: %s Sub: %s, Event: %s)",
                event.device.id_string.lower(),
                event.device.__class__.__name__,
                event.device.subtype,
                "".join(f"{x:02x}" for x in event.data),
            )

            entity = RfxtrxSensor(event.device, device_id, data_type, event=event)
            async_add_entities([entity])

    # Subscribe to main RFXtrx events
    connect_auto_add(opp, discovery_info, sensor_update)


class RfxtrxSensor(RfxtrxEntity):
    """Representation of a RFXtrx sensor."""

    def __init__(self, device, device_id, data_type, event=None):
        """Initialize the sensor."""
        super().__init__(device, device_id, event=event)
        self.data_type = data_type
        self._unit_of_measurement = DATA_TYPES.get(data_type)
        self._name = f"{device.type_string} {device.id_string} {data_type}"
        self._unique_id = "_".join(x for x in (*self._device_id, data_type))

        self._device_class = DEVICE_CLASSES.get(data_type)
        self._convert_fun = CONVERT_FUNCTIONS.get(data_type, lambda x: x)

    async def async_added_to_opp(self):
        """Restore device state."""
        await super().async_added_to_opp()

        if self._event is None:
            old_state = await self.async_get_last_state()
            if old_state is not None:
                event = old_state.attributes.get(ATTR_EVENT)
                if event:
                    self._apply_event(get_rfx_object(event))

    @property
    def state(self):
        """Return the state of the sensor."""
        if not self._event:
            return None
        value = self._event.values.get(self.data_type)
        return self._convert_fun(value)

    @property
    def unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        return self._unit_of_measurement

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def force_update(self) -> bool:
        """We should force updates. Repeated states have meaning."""
        return True

    @property
    def device_class(self):
        """Return a device class for sensor."""
        return self._device_class

    @callback
    def _handle_event(self, event, device_id):
        """Check if event applies to me and update."""
        if device_id != self._device_id:
            return

        if self.data_type not in event.values:
            return

        _LOGGER.debug(
            "Sensor update (Device ID: %s Class: %s Sub: %s)",
            event.device.id_string,
            event.device.__class__.__name__,
            event.device.subtype,
        )

        self._apply_event(event)

        self.async_write_op_state()
