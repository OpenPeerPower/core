"""Heartbeats for Broadlink devices."""
import datetime as dt
import logging

import broadlink as blk

from openpeerpower.const import CONF_HOST
from openpeerpower.helpers import event

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class BroadlinkHeartbeat:
    """Manages heartbeats in the Broadlink integration.

    Some devices reboot when they cannot reach the cloud. This mechanism
    feeds their watchdog timers so they can be used offline.
    """

    HEARTBEAT_INTERVAL = dt.timedelta(minutes=2)

    def __init__(self, opp):
        """Initialize the heartbeat."""
        self._opp = opp
        self._unsubscribe = None

    async def async_setup(self):
        """Set up the heartbeat."""
        if self._unsubscribe is None:
            await self.async_heartbeat(dt.datetime.now())
            self._unsubscribe = event.async_track_time_interval(
                self._opp, self.async_heartbeat, self.HEARTBEAT_INTERVAL
            )

    async def async_unload(self):
        """Unload the heartbeat."""
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None

    async def async_heartbeat(self, now):
        """Send packets to feed watchdog timers."""
        opp = self._opp
        config_entries = opp.config_entries.async_entries(DOMAIN)
        hosts = {entry.data[CONF_HOST] for entry in config_entries}
        await opp.async_add_executor_job(self.heartbeat, hosts)

    @staticmethod
    def heartbeat(hosts):
        """Send packets to feed watchdog timers."""
        for host in hosts:
            try:
                blk.ping(host)
            except OSError as err:
                _LOGGER.debug("Failed to send heartbeat to %s: %s", host, err)
            else:
                _LOGGER.debug("Heartbeat sent to %s", host)
