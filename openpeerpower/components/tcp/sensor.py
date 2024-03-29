"""Support for TCP socket based sensors."""
from __future__ import annotations

from typing import Any, Final

from openpeerpower.components.sensor import (
    PLATFORM_SCHEMA as PARENT_PLATFORM_SCHEMA,
    SensorEntity,
)
from openpeerpower.const import CONF_UNIT_OF_MEASUREMENT
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.entity_platform import AddEntitiesCallback
from openpeerpower.helpers.typing import ConfigType, StateType

from .common import TCP_PLATFORM_SCHEMA, TcpEntity

PLATFORM_SCHEMA: Final = PARENT_PLATFORM_SCHEMA.extend(TCP_PLATFORM_SCHEMA)


def setup_platform(
    opp: OpenPeerPower,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: dict[str, Any] | None = None,
) -> None:
    """Set up the TCP Sensor."""
    add_entities([TcpSensor(opp, config)])


class TcpSensor(TcpEntity, SensorEntity):
    """Implementation of a TCP socket based sensor."""

    @property
    def state(self) -> StateType:
        """Return the state of the device."""
        return self._state

    @property
    def unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of this entity."""
        return self._config[CONF_UNIT_OF_MEASUREMENT]
