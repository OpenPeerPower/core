"""Support for the TrackR platform."""
import logging

from pytrackr.api import trackrApiInterface
import voluptuous as vol

from openpeerpower.components.device_tracker import (
    PLATFORM_SCHEMA as PARENT_PLATFORM_SCHEMA,
)
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.event import track_utc_time_change
from openpeerpower.util import slugify

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PARENT_PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_USERNAME): cv.string, vol.Required(CONF_PASSWORD): cv.string}
)


def setup_scanner(opp, config: dict, see, discovery_info=None):
    """Validate the configuration and return a TrackR scanner."""
    TrackRDeviceScanner(opp, config, see)
    return True


class TrackRDeviceScanner:
    """A class representing a TrackR device."""

    def __init__(self, opp, config: dict, see) -> None:
        """Initialize the TrackR device scanner."""

        self.opp = opp
        self.api = trackrApiInterface(
            config.get(CONF_USERNAME), config.get(CONF_PASSWORD)
        )
        self.see = see
        self.devices = self.api.get_trackrs()
        self._update_info()

        track_utc_time_change(self.opp, self._update_info, second=range(0, 60, 30))

    def _update_info(self, now=None) -> None:
        """Update the device info."""
        _LOGGER.debug("Updating devices %s", now)

        # Update self.devices to collect new devices added
        # to the users account.
        self.devices = self.api.get_trackrs()

        for trackr in self.devices:
            trackr.update_state()
            trackr_id = trackr.tracker_id()
            trackr_device_id = trackr.id()
            lost = trackr.lost()
            dev_id = slugify(trackr.name())
            if dev_id is None:
                dev_id = trackr_id
            location = trackr.last_known_location()
            lat = location["latitude"]
            lon = location["longitude"]

            attrs = {
                "last_updated": trackr.last_updated(),
                "last_seen": trackr.last_time_seen(),
                "trackr_id": trackr_id,
                "id": trackr_device_id,
                "lost": lost,
                "battery_level": trackr.battery_level(),
            }

            self.see(dev_id=dev_id, gps=(lat, lon), attributes=attrs)
