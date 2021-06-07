"""Entity representing a Sonos player."""
from __future__ import annotations

import datetime
import logging

from pysonos.core import SoCo
from pysonos.exceptions import SoCoException

import openpeerpower.helpers.device_registry as dr
from openpeerpower.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from openpeerpower.helpers.entity import DeviceInfo, Entity

from .const import (
    DOMAIN,
    SONOS_ENTITY_CREATED,
    SONOS_HOUSEHOLD_UPDATED,
    SONOS_POLL_UPDATE,
    SONOS_STATE_UPDATED,
)
from .speaker import SonosSpeaker

_LOGGER = logging.getLogger(__name__)


class SonosEntity(Entity):
    """Representation of a Sonos entity."""

    def __init__(self, speaker: SonosSpeaker) -> None:
        """Initialize a SonosEntity."""
        self.speaker = speaker

    async def async_added_to_opp(self) -> None:
        """Handle common setup when added to opp."""
        await self.speaker.async_seen()

        self.async_on_remove(
            async_dispatcher_connect(
                self.opp,
                f"{SONOS_POLL_UPDATE}-{self.soco.uid}",
                self.async_poll,
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.opp,
                f"{SONOS_STATE_UPDATED}-{self.soco.uid}",
                self.async_write_op_state,
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.opp,
                f"{SONOS_HOUSEHOLD_UPDATED}-{self.soco.household_id}",
                self.async_write_op_state,
            )
        )
        async_dispatcher_send(
            self.opp, f"{SONOS_ENTITY_CREATED}-{self.soco.uid}", self.platform.domain
        )

    async def async_poll(self, now: datetime.datetime) -> None:
        """Poll the entity if subscriptions fail."""
        if self.speaker.is_first_poll:
            _LOGGER.warning(
                "%s cannot reach [%s], falling back to polling, functionality may be limited",
                self.speaker.zone_name,
                self.speaker.subscription_address,
            )
            self.speaker.is_first_poll = False
        try:
            await self.async_update()  # pylint: disable=no-member
        except (OSError, SoCoException) as ex:
            _LOGGER.debug("Error connecting to %s: %s", self.entity_id, ex)

    @property
    def soco(self) -> SoCo:
        """Return the speaker SoCo instance."""
        return self.speaker.soco

    @property
    def device_info(self) -> DeviceInfo:
        """Return information about the device."""
        return {
            "identifiers": {(DOMAIN, self.soco.uid)},
            "name": self.speaker.zone_name,
            "model": self.speaker.model_name.replace("Sonos ", ""),
            "sw_version": self.speaker.version,
            "connections": {(dr.CONNECTION_NETWORK_MAC, self.speaker.mac_address)},
            "manufacturer": "Sonos",
            "suggested_area": self.speaker.zone_name,
        }

    @property
    def available(self) -> bool:
        """Return whether this device is available."""
        return self.speaker.available

    @property
    def should_poll(self) -> bool:
        """Return that we should not be polled (we handle that internally)."""
        return False
