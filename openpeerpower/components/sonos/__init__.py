"""Support to embed Sonos."""
from __future__ import annotations

import asyncio
from collections import OrderedDict, deque
import datetime
import logging
import socket
from urllib.parse import urlparse

import pysonos
from pysonos import events_asyncio
from pysonos.alarms import Alarm
from pysonos.core import SoCo
from pysonos.exceptions import SoCoException
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.components import ssdp
from openpeerpower.components.media_player import DOMAIN as MP_DOMAIN
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import (
    CONF_HOSTS,
    EVENT_OPENPEERPOWER_START,
    EVENT_OPENPEERPOWER_STOP,
)
from openpeerpower.core import Event, OpenPeerPower, callback
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.dispatcher import async_dispatcher_send

from .const import (
    DATA_SONOS,
    DISCOVERY_INTERVAL,
    DOMAIN,
    PLATFORMS,
    SONOS_ALARM_UPDATE,
    SONOS_GROUP_UPDATE,
    SONOS_SEEN,
    UPNP_ST,
)
from .favorites import SonosFavorites
from .speaker import SonosSpeaker

_LOGGER = logging.getLogger(__name__)

CONF_ADVERTISE_ADDR = "advertise_addr"
CONF_INTERFACE_ADDR = "interface_addr"


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                MP_DOMAIN: vol.Schema(
                    {
                        vol.Optional(CONF_ADVERTISE_ADDR): cv.string,
                        vol.Optional(CONF_INTERFACE_ADDR): cv.string,
                        vol.Optional(CONF_HOSTS): vol.All(
                            cv.ensure_list_csv, [cv.string]
                        ),
                    }
                )
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


class SonosData:
    """Storage class for platform global data."""

    def __init__(self) -> None:
        """Initialize the data."""
        # OrderedDict behavior used by SonosFavorites
        self.discovered: OrderedDict[str, SonosSpeaker] = OrderedDict()
        self.favorites: dict[str, SonosFavorites] = {}
        self.alarms: dict[str, Alarm] = {}
        self.processed_alarm_events = deque(maxlen=5)
        self.topology_condition = asyncio.Condition()
        self.hosts_heartbeat = None
        self.ssdp_known: set[str] = set()


async def async_setup(opp, config):
    """Set up the Sonos component."""
    conf = config.get(DOMAIN)

    opp.data[DOMAIN] = conf or {}

    if conf is not None:
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_IMPORT}
            )
        )

    return True


async def async_setup_entry(  # noqa: C901
    opp: OpenPeerPower, entry: ConfigEntry
) -> bool:
    """Set up Sonos from a config entry."""
    pysonos.config.EVENTS_MODULE = events_asyncio

    if DATA_SONOS not in opp.data:
        opp.data[DATA_SONOS] = SonosData()

    data = opp.data[DATA_SONOS]
    config = opp.data[DOMAIN].get("media_player", {})
    hosts = config.get(CONF_HOSTS, [])
    discovery_lock = asyncio.Lock()
    _LOGGER.debug("Reached async_setup_entry, config=%s", config)

    advertise_addr = config.get(CONF_ADVERTISE_ADDR)
    if advertise_addr:
        pysonos.config.EVENT_ADVERTISE_IP = advertise_addr

    async def _async_stop_event_listener(event: Event) -> None:
        if events_asyncio.event_listener:
            await events_asyncio.event_listener.async_stop()

    def _stop_manual_heartbeat(event: Event) -> None:
        if data.hosts_heartbeat:
            data.hosts_heartbeat()
            data.hosts_heartbeat = None

    def _discovered_player(soco: SoCo) -> None:
        """Handle a (re)discovered player."""
        try:
            _LOGGER.debug("Reached _discovered_player, soco=%s", soco)
            speaker_info = soco.get_speaker_info(True)
            _LOGGER.debug("Adding new speaker: %s", speaker_info)
            speaker = SonosSpeaker(opp, soco, speaker_info)
            data.discovered[soco.uid] = speaker
            if soco.household_id not in data.favorites:
                data.favorites[soco.household_id] = SonosFavorites(
                    opp, soco.household_id
                )
                data.favorites[soco.household_id].update()
            speaker.setup()
        except SoCoException as ex:
            _LOGGER.debug("SoCoException, ex=%s", ex)

    def _manual_hosts(now: datetime.datetime | None = None) -> None:
        """Players from network configuration."""
        for host in hosts:
            try:
                _LOGGER.debug("Testing %s", host)
                player = pysonos.SoCo(socket.gethostbyname(host))
                if player.is_visible:
                    # Make sure that the player is available
                    _ = player.volume
                _discovered_player(player)
            except (OSError, SoCoException) as ex:
                _LOGGER.debug("Issue connecting to '%s': %s", host, ex)
                if now is None:
                    _LOGGER.warning("Failed to initialize '%s'", host)

        _LOGGER.debug("Tested all hosts")
        data.hosts_heartbeat = opp.helpers.event.call_later(
            DISCOVERY_INTERVAL.total_seconds(), _manual_hosts
        )

    @callback
    def _async_signal_update_groups(event):
        async_dispatcher_send(opp, SONOS_GROUP_UPDATE)

    def _discovered_ip(ip_address):
        try:
            player = pysonos.SoCo(ip_address)
        except (OSError, SoCoException):
            _LOGGER.debug("Failed to connect to discovered player '%s'", ip_address)
            return
        if player.is_visible:
            _discovered_player(player)

    async def _async_create_discovered_player(uid, discovered_ip):
        """Only create one player at a time."""
        async with discovery_lock:
            if uid in data.discovered:
                async_dispatcher_send(opp, f"{SONOS_SEEN}-{uid}")
                return
            await opp.async_add_executor_job(_discovered_ip, discovered_ip)

    @callback
    def _async_discovered_player(info):
        uid = info.get(ssdp.ATTR_UPNP_UDN)
        if uid.startswith("uuid:"):
            uid = uid[5:]
        if uid not in data.ssdp_known:
            _LOGGER.debug("New discovery: %s", info)
            data.ssdp_known.add(uid)
        discovered_ip = urlparse(info[ssdp.ATTR_SSDP_LOCATION]).hostname
        asyncio.create_task(_async_create_discovered_player(uid, discovered_ip))

    @callback
    def _async_signal_update_alarms(event):
        async_dispatcher_send(opp, SONOS_ALARM_UPDATE)

    async def setup_platforms_and_discovery():
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_setup(entry, platform)
                for platform in PLATFORMS
            ]
        )
        entry.async_on_unload(
            opp.bus.async_listen_once(
                EVENT_OPENPEERPOWER_START, _async_signal_update_groups
            )
        )
        entry.async_on_unload(
            opp.bus.async_listen_once(
                EVENT_OPENPEERPOWER_START, _async_signal_update_alarms
            )
        )
        entry.async_on_unload(
            opp.bus.async_listen_once(
                EVENT_OPENPEERPOWER_STOP, _async_stop_event_listener
            )
        )
        _LOGGER.debug("Adding discovery job")
        if hosts:
            entry.async_on_unload(
                opp.bus.async_listen_once(
                    EVENT_OPENPEERPOWER_STOP, _stop_manual_heartbeat
                )
            )
            await opp.async_add_executor_job(_manual_hosts)
            return

        entry.async_on_unload(
            ssdp.async_register_callback(
                opp, _async_discovered_player, {"st": UPNP_ST}
            )
        )

    opp.async_create_task(setup_platforms_and_discovery())

    return True
