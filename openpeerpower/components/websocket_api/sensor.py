"""Entity to track connections to websocket API."""
from __future__ import annotations

from typing import Any

from openpeerpower.components.sensor import SensorEntity
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers.entity_platform import AddEntitiesCallback
from openpeerpower.helpers.typing import ConfigType

from .const import (
    DATA_CONNECTIONS,
    SIGNAL_WEBSOCKET_CONNECTED,
    SIGNAL_WEBSOCKET_DISCONNECTED,
)


async def async_setup_platform(
    opp: OpenPeerPower,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict[str, Any] | None = None,
) -> None:
    """Set up the API streams platform."""
    entity = APICount()

    async_add_entities([entity])


class APICount(SensorEntity):
    """Entity to represent how many people are connected to the stream API."""

    def __init__(self) -> None:
        """Initialize the API count."""
        self.count = 0

    async def async_added_to_opp(self) -> None:
        """Added to opp."""
        self.async_on_remove(
            self.opp.helpers.dispatcher.async_dispatcher_connect(
                SIGNAL_WEBSOCKET_CONNECTED, self._update_count
            )
        )
        self.async_on_remove(
            self.opp.helpers.dispatcher.async_dispatcher_connect(
                SIGNAL_WEBSOCKET_DISCONNECTED, self._update_count
            )
        )

    @property
    def name(self) -> str:
        """Return name of entity."""
        return "Connected clients"

    @property
    def state(self) -> int:
        """Return current API count."""
        return self.count

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return "clients"

    @callback
    def _update_count(self) -> None:
        self.count = self.opp.data.get(DATA_CONNECTIONS, 0)
        self.async_write_op_state()
