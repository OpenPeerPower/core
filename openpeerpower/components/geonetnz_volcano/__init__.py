"""The GeoNet NZ Volcano integration."""
import asyncio
from datetime import datetime, timedelta
import logging
from typing import Optional

from aio_geojson_geonetnz_volcano import GeonetnzVolcanoFeedManager
import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT
from openpeerpower.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_RADIUS,
    CONF_SCAN_INTERVAL,
    CONF_UNIT_SYSTEM,
    CONF_UNIT_SYSTEM_IMPERIAL,
    LENGTH_MILES,
)
from openpeerpower.core import callback
from openpeerpower.helpers import aiohttp_client, config_validation as cv
from openpeerpower.helpers.dispatcher import async_dispatcher_send
from openpeerpower.helpers.event import async_track_time_interval
from openpeerpower.util.unit_system import METRIC_SYSTEM

from .config_flow import configured_instances
from .const import DEFAULT_RADIUS, DEFAULT_SCAN_INTERVAL, DOMAIN, FEED

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_LATITUDE): cv.latitude,
                vol.Optional(CONF_LONGITUDE): cv.longitude,
                vol.Optional(CONF_RADIUS, default=DEFAULT_RADIUS): vol.Coerce(float),
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): cv.time_period,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Set up the GeoNet NZ Volcano component."""
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]

    latitude = conf.get(CONF_LATITUDE, opp.config.latitude)
    longitude = conf.get(CONF_LONGITUDE, opp.config.longitude)
    scan_interval = conf[CONF_SCAN_INTERVAL]

    identifier = f"{latitude}, {longitude}"
    if identifier in configured_instances(opp):
        return True

    opp.async_create_task(
        opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data={
                CONF_LATITUDE: latitude,
                CONF_LONGITUDE: longitude,
                CONF_RADIUS: conf[CONF_RADIUS],
                CONF_SCAN_INTERVAL: scan_interval,
            },
        )
    )

    return True


async def async_setup_entry(opp, config_entry):
    """Set up the GeoNet NZ Volcano component as config entry."""
    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN].setdefault(FEED, {})

    radius = config_entry.data[CONF_RADIUS]
    unit_system = config_entry.data[CONF_UNIT_SYSTEM]
    if unit_system == CONF_UNIT_SYSTEM_IMPERIAL:
        radius = METRIC_SYSTEM.length(radius, LENGTH_MILES)
    # Create feed entity manager for all platforms.
    manager = GeonetnzVolcanoFeedEntityManager(opp, config_entry, radius, unit_system)
    opp.data[DOMAIN][FEED][config_entry.entry_id] = manager
    _LOGGER.debug("Feed entity manager added for %s", config_entry.entry_id)
    await manager.async_init()
    return True


async def async_unload_entry(opp, config_entry):
    """Unload an GeoNet NZ Volcano component config entry."""
    manager = opp.data[DOMAIN][FEED].pop(config_entry.entry_id)
    await manager.async_stop()
    await asyncio.wait(
        [opp.config_entries.async_forward_entry_unload(config_entry, "sensor")]
    )
    return True


class GeonetnzVolcanoFeedEntityManager:
    """Feed Entity Manager for GeoNet NZ Volcano feed."""

    def __init__(self, opp, config_entry, radius_in_km, unit_system):
        """Initialize the Feed Entity Manager."""
        self._opp = opp
        self._config_entry = config_entry
        coordinates = (
            config_entry.data[CONF_LATITUDE],
            config_entry.data[CONF_LONGITUDE],
        )
        websession = aiohttp_client.async_get_clientsession(opp)
        self._feed_manager = GeonetnzVolcanoFeedManager(
            websession,
            self._generate_entity,
            self._update_entity,
            self._remove_entity,
            coordinates,
            filter_radius=radius_in_km,
        )
        self._config_entry_id = config_entry.entry_id
        self._scan_interval = timedelta(seconds=config_entry.data[CONF_SCAN_INTERVAL])
        self._unit_system = unit_system
        self._track_time_remove_callback = None
        self.listeners = []

    async def async_init(self):
        """Schedule initial and regular updates based on configured time interval."""

        self._opp.async_create_task(
            self._opp.config_entries.async_forward_entry_setup(
                self._config_entry, "sensor"
            )
        )

        async def update(event_time):
            """Update."""
            await self.async_update()

        # Trigger updates at regular intervals.
        self._track_time_remove_callback = async_track_time_interval(
            self._opp, update, self._scan_interval
        )

        _LOGGER.debug("Feed entity manager initialized")

    async def async_update(self):
        """Refresh data."""
        await self._feed_manager.update()
        _LOGGER.debug("Feed entity manager updated")

    async def async_stop(self):
        """Stop this feed entity manager from refreshing."""
        for unsub_dispatcher in self.listeners:
            unsub_dispatcher()
        self.listeners = []
        if self._track_time_remove_callback:
            self._track_time_remove_callback()
        _LOGGER.debug("Feed entity manager stopped")

    @callback
    def async_event_new_entity(self):
        """Return manager specific event to signal new entity."""
        return f"geonetnz_volcano_new_sensor_{self._config_entry_id}"

    def get_entry(self, external_id):
        """Get feed entry by external id."""
        return self._feed_manager.feed_entries.get(external_id)

    def last_update(self) -> Optional[datetime]:
        """Return the last update of this feed."""
        return self._feed_manager.last_update

    def last_update_successful(self) -> Optional[datetime]:
        """Return the last successful update of this feed."""
        return self._feed_manager.last_update_successful

    async def _generate_entity(self, external_id):
        """Generate new entity."""
        async_dispatcher_send(
            self._opp,
            self.async_event_new_entity(),
            self,
            external_id,
            self._unit_system,
        )

    async def _update_entity(self, external_id):
        """Update entity."""
        async_dispatcher_send(self._opp, f"geonetnz_volcano_update_{external_id}")

    async def _remove_entity(self, external_id):
        """Ignore removing entity."""
