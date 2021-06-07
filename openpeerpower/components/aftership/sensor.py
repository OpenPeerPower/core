"""Support for non-delivered packages recorded in AfterShip."""
from __future__ import annotations

import logging
from typing import Any, Final

from pyaftership.tracker import Tracking
import voluptuous as vol

from openpeerpower.components.sensor import (
    PLATFORM_SCHEMA as BASE_PLATFORM_SCHEMA,
    SensorEntity,
)
from openpeerpower.const import ATTR_ATTRIBUTION, CONF_API_KEY, CONF_NAME, HTTP_OK
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.dispatcher import async_dispatcher_send
from openpeerpower.helpers.entity_platform import AddEntitiesCallback
from openpeerpower.helpers.service import ServiceCall
from openpeerpower.helpers.typing import ConfigType, DiscoveryInfoType
from openpeerpower.util import Throttle

from .const import (
    ADD_TRACKING_SERVICE_SCHEMA,
    ATTR_TRACKINGS,
    ATTRIBUTION,
    BASE,
    CONF_SLUG,
    CONF_TITLE,
    CONF_TRACKING_NUMBER,
    DEFAULT_NAME,
    DOMAIN,
    ICON,
    MIN_TIME_BETWEEN_UPDATES,
    REMOVE_TRACKING_SERVICE_SCHEMA,
    SERVICE_ADD_TRACKING,
    SERVICE_REMOVE_TRACKING,
    UPDATE_TOPIC,
)

_LOGGER: Final = logging.getLogger(__name__)

PLATFORM_SCHEMA: Final = BASE_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


async def async_setup_platform(
    opp: OpenPeerPower,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the AfterShip sensor platform."""
    apikey = config[CONF_API_KEY]
    name = config[CONF_NAME]

    session = async_get_clientsession(opp)
    aftership = Tracking(opp.loop, session, apikey)

    await aftership.get_trackings()

    if not aftership.meta or aftership.meta["code"] != HTTP_OK:
        _LOGGER.error(
            "No tracking data found. Check API key is correct: %s", aftership.meta
        )
        return

    instance = AfterShipSensor(aftership, name)

    async_add_entities([instance], True)

    async def handle_add_tracking(call: ServiceCall) -> None:
        """Call when a user adds a new Aftership tracking from Open Peer Power."""
        title = call.data.get(CONF_TITLE)
        slug = call.data.get(CONF_SLUG)
        tracking_number = call.data[CONF_TRACKING_NUMBER]

        await aftership.add_package_tracking(tracking_number, title, slug)
        async_dispatcher_send(opp, UPDATE_TOPIC)

    opp.services.async_register(
        DOMAIN,
        SERVICE_ADD_TRACKING,
        handle_add_tracking,
        schema=ADD_TRACKING_SERVICE_SCHEMA,
    )

    async def handle_remove_tracking(call: ServiceCall) -> None:
        """Call when a user removes an Aftership tracking from Open Peer Power."""
        slug = call.data[CONF_SLUG]
        tracking_number = call.data[CONF_TRACKING_NUMBER]

        await aftership.remove_package_tracking(slug, tracking_number)
        async_dispatcher_send(opp, UPDATE_TOPIC)

    opp.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_TRACKING,
        handle_remove_tracking,
        schema=REMOVE_TRACKING_SERVICE_SCHEMA,
    )


class AfterShipSensor(SensorEntity):
    """Representation of a AfterShip sensor."""

    def __init__(self, aftership: Tracking, name: str) -> None:
        """Initialize the sensor."""
        self._attributes: dict[str, Any] = {}
        self._name: str = name
        self._state: int | None = None
        self.aftership = aftership

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self) -> int | None:
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement of this entity, if any."""
        return "packages"

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return attributes for the sensor."""
        return self._attributes

    @property
    def icon(self) -> str:
        """Icon to use in the frontend."""
        return ICON

    async def async_added_to_opp(self) -> None:
        """Register callbacks."""
        self.async_on_remove(
            self.opp.helpers.dispatcher.async_dispatcher_connect(
                UPDATE_TOPIC, self._force_update
            )
        )

    async def _force_update(self) -> None:
        """Force update of data."""
        await self.async_update(no_throttle=True)
        self.async_write_op_state()

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self, **kwargs: Any) -> None:
        """Get the latest data from the AfterShip API."""
        await self.aftership.get_trackings()

        if not self.aftership.meta:
            _LOGGER.error("Unknown errors when querying")
            return
        if self.aftership.meta["code"] != HTTP_OK:
            _LOGGER.error(
                "Errors when querying AfterShip. %s", str(self.aftership.meta)
            )
            return

        status_to_ignore = {"delivered"}
        status_counts: dict[str, int] = {}
        trackings = []
        not_delivered_count = 0

        for track in self.aftership.trackings["trackings"]:
            status = track["tag"].lower()
            name = (
                track["tracking_number"] if track["title"] is None else track["title"]
            )
            last_checkpoint = (
                f"Shipment {track['tag'].lower()}"
                if not track["checkpoints"]
                else track["checkpoints"][-1]
            )
            status_counts[status] = status_counts.get(status, 0) + 1
            trackings.append(
                {
                    "name": name,
                    "tracking_number": track["tracking_number"],
                    "slug": track["slug"],
                    "link": f"{BASE}{track['slug']}/{track['tracking_number']}",
                    "last_update": track["updated_at"],
                    "expected_delivery": track["expected_delivery"],
                    "status": track["tag"],
                    "last_checkpoint": last_checkpoint,
                }
            )

            if status not in status_to_ignore:
                not_delivered_count += 1
            else:
                _LOGGER.debug("Ignoring %s as it has status: %s", name, status)

        self._attributes = {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            **status_counts,
            ATTR_TRACKINGS: trackings,
        }

        self._state = not_delivered_count
