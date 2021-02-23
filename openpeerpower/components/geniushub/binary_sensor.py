"""Support for Genius Hub binary_sensor devices."""
from openpeerpower.components.binary_sensor import BinarySensorEntity
from openpeerpower.helpers.typing import ConfigType, OpenPeerPowerType

from . import DOMAIN, GeniusDevice

GH_STATE_ATTR = "outputOnOff"


async def async_setup_platform(
    opp: OpenPeerPowerType, config: ConfigType, async_add_entities, discovery_info=None
) -> None:
    """Set up the Genius Hub sensor entities."""
    if discovery_info is None:
        return

    broker = opp.data[DOMAIN]["broker"]

    switches = [
        GeniusBinarySensor(broker, d, GH_STATE_ATTR)
        for d in broker.client.device_objs
        if GH_STATE_ATTR in d.data["state"]
    ]

    async_add_entities(switches, update_before_add=True)


class GeniusBinarySensor(GeniusDevice, BinarySensorEntity):
    """Representation of a Genius Hub binary_sensor."""

    def __init__(self, broker, device, state_attr) -> None:
        """Initialize the binary sensor."""
        super().__init__(broker, device)

        self._state_attr = state_attr

        if device.type[:21] == "Dual Channel Receiver":
            self._name = f"{device.type[:21]} {device.id}"
        else:
            self._name = f"{device.type} {device.id}"

    @property
    def is_on(self) -> bool:
        """Return the status of the sensor."""
        return self._device.data["state"][self._state_attr]
