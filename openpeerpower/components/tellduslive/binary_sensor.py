"""Support for binary sensors using Tellstick Net."""
from openpeerpower.components import binary_sensor, tellduslive
from openpeerpower.components.binary_sensor import BinarySensorEntity
from openpeerpower.helpers.dispatcher import async_dispatcher_connect

from .entry import TelldusLiveEntity


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up tellduslive sensors dynamically."""

    async def async_discover_binary_sensor(device_id):
        """Discover and add a discovered sensor."""
        client = opp.data[tellduslive.DOMAIN]
        async_add_entities([TelldusLiveSensor(client, device_id)])

    async_dispatcher_connect(
        opp,
        tellduslive.TELLDUS_DISCOVERY_NEW.format(
            binary_sensor.DOMAIN, tellduslive.DOMAIN
        ),
        async_discover_binary_sensor,
    )


class TelldusLiveSensor(TelldusLiveEntity, BinarySensorEntity):
    """Representation of a Tellstick sensor."""

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self.device.is_on
