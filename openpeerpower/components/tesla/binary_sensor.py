"""Support for Tesla binary sensor."""

from openpeerpower.components.binary_sensor import DEVICE_CLASSES, BinarySensorEntity

from . import DOMAIN as TESLA_DOMAIN, TeslaDevice


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up the Tesla binary_sensors by config_entry."""
    async_add_entities(
        [
            TeslaBinarySensor(
                device,
                opp.data[TESLA_DOMAIN][config_entry.entry_id]["coordinator"],
            )
            for device in opp.data[TESLA_DOMAIN][config_entry.entry_id]["devices"][
                "binary_sensor"
            ]
        ],
        True,
    )


class TeslaBinarySensor(TeslaDevice, BinarySensorEntity):
    """Implement an Tesla binary sensor for parking and charger."""

    @property
    def device_class(self):
        """Return the class of this binary sensor."""
        return (
            self.tesla_device.sensor_type
            if self.tesla_device.sensor_type in DEVICE_CLASSES
            else None
        )

    @property
    def is_on(self):
        """Return the state of the binary sensor."""
        return self.tesla_device.get_value()
