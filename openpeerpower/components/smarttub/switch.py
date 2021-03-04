"""Platform for switch integration."""
import logging

import async_timeout
from smarttub import SpaPump

from openpeerpower.components.switch import SwitchEntity

from .const import API_TIMEOUT, DOMAIN, SMARTTUB_CONTROLLER
from .entity import SmartTubEntity
from .helpers import get_spa_name

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(opp, entry, async_add_entities):
    """Set up switch entities for the pumps on the tub."""

    controller = opp.data[DOMAIN][entry.entry_id][SMARTTUB_CONTROLLER]

    entities = [
        SmartTubPump(controller.coordinator, pump)
        for spa in controller.spas
        for pump in await spa.get_pumps()
    ]

    async_add_entities(entities)


class SmartTubPump(SmartTubEntity, SwitchEntity):
    """A pump on a spa."""

    def __init__(self, coordinator, pump: SpaPump):
        """Initialize the entity."""
        super().__init__(coordinator, pump.spa, "pump")
        self.pump_id = pump.id
        self.pump_type = pump.type

    @property
    def pump(self) -> SpaPump:
        """Return the underlying SpaPump object for this entity."""
        return self.coordinator.data[self.spa.id]["pumps"][self.pump_id]

    @property
    def unique_id(self) -> str:
        """Return a unique ID for this pump entity."""
        return f"{super().unique_id}-{self.pump_id}"

    @property
    def name(self) -> str:
        """Return a name for this pump entity."""
        spa_name = get_spa_name(self.spa)
        if self.pump_type == SpaPump.PumpType.CIRCULATION:
            return f"{spa_name} Circulation Pump"
        if self.pump_type == SpaPump.PumpType.JET:
            return f"{spa_name} Jet {self.pump_id}"
        return f"{spa_name} pump {self.pump_id}"

    @property
    def is_on(self) -> bool:
        """Return True if the pump is on."""
        return self.pump.state != SpaPump.PumpState.OFF

    async def async_toggle(self, **kwargs) -> None:
        """Toggle the pump on or off."""
        async with async_timeout.timeout(API_TIMEOUT):
            await self.pump.toggle()
        await self.coordinator.async_request_refresh()
