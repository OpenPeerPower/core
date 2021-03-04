"""Support for Z-Wave controls using the number platform."""
from typing import Callable, List, Optional

from zwave_js_server.client import Client as ZwaveClient

from openpeerpower.components.number import DOMAIN as NUMBER_DOMAIN, NumberEntity
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers.dispatcher import async_dispatcher_connect

from .const import DATA_CLIENT, DATA_UNSUBSCRIBE, DOMAIN
from .discovery import ZwaveDiscoveryInfo
from .entity import ZWaveBaseEntity


async def async_setup_entry(
    opp: OpenPeerPower, config_entry: ConfigEntry, async_add_entities: Callable
) -> None:
    """Set up Z-Wave Number entity from Config Entry."""
    client: ZwaveClient = opp.data[DOMAIN][config_entry.entry_id][DATA_CLIENT]

    @callback
    def async_add_number(info: ZwaveDiscoveryInfo) -> None:
        """Add Z-Wave number entity."""
        entities: List[ZWaveBaseEntity] = []
        entities.append(ZwaveNumberEntity(config_entry, client, info))
        async_add_entities(entities)

    opp.data[DOMAIN][config_entry.entry_id][DATA_UNSUBSCRIBE].append(
        async_dispatcher_connect(
            opp,
            f"{DOMAIN}_{config_entry.entry_id}_add_{NUMBER_DOMAIN}",
            async_add_number,
        )
    )


class ZwaveNumberEntity(ZWaveBaseEntity, NumberEntity):
    """Representation of a Z-Wave number entity."""

    def __init__(
        self, config_entry: ConfigEntry, client: ZwaveClient, info: ZwaveDiscoveryInfo
    ) -> None:
        """Initialize a ZwaveNumberEntity entity."""
        super().__init__(config_entry, client, info)
        self._name = self.generate_name(
            include_value_name=True, alternate_value_name=info.platform_hint
        )
        if self.info.primary_value.metadata.writeable:
            self._target_value = self.info.primary_value
        else:
            self._target_value = self.get_zwave_value("targetValue")

    @property
    def min_value(self) -> float:
        """Return the minimum value."""
        if self.info.primary_value.metadata.min is None:
            return 0
        return float(self.info.primary_value.metadata.min)

    @property
    def max_value(self) -> float:
        """Return the maximum value."""
        if self.info.primary_value.metadata.max is None:
            return 255
        return float(self.info.primary_value.metadata.max)

    @property
    def value(self) -> Optional[float]:  # type: ignore
        """Return the entity value."""
        if self.info.primary_value.value is None:
            return None
        return float(self.info.primary_value.value)

    @property
    def unit_of_measurement(self) -> Optional[str]:
        """Return the unit of measurement of this entity, if any."""
        if self.info.primary_value.metadata.unit is None:
            return None
        return str(self.info.primary_value.metadata.unit)

    async def async_set_value(self, value: float) -> None:
        """Set new value."""
        await self.info.node.async_set_value(self._target_value, value)
