"""Support for ISY994 fans."""
import math
from typing import Callable, Optional

from pyisy.constants import ISY_VALUE_UNKNOWN, PROTO_INSTEON

from openpeerpower.components.fan import DOMAIN as FAN, SUPPORT_SET_SPEED, FanEntity
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.helpers.typing import OpenPeerPowerType
from openpeerpower.util.percentage import (
    int_states_in_range,
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from .const import _LOGGER, DOMAIN as ISY994_DOMAIN, ISY994_NODES, ISY994_PROGRAMS
from .entity import ISYNodeEntity, ISYProgramEntity
from .helpers import migrate_old_unique_ids

SPEED_RANGE = (1, 255)  # off is not included


async def async_setup_entry(
    opp: OpenPeerPowerType,
    entry: ConfigEntry,
    async_add_entities: Callable[[list], None],
) -> bool:
    """Set up the ISY994 fan platform."""
    opp_isy_data = opp.data[ISY994_DOMAIN][entry.entry_id]
    devices = []

    for node in opp_isy_data[ISY994_NODES][FAN]:
        devices.append(ISYFanEntity(node))

    for name, status, actions in opp_isy_data[ISY994_PROGRAMS][FAN]:
        devices.append(ISYFanProgramEntity(name, status, actions))

    await migrate_old_unique_ids(opp, FAN, devices)
    async_add_entities(devices)


class ISYFanEntity(ISYNodeEntity, FanEntity):
    """Representation of an ISY994 fan device."""

    @property
    def percentage(self) -> Optional[int]:
        """Return the current speed percentage."""
        if self._node.status == ISY_VALUE_UNKNOWN:
            return None
        return ranged_value_to_percentage(SPEED_RANGE, self._node.status)

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        if self._node.protocol == PROTO_INSTEON:
            return 3
        return int_states_in_range(SPEED_RANGE)

    @property
    def is_on(self) -> bool:
        """Get if the fan is on."""
        if self._node.status == ISY_VALUE_UNKNOWN:
            return None
        return self._node.status != 0

    def set_percentage(self, percentage: int) -> None:
        """Set node to speed percentage for the ISY994 fan device."""
        if percentage == 0:
            self._node.turn_off()
            return

        isy_speed = math.ceil(percentage_to_ranged_value(SPEED_RANGE, percentage))

        self._node.turn_on(val=isy_speed)

    def turn_on(
        self,
        speed: str = None,
        percentage: int = None,
        preset_mode: str = None,
        **kwargs,
    ) -> None:
        """Send the turn on command to the ISY994 fan device."""
        self.set_percentage(percentage)

    def turn_off(self, **kwargs) -> None:
        """Send the turn off command to the ISY994 fan device."""
        self._node.turn_off()

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return SUPPORT_SET_SPEED


class ISYFanProgramEntity(ISYProgramEntity, FanEntity):
    """Representation of an ISY994 fan program."""

    @property
    def percentage(self) -> Optional[int]:
        """Return the current speed percentage."""
        if self._node.status == ISY_VALUE_UNKNOWN:
            return None
        return ranged_value_to_percentage(SPEED_RANGE, self._node.status)

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        if self._node.protocol == PROTO_INSTEON:
            return 3
        return int_states_in_range(SPEED_RANGE)

    @property
    def is_on(self) -> bool:
        """Get if the fan is on."""
        return self._node.status != 0

    def turn_off(self, **kwargs) -> None:
        """Send the turn on command to ISY994 fan program."""
        if not self._actions.run_then():
            _LOGGER.error("Unable to turn off the fan")

    def turn_on(
        self,
        speed: str = None,
        percentage: int = None,
        preset_mode: str = None,
        **kwargs,
    ) -> None:
        """Send the turn off command to ISY994 fan program."""
        if not self._actions.run_else():
            _LOGGER.error("Unable to turn on the fan")
