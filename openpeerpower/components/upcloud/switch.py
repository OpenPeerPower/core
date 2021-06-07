"""Support for interacting with UpCloud servers."""

from typing import Any

import voluptuous as vol

from openpeerpower.components.switch import PLATFORM_SCHEMA, SwitchEntity
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_USERNAME, STATE_OFF
from openpeerpower.core import OpenPeerPower
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.dispatcher import dispatcher_send
from openpeerpower.helpers.entity_platform import AddEntitiesCallback

from . import CONF_SERVERS, DATA_UPCLOUD, SIGNAL_UPDATE_UPCLOUD, UpCloudServerEntity

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_SERVERS): vol.All(cv.ensure_list, [cv.string])}
)


async def async_setup_entry(
    opp: OpenPeerPower,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the UpCloud server switch."""
    coordinator = opp.data[DATA_UPCLOUD].coordinators[config_entry.data[CONF_USERNAME]]
    entities = [UpCloudSwitch(coordinator, uuid) for uuid in coordinator.data]
    async_add_entities(entities, True)


class UpCloudSwitch(UpCloudServerEntity, SwitchEntity):
    """Representation of an UpCloud server switch."""

    def turn_on(self, **kwargs: Any) -> None:
        """Start the server."""
        if self.state == STATE_OFF:
            self._server.start()
            dispatcher_send(self.opp, SIGNAL_UPDATE_UPCLOUD)

    def turn_off(self, **kwargs: Any) -> None:
        """Stop the server."""
        if self.is_on:
            self._server.stop()
