"""Support for Tellstick covers using Tellstick Net."""
from openpeerpower.components import cover, tellduslive
from openpeerpower.components.cover import CoverEntity
from openpeerpower.helpers.dispatcher import async_dispatcher_connect

from .entry import TelldusLiveEntity


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up tellduslive sensors dynamically."""

    async def async_discover_cover(device_id):
        """Discover and add a discovered sensor."""
        client = opp.data[tellduslive.DOMAIN]
        async_add_entities([TelldusLiveCover(client, device_id)])

    async_dispatcher_connect(
        opp,
        tellduslive.TELLDUS_DISCOVERY_NEW.format(cover.DOMAIN, tellduslive.DOMAIN),
        async_discover_cover,
    )


class TelldusLiveCover(TelldusLiveEntity, CoverEntity):
    """Representation of a cover."""

    @property
    def is_closed(self):
        """Return the current position of the cover."""
        return self.device.is_down

    def close_cover(self, **kwargs):
        """Close the cover."""
        self.device.down()
        self._update_callback()

    def open_cover(self, **kwargs):
        """Open the cover."""
        self.device.up()
        self._update_callback()

    def stop_cover(self, **kwargs):
        """Stop the cover."""
        self.device.stop()
        self._update_callback()
