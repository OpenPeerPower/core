"""Provides a binary sensor which gets its values from a TCP socket."""
from __future__ import annotations

from typing import Any, Final

from openpeerpower.components.binary_sensor import (
    PLATFORM_SCHEMA as PARENT_PLATFORM_SCHEMA,
    BinarySensorEntity,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.entity_platform import AddEntitiesCallback
from openpeerpower.helpers.typing import ConfigType

from .common import TCP_PLATFORM_SCHEMA, TcpEntity
from .const import CONF_VALUE_ON

PLATFORM_SCHEMA: Final = PARENT_PLATFORM_SCHEMA.extend(TCP_PLATFORM_SCHEMA)


def setup_platform(
    opp: OpenPeerPower,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: dict[str, Any] | None = None,
) -> None:
    """Set up the TCP binary sensor."""
    add_entities([TcpBinarySensor(opp, config)])


class TcpBinarySensor(TcpEntity, BinarySensorEntity):
    """A binary sensor which is on when its state == CONF_VALUE_ON."""

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self._state == self._config[CONF_VALUE_ON]
