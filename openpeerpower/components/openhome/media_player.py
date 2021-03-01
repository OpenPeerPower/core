"""Support for Openhome Devices."""
import logging

from openhomedevice.Device import Device
import voluptuous as vol

from openpeerpower.components.media_player import MediaPlayerEntity
from openpeerpower.components.media_player.const import (
    MEDIA_TYPE_MUSIC,
    SUPPORT_NEXT_TRACK,
    SUPPORT_PAUSE,
    SUPPORT_PLAY,
    SUPPORT_PLAY_MEDIA,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_SELECT_SOURCE,
    SUPPORT_STOP,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_STEP,
)
from openpeerpower.const import STATE_IDLE, STATE_OFF, STATE_PAUSED, STATE_PLAYING
from openpeerpower.helpers import config_validation as cv, entity_platform

from .const import ATTR_PIN_INDEX, DATA_OPENHOME, SERVICE_INVOKE_PIN

SUPPORT_OPENHOME = SUPPORT_SELECT_SOURCE | SUPPORT_TURN_OFF | SUPPORT_TURN_ON

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(opp, config, async_add_entities, discovery_info=None):
    """Set up the Openhome platform."""

    if not discovery_info:
        return

    openhome_data = opp.data.setdefault(DATA_OPENHOME, set())

    name = discovery_info.get("name")
    description = discovery_info.get("ssdp_description")

    _LOGGER.info("Openhome device found: %s", name)
    device = await opp.async_add_executor_job(Device, description)

    # if device has already been discovered
    if device.Uuid() in openhome_data:
        return True

    entity = OpenhomeDevice(opp, device)

    async_add_entities([entity])
    openhome_data.add(device.Uuid())

    platform = entity_platform.current_platform.get()

    platform.async_register_entity_service(
        SERVICE_INVOKE_PIN,
        {vol.Required(ATTR_PIN_INDEX): cv.positive_int},
        "invoke_pin",
    )


class OpenhomeDevice(MediaPlayerEntity):
    """Representation of an Openhome device."""

    def __init__(self, opp, device):
        """Initialise the Openhome device."""
        self.opp = opp
        self._device = device
        self._track_information = {}
        self._in_standby = None
        self._transport_state = None
        self._volume_level = None
        self._volume_muted = None
        self._supported_features = SUPPORT_OPENHOME
        self._source_names = []
        self._source_index = {}
        self._source = {}
        self._name = None
        self._state = STATE_PLAYING

    def update(self):
        """Update state of device."""
        self._in_standby = self._device.IsInStandby()
        self._transport_state = self._device.TransportState()
        self._track_information = self._device.TrackInfo()
        self._source = self._device.Source()
        self._name = self._device.Room().decode("utf-8")
        self._supported_features = SUPPORT_OPENHOME
        source_index = {}
        source_names = []

        if self._device.VolumeEnabled():
            self._supported_features |= (
                SUPPORT_VOLUME_STEP | SUPPORT_VOLUME_MUTE | SUPPORT_VOLUME_SET
            )
            self._volume_level = self._device.VolumeLevel() / 100.0
            self._volume_muted = self._device.IsMuted()

        for source in self._device.Sources():
            source_names.append(source["name"])
            source_index[source["name"]] = source["index"]

        self._source_index = source_index
        self._source_names = source_names

        if self._source["type"] == "Radio":
            self._supported_features |= SUPPORT_STOP | SUPPORT_PLAY | SUPPORT_PLAY_MEDIA
        if self._source["type"] in ("Playlist", "Spotify"):
            self._supported_features |= (
                SUPPORT_PREVIOUS_TRACK
                | SUPPORT_NEXT_TRACK
                | SUPPORT_PAUSE
                | SUPPORT_PLAY
                | SUPPORT_PLAY_MEDIA
            )

        if self._in_standby:
            self._state = STATE_OFF
        elif self._transport_state == "Paused":
            self._state = STATE_PAUSED
        elif self._transport_state in ("Playing", "Buffering"):
            self._state = STATE_PLAYING
        elif self._transport_state == "Stopped":
            self._state = STATE_IDLE
        else:
            # Device is playing an external source with no transport controls
            self._state = STATE_PLAYING

    def turn_on(self):
        """Bring device out of standby."""
        self._device.SetStandby(False)

    def turn_off(self):
        """Put device in standby."""
        self._device.SetStandby(True)

    def play_media(self, media_type, media_id, **kwargs):
        """Send the play_media command to the media player."""
        if not media_type == MEDIA_TYPE_MUSIC:
            _LOGGER.error(
                "Invalid media type %s. Only %s is supported",
                media_type,
                MEDIA_TYPE_MUSIC,
            )
            return
        track_details = {"title": "Open Peer Power", "uri": media_id}
        self._device.PlayMedia(track_details)

    def media_pause(self):
        """Send pause command."""
        self._device.Pause()

    def media_stop(self):
        """Send stop command."""
        self._device.Stop()

    def media_play(self):
        """Send play command."""
        self._device.Play()

    def media_next_track(self):
        """Send next track command."""
        self._device.Skip(1)

    def media_previous_track(self):
        """Send previous track command."""
        self._device.Skip(-1)

    def select_source(self, source):
        """Select input source."""
        self._device.SetSource(self._source_index[source])

    def invoke_pin(self, pin):
        """Invoke pin."""
        self._device.InvokePin(pin)

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def supported_features(self):
        """Flag of features commands that are supported."""
        return self._supported_features

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._device.Uuid()

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def source_list(self):
        """List of available input sources."""
        return self._source_names

    @property
    def media_image_url(self):
        """Image url of current playing media."""
        return self._track_information.get("albumArtwork")

    @property
    def media_artist(self):
        """Artist of current playing media, music track only."""
        artists = self._track_information.get("artist")
        if artists:
            return artists[0]

    @property
    def media_album_name(self):
        """Album name of current playing media, music track only."""
        return self._track_information.get("albumTitle")

    @property
    def media_title(self):
        """Title of current playing media."""
        return self._track_information.get("title")

    @property
    def source(self):
        """Name of the current input source."""
        return self._source.get("name")

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        return self._volume_level

    @property
    def is_volume_muted(self):
        """Return true if volume is muted."""
        return self._volume_muted

    def volume_up(self):
        """Volume up media player."""
        self._device.IncreaseVolume()

    def volume_down(self):
        """Volume down media player."""
        self._device.DecreaseVolume()

    def set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        self._device.SetVolumeLevel(int(volume * 100))

    def mute_volume(self, mute):
        """Mute (true) or unmute (false) media player."""
        self._device.SetMute(mute)
