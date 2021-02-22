"""Support for Firmata binary sensor input."""

import logging

from openpeerpower.components.binary_sensor import BinarySensorEntity
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_NAME, CONF_PIN
from openpeerpower.core import OpenPeerPower

from .const import CONF_NEGATE_STATE, CONF_PIN_MODE, DOMAIN
from .entity import FirmataPinEntity
from .pin import FirmataBinaryDigitalInput, FirmataPinUsedException

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    opp: OpenPeerPower, config_entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the Firmata binary sensors."""
    new_entities = []

    board =.opp.data[DOMAIN][config_entry.entry_id]
    for binary_sensor in board.binary_sensors:
        pin = binary_sensor[CONF_PIN]
        pin_mode = binary_sensor[CONF_PIN_MODE]
        negate = binary_sensor[CONF_NEGATE_STATE]
        api = FirmataBinaryDigitalInput(board, pin, pin_mode, negate)
        try:
            api.setup()
        except FirmataPinUsedException:
            _LOGGER.error(
                "Could not setup binary sensor on pin %s since pin already in use",
                binary_sensor[CONF_PIN],
            )
            continue
        name = binary_sensor[CONF_NAME]
        binary_sensor_entity = FirmataBinarySensor(api, config_entry, name, pin)
        new_entities.append(binary_sensor_entity)

    if new_entities:
        async_add_entities(new_entities)


class FirmataBinarySensor(FirmataPinEntity, BinarySensorEntity):
    """Representation of a binary sensor on a Firmata board."""

    async def async_added_to.opp(self) -> None:
        """Set up a binary sensor."""
        await self._api.start_pin(self.async_write_ha_state)

    async def async_will_remove_from.opp(self) -> None:
        """Stop reporting a binary sensor."""
        await self._api.stop_pin()

    @property
    def is_on(self) -> bool:
        """Return true if binary sensor is on."""
        return self._api.is_on
