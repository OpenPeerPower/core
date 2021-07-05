"""Support for Verisure alarm control panels."""
from __future__ import annotations

import asyncio

from openpeerpower.components.alarm_control_panel import (
    FORMAT_NUMBER,
    AlarmControlPanelEntity,
)
from openpeerpower.components.alarm_control_panel.const import (
    SUPPORT_ALARM_ARM_AWAY,
    SUPPORT_ALARM_ARM_HOME,
)
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers.entity import DeviceInfo
from openpeerpower.helpers.entity_platform import AddEntitiesCallback
from openpeerpower.helpers.update_coordinator import CoordinatorEntity

from .const import ALARM_STATE_TO_HA, CONF_GIID, DOMAIN, LOGGER
from .coordinator import VerisureDataUpdateCoordinator


async def async_setup_entry(
    opp: OpenPeerPower,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Verisure alarm control panel from a config entry."""
    async_add_entities([VerisureAlarm(coordinator=opp.data[DOMAIN][entry.entry_id])])


class VerisureAlarm(CoordinatorEntity, AlarmControlPanelEntity):
    """Representation of a Verisure alarm status."""

    coordinator: VerisureDataUpdateCoordinator

    _attr_name = "Verisure Alarm"
    _changed_by: str | None = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity."""
        return {
            "name": "Verisure Alarm",
            "manufacturer": "Verisure",
            "model": "VBox",
            "identifiers": {(DOMAIN, self.coordinator.entry.data[CONF_GIID])},
        }

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return SUPPORT_ALARM_ARM_HOME | SUPPORT_ALARM_ARM_AWAY

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this entity."""
        return self.coordinator.entry.data[CONF_GIID]

    @property
    def code_format(self) -> str:
        """Return one or more digits/characters."""
        return FORMAT_NUMBER

    @property
    def changed_by(self) -> str | None:
        """Return the last change triggered by."""
        return self._changed_by

    async def _async_set_arm_state(self, state: str, code: str | None = None) -> None:
        """Send set arm state command."""
        arm_state = await self.opp.async_add_executor_job(
            self.coordinator.verisure.set_arm_state, code, state
        )
        LOGGER.debug("Verisure set arm state %s", state)
        transaction = {}
        while "result" not in transaction:
            await asyncio.sleep(0.5)
            transaction = await self.opp.async_add_executor_job(
                self.coordinator.verisure.get_arm_state_transaction,
                arm_state["armStateChangeTransactionId"],
            )

        await self.coordinator.async_refresh()

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        await self._async_set_arm_state("DISARMED", code)

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        await self._async_set_arm_state("ARMED_HOME", code)

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        await self._async_set_arm_state("ARMED_AWAY", code)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_state = ALARM_STATE_TO_HA.get(
            self.coordinator.data["alarm"]["statusType"]
        )
        self._changed_by = self.coordinator.data["alarm"].get("name")
        super()._handle_coordinator_update()

    async def async_added_to_opp(self) -> None:
        """When entity is added to opp."""
        await super().async_added_to_opp()
        self._handle_coordinator_update()
