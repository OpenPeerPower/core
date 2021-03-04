"""Deal with Cast discovery."""
import logging
import threading

import pychromecast

from openpeerpower.const import EVENT_OPENPEERPOWER_STOP
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.dispatcher import dispatcher_send

from .const import (
    CAST_BROWSER_KEY,
    CONF_KNOWN_HOSTS,
    DEFAULT_PORT,
    INTERNAL_DISCOVERY_RUNNING_KEY,
    KNOWN_CHROMECAST_INFO_KEY,
    SIGNAL_CAST_DISCOVERED,
    SIGNAL_CAST_REMOVED,
)
from .helpers import ChromecastInfo, ChromeCastZeroconf

_LOGGER = logging.getLogger(__name__)


def discover_chromecast(opp: OpenPeerPower, device_info):
    """Discover a Chromecast."""

    info = ChromecastInfo(
        services=device_info.services,
        uuid=device_info.uuid,
        model_name=device_info.model_name,
        friendly_name=device_info.friendly_name,
        is_audio_group=device_info.port != DEFAULT_PORT,
    )

    if info.uuid is None:
        _LOGGER.error("Discovered chromecast without uuid %s", info)
        return

    info = info.fill_out_missing_chromecast_info()
    if info.uuid in opp.data[KNOWN_CHROMECAST_INFO_KEY]:
        _LOGGER.debug("Discovered update for known chromecast %s", info)
    else:
        _LOGGER.debug("Discovered chromecast %s", info)

    opp.data[KNOWN_CHROMECAST_INFO_KEY][info.uuid] = info
    dispatcher_send(opp, SIGNAL_CAST_DISCOVERED, info)


def _remove_chromecast(opp: OpenPeerPower, info: ChromecastInfo):
    # Removed chromecast
    _LOGGER.debug("Removed chromecast %s", info)

    dispatcher_send(opp, SIGNAL_CAST_REMOVED, info)


def setup_internal_discovery(opp: OpenPeerPower, config_entry) -> None:
    """Set up the pychromecast internal discovery."""
    if INTERNAL_DISCOVERY_RUNNING_KEY not in opp.data:
        opp.data[INTERNAL_DISCOVERY_RUNNING_KEY] = threading.Lock()

    if not opp.data[INTERNAL_DISCOVERY_RUNNING_KEY].acquire(blocking=False):
        # Internal discovery is already running
        return

    class CastListener(pychromecast.discovery.AbstractCastListener):
        """Listener for discovering chromecasts."""

        def add_cast(self, uuid, _):
            """Handle zeroconf discovery of a new chromecast."""
            discover_chromecast(opp, browser.devices[uuid])

        def update_cast(self, uuid, _):
            """Handle zeroconf discovery of an updated chromecast."""
            discover_chromecast(opp, browser.devices[uuid])

        def remove_cast(self, uuid, service, cast_info):
            """Handle zeroconf discovery of a removed chromecast."""
            _remove_chromecast(
                opp,
                ChromecastInfo(
                    services=cast_info.services,
                    uuid=cast_info.uuid,
                    model_name=cast_info.model_name,
                    friendly_name=cast_info.friendly_name,
                ),
            )

    _LOGGER.debug("Starting internal pychromecast discovery")
    browser = pychromecast.discovery.CastBrowser(
        CastListener(),
        ChromeCastZeroconf.get_zeroconf(),
        config_entry.data.get(CONF_KNOWN_HOSTS),
    )
    opp.data[CAST_BROWSER_KEY] = browser
    browser.start_discovery()

    def stop_discovery(event):
        """Stop discovery of new chromecasts."""
        _LOGGER.debug("Stopping internal pychromecast discovery")
        browser.stop_discovery()
        opp.data[INTERNAL_DISCOVERY_RUNNING_KEY].release()

    opp.bus.listen_once(EVENT_OPENPEERPOWER_STOP, stop_discovery)

    config_entry.add_update_listener(config_entry_updated)


async def config_entry_updated(opp, config_entry):
    """Handle config entry being updated."""
    browser = opp.data[CAST_BROWSER_KEY]
    browser.host_browser.update_hosts(config_entry.data.get(CONF_KNOWN_HOSTS))
