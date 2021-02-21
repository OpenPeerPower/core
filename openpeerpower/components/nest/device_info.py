"""Library for extracting device specific information common to entities."""

from google_nest_sdm.device import Device
from google_nest_sdm.device_traits import InfoTrait

from .const import DOMAIN

DEVICE_TYPE_MAP = {
    "sdm.devices.types.CAMERA": "Camera",
    "sdm.devices.types.DISPLAY": "Display",
    "sdm.devices.types.DOORBELL": "Doorbell",
    "sdm.devices.types.THERMOSTAT": "Thermostat",
}


class DeviceInfo:
    """Provide device info from the SDM device, shared across platforms."""

    device_brand = "Google Nest"

    def __init__(self, device: Device):
        """Initialize the DeviceInfo."""
        self._device = device

    @property
    def device_info(self):
        """Return device specific attributes."""
        return {
            # The API "name" field is a unique device identifier.
            "identifiers": {(DOMAIN, self._device.name)},
            "name": self.device_name,
            "manufacturer": self.device_brand,
            "model": self.device_model,
        }

    @property
    def device_name(self):
        """Return the name of the physical device that includes the sensor."""
        if InfoTrait.NAME in self._device.traits:
            trait = self._device.traits[InfoTrait.NAME]
            if trait.custom_name:
                return trait.custom_name
        # Build a name from the room/structure.  Note: This room/structure name
        # is not associated with a open peer power Area.
        parent_relations = self._device.parent_relations
        if parent_relations:
            items = sorted(parent_relations.items())
            names = [name for id, name in items]
            return " ".join(names)
        return self.device_model

    @property
    def device_model(self):
        """Return device model information."""
        # The API intentionally returns minimal information about specific
        # devices, instead relying on traits, but we can infer a generic model
        # name based on the type
        return DEVICE_TYPE_MAP.get(self._device.type)
