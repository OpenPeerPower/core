"""Provide functionality to interact with Cast devices on the network."""
import asyncio
from datetime import timedelta
import functools as ft
import json
import logging
from typing import Optional

import pychromecast
from pychromecast.controllers.homeassistant import HomeAssistantController
from pychromecast.controllers.multizone import MultizoneManager
from pychromecast.controllers.plex import PlexController
from pychromecast.controllers.receiver import VOLUME_CONTROL_TYPE_FIXED
from pychromecast.quick_play import quick_play
from pychromecast.socket_client import (
    CONNECTION_STATUS_CONNECTED,
    CONNECTION_STATUS_DISCONNECTED,
)
import voluptuous as vol

from openpeerpower.auth.models import RefreshToken
from openpeerpower.components import media_source, zeroconf
from openpeerpower.components.http.auth import async_sign_path
from openpeerpower.components.media_player import MediaPlayerEntity
from openpeerpower.components.media_player.const import (
    ATTR_MEDIA_EXTRA,
    MEDIA_TYPE_MOVIE,
    MEDIA_TYPE_MUSIC,
    MEDIA_TYPE_TVSHOW,
    SUPPORT_BROWSE_MEDIA,
    SUPPORT_NEXT_TRACK,
    SUPPORT_PAUSE,
    SUPPORT_PLAY,
    SUPPORT_PLAY_MEDIA,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_SEEK,
    SUPPORT_STOP,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_SET,
)
from openpeerpower.components.plex.const import PLEX_URI_SCHEME
from openpeerpower.components.plex.services import lookup_plex_media
from openpeerpower.const import (
    EVENT_OPENPEERPOWER_STOP,
    STATE_IDLE,
    STATE_OFF,
    STATE_PAUSED,
    STATE_PLAYING,
)
from openpeerpower.core import callback
from openpeerpower.exceptions import PlatformNotReady
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.dispatcher import async_dispatcher_connect
from openpeerpower.helpers.network import NoURLAvailableError, get_url
from openpeerpower.helpers.typing import ConfigType, OpenPeerPowerType
import openpeerpower.util.dt as dt_util
from openpeerpower.util.logging import async_create_catching_coro

from .const import (
    ADDED_CAST_DEVICES_KEY,
    CAST_MULTIZONE_MANAGER_KEY,
    DOMAIN as CAST_DOMAIN,
    KNOWN_CHROMECAST_INFO_KEY,
    SIGNAL_CAST_DISCOVERED,
    SIGNAL_CAST_REMOVED,
    SIGNAL_OPP_CAST_SHOW_VIEW,
)
from .discovery import setup_internal_discovery
from .helpers import CastStatusListener, ChromecastInfo, ChromeCastZeroconf

_LOGGER = logging.getLogger(__name__)

CONF_IGNORE_CEC = "ignore_cec"
CONF_UUID = "uuid"
CAST_SPLASH = "https://www.openpeerpower.io/images/cast/splash.png"

SUPPORT_CAST = (
    SUPPORT_PAUSE
    | SUPPORT_PLAY
    | SUPPORT_PLAY_MEDIA
    | SUPPORT_STOP
    | SUPPORT_TURN_OFF
    | SUPPORT_TURN_ON
)


ENTITY_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Optional(CONF_UUID): cv.string,
            vol.Optional(CONF_IGNORE_CEC): vol.All(cv.ensure_list, [cv.string]),
        }
    ),
)


