"""Feed Entity Manager Sensor support for GDACS Feed."""
from __future__ import annotations

import logging

from openpeerpower.components.sensor import SensorEntity
from openpeerpower.core import callback
from openpeerpower.helpers.dispatcher import async_dispatcher_connect
from openpeerpower.util import dt

from .const import DEFAULT_ICON, DOMAIN, FEED

_LOGGER = logging.getLogger(__name__)

ATTR_STATUS = "status"
ATTR_LAST_UPDATE = "last_update"
ATTR_LAST_UPDATE_SUCCESSFUL = "last_update_successful"
ATTR_LAST_TIMESTAMP = "last_timestamp"
ATTR_CREATED = "created"
ATTR_UPDATED = "updated"
ATTR_REMOVED = "removed"

DEFAULT_UNIT_OF_MEASUREMENT = "alerts"

# An update of this entity is not making a web request, but uses internal data only.
PARALLEL_UPDATES = 0


async def async_setup_entry(opp, entry, async_add_entities):
    """Set up the GDACS Feed platform."""
    manager = opp.data[DOMAIN][FEED][entry.entry_id]
    sensor = GdacsSensor(entry.entry_id, entry.unique_id, entry.title, manager)
    async_add_entities([sensor])
    _LOGGER.debug("Sensor setup done")


class GdacsSensor(SensorEntity):
    """This is a status sensor for the GDACS integration."""

    def __init__(self, config_entry_id, config_unique_id, config_title, manager):
        """Initialize entity."""
        self._config_entry_id = config_entry_id
        self._config_unique_id = config_unique_id
        self._config_title = config_title
        self._manager = manager
        self._status = None
        self._last_update = None
        self._last_update_successful = None
        self._last_timestamp = None
        self._total = None
        self._created = None
        self._updated = None
        self._removed = None
        self._remove_signal_status = None

    async def async_added_to_opp(self):
        """Call when entity is added to opp."""
        self._remove_signal_status = async_dispatcher_connect(
            self.opp,
            f"gdacs_status_{self._config_entry_id}",
            self._update_status_callback,
        )
        _LOGGER.debug("Waiting for updates %s", self._config_entry_id)
        # First update is manual because of how the feed entity manager is updated.
        await self.async_update()

    async def async_will_remove_from_opp(self) -> None:
        """Call when entity will be removed from opp."""
        if self._remove_signal_status:
            self._remove_signal_status()

    @callback
    def _update_status_callback(self):
        """Call status update method."""
        _LOGGER.debug("Received status update for %s", self._config_entry_id)
        self.async_schedule_update_op_state(True)

    @property
    def should_poll(self):
        """No polling needed for GDACS status sensor."""
        return False

    async def async_update(self):
        """Update this entity from the data held in the feed manager."""
        _LOGGER.debug("Updating %s", self._config_entry_id)
        if self._manager:
            status_info = self._manager.status_info()
            if status_info:
                self._update_from_status_info(status_info)

    def _update_from_status_info(self, status_info):
        """Update the internal state from the provided information."""
        self._status = status_info.status
        self._last_update = (
            dt.as_utc(status_info.last_update) if status_info.last_update else None
        )
        if status_info.last_update_successful:
            self._last_update_successful = dt.as_utc(status_info.last_update_successful)
        else:
            self._last_update_successful = None
        self._last_timestamp = status_info.last_timestamp
        self._total = status_info.total
        self._created = status_info.created
        self._updated = status_info.updated
        self._removed = status_info.removed

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._total

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID containing latitude/longitude."""
        return self._config_unique_id

    @property
    def name(self) -> str | None:
        """Return the name of the entity."""
        return f"GDACS ({self._config_title})"

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return DEFAULT_ICON

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return DEFAULT_UNIT_OF_MEASUREMENT

    @property
    def extra_state_attributes(self):
        """Return the device state attributes."""
        attributes = {}
        for key, value in (
            (ATTR_STATUS, self._status),
            (ATTR_LAST_UPDATE, self._last_update),
            (ATTR_LAST_UPDATE_SUCCESSFUL, self._last_update_successful),
            (ATTR_LAST_TIMESTAMP, self._last_timestamp),
            (ATTR_CREATED, self._created),
            (ATTR_UPDATED, self._updated),
            (ATTR_REMOVED, self._removed),
        ):
            if value or isinstance(value, bool):
                attributes[key] = value
        return attributes