@callback
def _async_create_cast_device(opp: OpenPeerPowerType, info: ChromecastInfo):
    """Create a CastDevice Entity from the chromecast object.

    Returns None if the cast device has already been added.
    """
    _LOGGER.debug("_async_create_cast_device: %s", info)
    if info.uuid is None:
        _LOGGER.error("_async_create_cast_device uuid none: %s", info)
        return None

    # Found a cast with UUID
    added_casts = opp.data[ADDED_CAST_DEVICES_KEY]
    if info.uuid in added_casts:
        # Already added this one, the entity will take care of moved hosts
        # itself
        return None
    # -> New cast device
    added_casts.add(info.uuid)

    if info.is_dynamic_group:
        # This is a dynamic group, do not add it but connect to the service.
        group = DynamicCastGroup(opp, info)
        group.async_setup()
        return None

    return CastDevice(info)


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up Cast from a config entry."""
    config = opp.data[CAST_DOMAIN].get("media_player") or {}
    if not isinstance(config, list):
        config = [config]

    # no pending task
    done, _ = await asyncio.wait(
        [
            _async_setup_platform(
                opp, ENTITY_SCHEMA(cfg), async_add_entities, config_entry
            )
            for cfg in config
        ]
    )
    if any(task.exception() for task in done):
        exceptions = [task.exception() for task in done]
        for exception in exceptions:
            _LOGGER.debug("Failed to setup chromecast", exc_info=exception)
        raise PlatformNotReady


async def _async_setup_platform(
    opp: OpenPeerPowerType, config: ConfigType, async_add_entities, config_entry
):
    """Set up the cast platform."""
    # Import CEC IGNORE attributes
    pychromecast.IGNORE_CEC += config.get(CONF_IGNORE_CEC, [])
    opp.data.setdefault(ADDED_CAST_DEVICES_KEY, set())
    opp.data.setdefault(KNOWN_CHROMECAST_INFO_KEY, {})

    wanted_uuid = None
    if CONF_UUID in config:
        wanted_uuid = config[CONF_UUID]

    @callback
    def async_cast_discovered(discover: ChromecastInfo) -> None:
        """Handle discovery of a new chromecast."""
        # If wanted_uuid is set, we're handling a specific cast device identified by UUID
        if wanted_uuid is not None and wanted_uuid != discover.uuid:
            # UUID not matching, this is not it.
            return

        cast_device = _async_create_cast_device(opp, discover)
        if cast_device is not None:
            async_add_entities([cast_device])

    async_dispatcher_connect(opp, SIGNAL_CAST_DISCOVERED, async_cast_discovered)
    # Re-play the callback for all past chromecasts, store the objects in
    # a list to avoid concurrent modification resulting in exception.
    for chromecast in opp.data[KNOWN_CHROMECAST_INFO_KEY].values():
        async_cast_discovered(chromecast)

    ChromeCastZeroconf.set_zeroconf(await zeroconf.async_get_instance(opp))
    opp.async_add_executor_job(setup_internal_discovery, opp, config_entry)


class CastDevice(MediaPlayerEntity):
    """Representation of a Cast device on the network.

    This class is the holder of the pychromecast.Chromecast object and its
    socket client. It therefore handles all reconnects and audio group changing
    "elected leader" itself.
    """

    def __init__(self, cast_info: ChromecastInfo):
        """Initialize the cast device."""

        self._cast_info = cast_info
        self.services = cast_info.services
        self._chromecast: Optional[pychromecast.Chromecast] = None
        self.cast_status = None
        self.media_status = None
        self.media_status_received = None
        self.mz_media_status = {}
        self.mz_media_status_received = {}
        self.mz_mgr = None
        self._available = False
        self._status_listener: Optional[CastStatusListener] = None
        self._opp_cast_controller: Optional[HomeAssistantController] = None

        self._add_remove_handler = None
        self._cast_view_remove_handler = None

    async def async_added_to_opp(self):
        """Create chromecast object when added to opp."""
        self._add_remove_handler = async_dispatcher_connect(
            self.opp, SIGNAL_CAST_DISCOVERED, self._async_cast_discovered
        )
        self.opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, self._async_stop)
        self.async_set_cast_info(self._cast_info)
        self.opp.async_create_task(
            async_create_catching_coro(self.async_connect_to_chromecast())
        )

        self._cast_view_remove_handler = async_dispatcher_connect(
            self.opp, SIGNAL_OPP_CAST_SHOW_VIEW, self._handle_signal_show_view
        )

    async def async_will_remove_from_opp(self) -> None:
        """Disconnect Chromecast object when removed."""
        await self._async_disconnect()
        if self._cast_info.uuid is not None:
            # Remove the entity from the added casts so that it can dynamically
            # be re-added again.
            self.opp.data[ADDED_CAST_DEVICES_KEY].remove(self._cast_info.uuid)
        if self._add_remove_handler:
            self._add_remove_handler()
            self._add_remove_handler = None
        if self._cast_view_remove_handler:
            self._cast_view_remove_handler()
            self._cast_view_remove_handler = None

    def async_set_cast_info(self, cast_info):
        """Set the cast information."""

        self._cast_info = cast_info

    async def async_connect_to_chromecast(self):
        """Set up the chromecast object."""

        _LOGGER.debug(
            "[%s %s] Connecting to cast device by service %s",
            self.entity_id,
            self._cast_info.friendly_name,
            self.services,
        )
        chromecast = await self.opp.async_add_executor_job(
            pychromecast.get_chromecast_from_cast_info,
            pychromecast.discovery.CastInfo(
                self.services,
                self._cast_info.uuid,
                self._cast_info.model_name,
                self._cast_info.friendly_name,
                None,
                None,
            ),
            ChromeCastZeroconf.get_zeroconf(),
        )
        self._chromecast = chromecast

        if CAST_MULTIZONE_MANAGER_KEY not in self.opp.data:
            self.opp.data[CAST_MULTIZONE_MANAGER_KEY] = MultizoneManager()

        self.mz_mgr = self.opp.data[CAST_MULTIZONE_MANAGER_KEY]

        self._status_listener = CastStatusListener(self, chromecast, self.mz_mgr)
        self._available = False
        self.cast_status = chromecast.status
        self.media_status = chromecast.media_controller.status
        self._chromecast.start()
        self.async_write_op_state()

    async def _async_disconnect(self):
        """Disconnect Chromecast object if it is set."""
        if self._chromecast is None:
            # Can't disconnect if not connected.
            return
        _LOGGER.debug(
            "[%s %s] Disconnecting from chromecast socket",
            self.entity_id,
            self._cast_info.friendly_name,
        )
        self._available = False
        self.async_write_op_state()

        await self.opp.async_add_executor_job(self._chromecast.disconnect)

        self._invalidate()

        self.async_write_op_state()

    def _invalidate(self):
        """Invalidate some attributes."""
        self._chromecast = None
        self.cast_status = None
        self.media_status = None
        self.media_status_received = None
        self.mz_media_status = {}
        self.mz_media_status_received = {}
        self.mz_mgr = None
        self._opp_cast_controller = None
        if self._status_listener is not None:
            self._status_listener.invalidate()
            self._status_listener = None

    # ========== Callbacks ==========
    def new_cast_status(self, cast_status):
        """Handle updates of the cast status."""
        self.cast_status = cast_status
        self.schedule_update_op_state()

    def new_media_status(self, media_status):
        """Handle updates of the media status."""
        if (
            media_status
            and media_status.player_is_idle
            and media_status.idle_reason == "ERROR"
        ):
            external_url = None
            internal_url = None
            tts_base_url = None
            url_description = ""
            if "tts" in self.opp.config.components:
                try:
                    tts_base_url = self.opp.components.tts.get_base_url(self.opp)
                except KeyError:
                    # base_url not configured, ignore
                    pass
            try:
                external_url = get_url(self.opp, allow_internal=False)
            except NoURLAvailableError:
                # external_url not configured, ignore
                pass
            try:
                internal_url = get_url(self.opp, allow_external=False)
            except NoURLAvailableError:
                # internal_url not configured, ignore
                pass

            if media_status.content_id:
                if tts_base_url and media_status.content_id.startswith(tts_base_url):
                    url_description = f" from tts.base_url ({tts_base_url})"
                if external_url and media_status.content_id.startswith(external_url):
                    url_description = f" from external_url ({external_url})"
                if internal_url and media_status.content_id.startswith(internal_url):
                    url_description = f" from internal_url ({internal_url})"

            _LOGGER.error(
                "Failed to cast media %s%s. Please make sure the URL is: "
                "Reachable from the cast device and either a publicly resolvable "
                "hostname or an IP address",
                media_status.content_id,
                url_description,
            )

        self.media_status = media_status
        self.media_status_received = dt_util.utcnow()
        self.schedule_update_op_state()

    def new_connection_status(self, connection_status):
        """Handle updates of connection status."""
        _LOGGER.debug(
            "[%s %s] Received cast device connection status: %s",
            self.entity_id,
            self._cast_info.friendly_name,
            connection_status.status,
        )
        if connection_status.status == CONNECTION_STATUS_DISCONNECTED:
            self._available = False
            self._invalidate()
            self.schedule_update_op_state()
            return

        new_available = connection_status.status == CONNECTION_STATUS_CONNECTED
        if new_available != self._available:
            # Connection status callbacks happen often when disconnected.
            # Only update state when availability changed to put less pressure
            # on state machine.
            _LOGGER.debug(
                "[%s %s] Cast device availability changed: %s",
                self.entity_id,
                self._cast_info.friendly_name,
                connection_status.status,
            )
            self._available = new_available
            self.schedule_update_op_state()

    def multizone_new_media_status(self, group_uuid, media_status):
        """Handle updates of audio group media status."""
        _LOGGER.debug(
            "[%s %s] Multizone %s media status: %s",
            self.entity_id,
            self._cast_info.friendly_name,
            group_uuid,
            media_status,
        )
        self.mz_media_status[group_uuid] = media_status
        self.mz_media_status_received[group_uuid] = dt_util.utcnow()
        self.schedule_update_op_state()

    # ========== Service Calls ==========
    def _media_controller(self):
        """
        Return media controller.

        First try from our own cast, then groups which our cast is a member in.
        """
        media_status = self.media_status
        media_controller = self._chromecast.media_controller

        if media_status is None or media_status.player_state == "UNKNOWN":
            groups = self.mz_media_status
            for k, val in groups.items():
                if val and val.player_state != "UNKNOWN":
                    media_controller = self.mz_mgr.get_multizone_mediacontroller(k)
                    break

        return media_controller

    def turn_on(self):
        """Turn on the cast device."""

        if not self._chromecast.is_idle:
            # Already turned on
            return

        if self._chromecast.app_id is not None:
            # Quit the previous app before starting splash screen
            self._chromecast.quit_app()

        # The only way we can turn the Chromecast is on is by launching an app
        self._chromecast.play_media(CAST_SPLASH, pychromecast.STREAM_TYPE_BUFFERED)

    def turn_off(self):
        """Turn off the cast device."""
        self._chromecast.quit_app()

    def mute_volume(self, mute):
        """Mute the volume."""
        self._chromecast.set_volume_muted(mute)

    def set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        self._chromecast.set_volume(volume)

    def media_play(self):
        """Send play command."""
        media_controller = self._media_controller()
        media_controller.play()

    def media_pause(self):
        """Send pause command."""
        media_controller = self._media_controller()
        media_controller.pause()

    def media_stop(self):
        """Send stop command."""
        media_controller = self._media_controller()
        media_controller.stop()

    def media_previous_track(self):
        """Send previous track command."""
        media_controller = self._media_controller()
        media_controller.queue_prev()

    def media_next_track(self):
        """Send next track command."""
        media_controller = self._media_controller()
        media_controller.queue_next()

    def media_seek(self, position):
        """Seek the media to a specific location."""
        media_controller = self._media_controller()
        media_controller.seek(position)

    async def async_browse_media(self, media_content_type=None, media_content_id=None):
        """Implement the websocket media browsing helper."""
        result = await media_source.async_browse_media(self.opp, media_content_id)
        return result

    async def async_play_media(self, media_type, media_id, **kwargs):
        """Play a piece of media."""
        # Handle media_source
        if media_source.is_media_source_id(media_id):
            sourced_media = await media_source.async_resolve_media(self.opp, media_id)
            media_type = sourced_media.mime_type
            media_id = sourced_media.url

        # If media ID is a relative URL, we serve it from HA.
        # Create a signed path.
        if media_id[0] == "/":
            # Sign URL with Open Peer Power Cast User
            config_entries = self.opp.config_entries.async_entries(CAST_DOMAIN)
            user_id = config_entries[0].data["user_id"]
            user = await self.opp.auth.async_get_user(user_id)
            if user.refresh_tokens:
                refresh_token: RefreshToken = list(user.refresh_tokens.values())[0]

                media_id = async_sign_path(
                    self.opp,
                    refresh_token.id,
                    media_id,
                    timedelta(minutes=5),
                )

            # prepend external URL
            opp_url = get_url(self.opp, prefer_external=True)
            media_id = f"{opp_url}{media_id}"

        await self.opp.async_add_executor_job(
            ft.partial(self.play_media, media_type, media_id, **kwargs)
        )

    def play_media(self, media_type, media_id, **kwargs):
        """Play media from a URL."""
        # We do not want this to be forwarded to a group
        if media_type == CAST_DOMAIN:
            try:
                app_data = json.loads(media_id)
            except json.JSONDecodeError:
                _LOGGER.error("Invalid JSON in media_content_id")
                raise

            # Special handling for passed `app_id` parameter. This will only launch
            # an arbitrary cast app, generally for UX.
            if "app_id" in app_data:
                app_id = app_data.pop("app_id")
                _LOGGER.info("Starting Cast app by ID %s", app_id)
                self._chromecast.start_app(app_id)
                if app_data:
                    _LOGGER.warning(
                        "Extra keys %s were ignored. Please use app_name to cast media",
                        app_data.keys(),
                    )
                return

            app_name = app_data.pop("app_name")
            try:
                quick_play(self._chromecast, app_name, app_data)
            except NotImplementedError:
                _LOGGER.error("App %s not supported", app_name)
        # Handle plex
        elif media_id and media_id.startswith(PLEX_URI_SCHEME):
            media_id = media_id[len(PLEX_URI_SCHEME) :]
            media, _ = lookup_plex_media(self.opp, media_type, media_id)
            if media is None:
                return
            controller = PlexController()
            self._chromecast.register_handler(controller)
            controller.play_media(media)
        else:
            self._chromecast.media_controller.play_media(
                media_id, media_type, **kwargs.get(ATTR_MEDIA_EXTRA, {})
            )

    # ========== Properties ==========
    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def name(self):
        """Return the name of the device."""
        return self._cast_info.friendly_name

    @property
    def device_info(self):
        """Return information about the device."""
        cast_info = self._cast_info

        if cast_info.model_name == "Google Cast Group":
            return None

        return {
            "name": cast_info.friendly_name,
            "identifiers": {(CAST_DOMAIN, cast_info.uuid.replace("-", ""))},
            "model": cast_info.model_name,
            "manufacturer": cast_info.manufacturer,
        }

    def _media_status(self):
        """
        Return media status.

        First try from our own cast, then groups which our cast is a member in.
        """
        media_status = self.media_status
        media_status_received = self.media_status_received

        if media_status is None or media_status.player_state == "UNKNOWN":
            groups = self.mz_media_status
            for k, val in groups.items():
                if val and val.player_state != "UNKNOWN":
                    media_status = val
                    media_status_received = self.mz_media_status_received[k]
                    break

        return (media_status, media_status_received)

    @property
    def state(self):
        """Return the state of the player."""
        media_status = self._media_status()[0]

        if media_status is None:
            return None
        if media_status.player_is_playing:
            return STATE_PLAYING
        if media_status.player_is_paused:
            return STATE_PAUSED
        if media_status.player_is_idle:
            return STATE_IDLE
        if self._chromecast is not None and self._chromecast.is_idle:
            return STATE_OFF
        return None

    @property
    def available(self):
        """Return True if the cast device is connected."""
        return self._available

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        return self.cast_status.volume_level if self.cast_status else None

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self.cast_status.volume_muted if self.cast_status else None

    @property
    def media_content_id(self):
        """Content ID of current playing media."""
        media_status = self._media_status()[0]
        return media_status.content_id if media_status else None

    @property
    def media_content_type(self):
        """Content type of current playing media."""
        media_status = self._media_status()[0]
        if media_status is None:
            return None
        if media_status.media_is_tvshow:
            return MEDIA_TYPE_TVSHOW
        if media_status.media_is_movie:
            return MEDIA_TYPE_MOVIE
        if media_status.media_is_musictrack:
            return MEDIA_TYPE_MUSIC
        return None

    @property
    def media_duration(self):
        """Duration of current playing media in seconds."""
        media_status = self._media_status()[0]
        return media_status.duration if media_status else None

    @property
    def media_image_url(self):
        """Image url of current playing media."""
        media_status = self._media_status()[0]
        if media_status is None:
            return None

        images = media_status.images

        return images[0].url if images and images[0].url else None

    @property
    def media_image_remotely_accessible(self) -> bool:
        """If the image url is remotely accessible."""
        return True

    @property
    def media_title(self):
        """Title of current playing media."""
        media_status = self._media_status()[0]
        return media_status.title if media_status else None

    @property
    def media_artist(self):
        """Artist of current playing media (Music track only)."""
        media_status = self._media_status()[0]
        return media_status.artist if media_status else None

    @property
    def media_album_name(self):
        """Album of current playing media (Music track only)."""
        media_status = self._media_status()[0]
        return media_status.album_name if media_status else None

    @property
    def media_album_artist(self):
        """Album artist of current playing media (Music track only)."""
        media_status = self._media_status()[0]
        return media_status.album_artist if media_status else None

    @property
    def media_track(self):
        """Track number of current playing media (Music track only)."""
        media_status = self._media_status()[0]
        return media_status.track if media_status else None

    @property
    def media_series_title(self):
        """Return the title of the series of current playing media."""
        media_status = self._media_status()[0]
        return media_status.series_title if media_status else None

    @property
    def media_season(self):
        """Season of current playing media (TV Show only)."""
        media_status = self._media_status()[0]
        return media_status.season if media_status else None

    @property
    def media_episode(self):
        """Episode of current playing media (TV Show only)."""
        media_status = self._media_status()[0]
        return media_status.episode if media_status else None

    @property
    def app_id(self):
        """Return the ID of the current running app."""
        return self._chromecast.app_id if self._chromecast else None

    @property
    def app_name(self):
        """Name of the current running app."""
        return self._chromecast.app_display_name if self._chromecast else None

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        support = SUPPORT_CAST
        media_status = self._media_status()[0]

        if self.cast_status:
            if self.cast_status.volume_control_type != VOLUME_CONTROL_TYPE_FIXED:
                support |= SUPPORT_VOLUME_MUTE | SUPPORT_VOLUME_SET

        if media_status:
            if media_status.supports_queue_next:
                support |= SUPPORT_PREVIOUS_TRACK
            if media_status.supports_queue_next:
                support |= SUPPORT_NEXT_TRACK
            if media_status.supports_seek:
                support |= SUPPORT_SEEK

        if "media_source" in self.opp.config.components:
            support |= SUPPORT_BROWSE_MEDIA

        return support

    @property
    def media_position(self):
        """Position of current playing media in seconds."""
        media_status = self._media_status()[0]
        if media_status is None or not (
            media_status.player_is_playing
            or media_status.player_is_paused
            or media_status.player_is_idle
        ):
            return None
        return media_status.current_time

    @property
    def media_position_updated_at(self):
        """When was the position of the current playing media valid.

        Returns value from openpeerpower.util.dt.utcnow().
        """
        media_status_recevied = self._media_status()[1]
        return media_status_recevied

    @property
    def unique_id(self) -> Optional[str]:
        """Return a unique ID."""
        return self._cast_info.uuid

    async def _async_cast_discovered(self, discover: ChromecastInfo):
        """Handle discovery of new Chromecast."""
        if self._cast_info.uuid != discover.uuid:
            # Discovered is not our device.
            return

        _LOGGER.debug("Discovered chromecast with same UUID: %s", discover)
        self.async_set_cast_info(discover)

    async def _async_stop(self, event):
        """Disconnect socket on Open Peer Power stop."""
        await self._async_disconnect()

    def _handle_signal_show_view(
        self,
        controller: HomeAssistantController,
        entity_id: str,
        view_path: str,
        url_path: Optional[str],
    ):
        """Handle a show view signal."""
        if entity_id != self.entity_id:
            return

        if self._opp_cast_controller is None:
            self._opp_cast_controller = controller
            self._chromecast.register_handler(controller)

        self._opp_cast_controller.show_lovelace_view(view_path, url_path)


class DynamicCastGroup:
    """Representation of a Cast device on the network - for dynamic cast groups."""

    def __init__(self, opp, cast_info: ChromecastInfo):
        """Initialize the cast device."""

        self.opp = opp
        self._cast_info = cast_info
        self.services = cast_info.services
        self._chromecast: Optional[pychromecast.Chromecast] = None
        self.mz_mgr = None
        self._status_listener: Optional[CastStatusListener] = None

        self._add_remove_handler = None
        self._del_remove_handler = None

    def async_setup(self):
        """Create chromecast object."""
        self._add_remove_handler = async_dispatcher_connect(
            self.opp, SIGNAL_CAST_DISCOVERED, self._async_cast_discovered
        )
        self._del_remove_handler = async_dispatcher_connect(
            self.opp, SIGNAL_CAST_REMOVED, self._async_cast_removed
        )
        self.opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, self._async_stop)
        self.async_set_cast_info(self._cast_info)
        self.opp.async_create_task(
            async_create_catching_coro(self.async_connect_to_chromecast())
        )

    async def async_tear_down(self) -> None:
        """Disconnect Chromecast object."""
        await self._async_disconnect()
        if self._cast_info.uuid is not None:
            # Remove the entity from the added casts so that it can dynamically
            # be re-added again.
            self.opp.data[ADDED_CAST_DEVICES_KEY].remove(self._cast_info.uuid)
        if self._add_remove_handler:
            self._add_remove_handler()
            self._add_remove_handler = None
        if self._del_remove_handler:
            self._del_remove_handler()
            self._del_remove_handler = None

    def async_set_cast_info(self, cast_info):
        """Set the cast information and set up the chromecast object."""

        self._cast_info = cast_info

    async def async_connect_to_chromecast(self):
        """Set the cast information and set up the chromecast object."""

        _LOGGER.debug(
            "[%s %s] Connecting to cast device by service %s",
            "Dynamic group",
            self._cast_info.friendly_name,
            self.services,
        )
        chromecast = await self.opp.async_add_executor_job(
            pychromecast.get_chromecast_from_cast_info,
            pychromecast.discovery.CastInfo(
                self.services,
                self._cast_info.uuid,
                self._cast_info.model_name,
                self._cast_info.friendly_name,
                None,
                None,
            ),
            ChromeCastZeroconf.get_zeroconf(),
        )
        self._chromecast = chromecast

        if CAST_MULTIZONE_MANAGER_KEY not in self.opp.data:
            self.opp.data[CAST_MULTIZONE_MANAGER_KEY] = MultizoneManager()

        self.mz_mgr = self.opp.data[CAST_MULTIZONE_MANAGER_KEY]

        self._status_listener = CastStatusListener(self, chromecast, self.mz_mgr, True)
        self._chromecast.start()

    async def _async_disconnect(self):
        """Disconnect Chromecast object if it is set."""
        if self._chromecast is None:
            # Can't disconnect if not connected.
            return
        _LOGGER.debug(
            "[%s %s] Disconnecting from chromecast socket",
            "Dynamic group",
            self._cast_info.friendly_name,
        )

        await self.opp.async_add_executor_job(self._chromecast.disconnect)

        self._invalidate()

    def _invalidate(self):
        """Invalidate some attributes."""
        self._chromecast = None
        self.mz_mgr = None
        if self._status_listener is not None:
            self._status_listener.invalidate()
            self._status_listener = None

    async def _async_cast_discovered(self, discover: ChromecastInfo):
        """Handle discovery of new Chromecast."""
        if self._cast_info.uuid != discover.uuid:
            # Discovered is not our device.
            return

        _LOGGER.debug("Discovered dynamic group with same UUID: %s", discover)
        self.async_set_cast_info(discover)

    async def _async_cast_removed(self, discover: ChromecastInfo):
        """Handle removal of Chromecast."""
        if self._cast_info.uuid != discover.uuid:
            # Removed is not our device.
            return

        if not discover.services:
            # Clean up the dynamic group
            _LOGGER.debug("Clean up dynamic group: %s", discover)
            await self.async_tear_down()

    async def _async_stop(self, event):
        """Disconnect socket on Open Peer Power stop."""
        await self._async_disconnect()
