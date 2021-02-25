"""The tests for the Universal Media player platform."""
import asyncio
from copy import copy
from os import path
import unittest
from unittest.mock import patch

from voluptuous.error import MultipleInvalid

from openpeerpower import config as.opp_config
import openpeerpower.components.input_number as input_number
import openpeerpower.components.input_select as input_select
import openpeerpower.components.media_player as media_player
import openpeerpower.components.switch as switch
import openpeerpower.components.universal.media_player as universal
from openpeerpower.const import (
    SERVICE_RELOAD,
    STATE_OFF,
    STATE_ON,
    STATE_PAUSED,
    STATE_PLAYING,
    STATE_UNKNOWN,
)
from openpeerpower.core import Context, callback
from openpeerpower.setup import async_setup_component

from tests.common import get_test_open_peer_power, mock_service


def validate_config(config):
    """Use the platform schema to validate configuration."""
    validated_config = universal.PLATFORM_SCHEMA(config)
    validated_config.pop("platform")
    return validated_config


class MockMediaPlayer(media_player.MediaPlayerEntity):
    """Mock media player for testing."""

    def __init__(self, opp, name):
        """Initialize the media player."""
        self.opp = opp
        self._name = name
        self.entity_id = media_player.ENTITY_ID_FORMAT.format(name)
        self._state = STATE_OFF
        self._volume_level = 0
        self._is_volume_muted = False
        self._media_title = None
        self._supported_features = 0
        self._source = None
        self._tracks = 12
        self._media_image_url = None
        self._shuffle = False
        self._sound_mode = None

        self.service_calls = {
            "turn_on": mock_service(
                opp. media_player.DOMAIN, media_player.SERVICE_TURN_ON
            ),
            "turn_off": mock_service(
                opp. media_player.DOMAIN, media_player.SERVICE_TURN_OFF
            ),
            "mute_volume": mock_service(
                opp. media_player.DOMAIN, media_player.SERVICE_VOLUME_MUTE
            ),
            "set_volume_level": mock_service(
                opp. media_player.DOMAIN, media_player.SERVICE_VOLUME_SET
            ),
            "media_play": mock_service(
                opp. media_player.DOMAIN, media_player.SERVICE_MEDIA_PLAY
            ),
            "media_pause": mock_service(
                opp. media_player.DOMAIN, media_player.SERVICE_MEDIA_PAUSE
            ),
            "media_stop": mock_service(
                opp. media_player.DOMAIN, media_player.SERVICE_MEDIA_STOP
            ),
            "media_previous_track": mock_service(
                opp. media_player.DOMAIN, media_player.SERVICE_MEDIA_PREVIOUS_TRACK
            ),
            "media_next_track": mock_service(
                opp. media_player.DOMAIN, media_player.SERVICE_MEDIA_NEXT_TRACK
            ),
            "media_seek": mock_service(
                opp. media_player.DOMAIN, media_player.SERVICE_MEDIA_SEEK
            ),
            "play_media": mock_service(
                opp. media_player.DOMAIN, media_player.SERVICE_PLAY_MEDIA
            ),
            "volume_up": mock_service(
                opp. media_player.DOMAIN, media_player.SERVICE_VOLUME_UP
            ),
            "volume_down": mock_service(
                opp. media_player.DOMAIN, media_player.SERVICE_VOLUME_DOWN
            ),
            "media_play_pause": mock_service(
                opp. media_player.DOMAIN, media_player.SERVICE_MEDIA_PLAY_PAUSE
            ),
            "select_sound_mode": mock_service(
                opp. media_player.DOMAIN, media_player.SERVICE_SELECT_SOUND_MODE
            ),
            "select_source": mock_service(
                opp. media_player.DOMAIN, media_player.SERVICE_SELECT_SOURCE
            ),
            "toggle": mock_service(
                opp. media_player.DOMAIN, media_player.SERVICE_TOGGLE
            ),
            "clear_playlist": mock_service(
                opp. media_player.DOMAIN, media_player.SERVICE_CLEAR_PLAYLIST
            ),
            "repeat_set": mock_service(
                opp. media_player.DOMAIN, media_player.SERVICE_REPEAT_SET
            ),
            "shuffle_set": mock_service(
                opp. media_player.DOMAIN, media_player.SERVICE_SHUFFLE_SET
            ),
        }

    @property
    def name(self):
        """Return the name of player."""
        return self._name

    @property
    def state(self):
        """Return the state of the player."""
        return self._state

    @property
    def volume_level(self):
        """Return the volume level of player."""
        return self._volume_level

    @property
    def is_volume_muted(self):
        """Return true if the media player is muted."""
        return self._is_volume_muted

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return self._supported_features

    @property
    def media_image_url(self):
        """Image url of current playing media."""
        return self._media_image_url

    @property
    def shuffle(self):
        """Return true if the media player is shuffling."""
        return self._shuffle

    def turn_on(self):
        """Mock turn_on function."""
        self._state = None

    def turn_off(self):
        """Mock turn_off function."""
        self._state = STATE_OFF

    def mute_volume(self, mute):
        """Mock mute function."""
        self._is_volume_muted = mute

    def set_volume_level(self, volume):
        """Mock set volume level."""
        self._volume_level = volume

    def media_play(self):
        """Mock play."""
        self._state = STATE_PLAYING

    def media_pause(self):
        """Mock pause."""
        self._state = STATE_PAUSED

    def select_sound_mode(self, sound_mode):
        """Set the sound mode."""
        self._sound_mode = sound_mode

    def select_source(self, source):
        """Set the input source."""
        self._source = source

    def async_toggle(self):
        """Toggle the power on the media player."""
        self._state = STATE_OFF if self._state == STATE_ON else STATE_ON

    def clear_playlist(self):
        """Clear players playlist."""
        self._tracks = 0

    def set_shuffle(self, shuffle):
        """Enable/disable shuffle mode."""
        self._shuffle = shuffle

    def set_repeat(self, repeat):
        """Enable/disable repeat mode."""
        self._repeat = repeat


class TestMediaPlayer(unittest.TestCase):
    """Test the media_player module."""

    def setUp(self):  # pylint: disable=invalid-name
        """Set up things to be run when tests are started."""
        self opp =get_test_open_peer_power()

        self.mock_mp_1 = MockMediaPlayer(self.opp, "mock1")
        self.mock_mp_1.schedule_update_op_state()

        self.mock_mp_2 = MockMediaPlayer(self.opp, "mock2")
        self.mock_mp_2.schedule_update_op_state()

        self.opp.block_till_done()

        self.mock_mute_switch_id = switch.ENTITY_ID_FORMAT.format("mute")
        self.opp.states.set(self.mock_mute_switch_id, STATE_OFF)

        self.mock_state_switch_id = switch.ENTITY_ID_FORMAT.format("state")
        self.opp.states.set(self.mock_state_switch_id, STATE_OFF)

        self.mock_volume_id = f"{input_number.DOMAIN}.volume_level"
        self.opp.states.set(self.mock_volume_id, 0)

        self.mock_source_list_id = f"{input_select.DOMAIN}.source_list"
        self.opp.states.set(self.mock_source_list_id, ["dvd", "htpc"])

        self.mock_source_id = f"{input_select.DOMAIN}.source"
        self.opp.states.set(self.mock_source_id, "dvd")

        self.mock_sound_mode_list_id = f"{input_select.DOMAIN}.sound_mode_list"
        self.opp.states.set(self.mock_sound_mode_list_id, ["music", "movie"])

        self.mock_sound_mode_id = f"{input_select.DOMAIN}.sound_mode"
        self.opp.states.set(self.mock_sound_mode_id, "music")

        self.mock_shuffle_switch_id = switch.ENTITY_ID_FORMAT.format("shuffle")
        self.opp.states.set(self.mock_shuffle_switch_id, STATE_OFF)

        self.mock_repeat_switch_id = switch.ENTITY_ID_FORMAT.format("repeat")
        self.opp.states.set(self.mock_repeat_switch_id, STATE_OFF)

        self.config_children_only = {
            "name": "test",
            "platform": "universal",
            "children": [
                media_player.ENTITY_ID_FORMAT.format("mock1"),
                media_player.ENTITY_ID_FORMAT.format("mock2"),
            ],
        }
        self.config_children_and_attr = {
            "name": "test",
            "platform": "universal",
            "children": [
                media_player.ENTITY_ID_FORMAT.format("mock1"),
                media_player.ENTITY_ID_FORMAT.format("mock2"),
            ],
            "attributes": {
                "is_volume_muted": self.mock_mute_switch_id,
                "volume_level": self.mock_volume_id,
                "source": self.mock_source_id,
                "source_list": self.mock_source_list_id,
                "state": self.mock_state_switch_id,
                "shuffle": self.mock_shuffle_switch_id,
                "repeat": self.mock_repeat_switch_id,
                "sound_mode_list": self.mock_sound_mode_list_id,
                "sound_mode": self.mock_sound_mode_id,
            },
        }
        self.addCleanup(self.tear_down_cleanup)

    def tear_down_cleanup(self):
        """Stop everything that was started."""
        self.opp.stop()

    def test_config_children_only(self):
        """Check config with only children."""
        config_start = copy(self.config_children_only)
        del config_start["platform"]
        config_start["commands"] = {}
        config_start["attributes"] = {}

        config = validate_config(self.config_children_only)
        assert config_start == config

    def test_config_children_and_attr(self):
        """Check config with children and attributes."""
        config_start = copy(self.config_children_and_attr)
        del config_start["platform"]
        config_start["commands"] = {}

        config = validate_config(self.config_children_and_attr)
        assert config_start == config

    def test_config_no_name(self):
        """Check config with no Name entry."""
        response = True
        try:
            validate_config({"platform": "universal"})
        except MultipleInvalid:
            response = False
        assert not response

    def test_config_bad_children(self):
        """Check config with bad children entry."""
        config_no_children = {"name": "test", "platform": "universal"}
        config_bad_children = {"name": "test", "children": {}, "platform": "universal"}

        config_no_children = validate_config(config_no_children)
        assert [] == config_no_children["children"]

        config_bad_children = validate_config(config_bad_children)
        assert [] == config_bad_children["children"]

    def test_config_bad_commands(self):
        """Check config with bad commands entry."""
        config = {"name": "test", "platform": "universal"}

        config = validate_config(config)
        assert {} == config["commands"]

    def test_config_bad_attributes(self):
        """Check config with bad attributes."""
        config = {"name": "test", "platform": "universal"}

        config = validate_config(config)
        assert {} == config["attributes"]

    def test_config_bad_key(self):
        """Check config with bad key."""
        config = {"name": "test", "asdf": 5, "platform": "universal"}

        config = validate_config(config)
        assert not ("asdf" in config)

    def test_platform_setup(self):
        """Test platform setup."""
        config = {"name": "test", "platform": "universal"}
        bad_config = {"platform": "universal"}
        entities = []

        def add_entities(new_entities):
            """Add devices to list."""
            for dev in new_entities:
                entities.append(dev)

        setup_ok = True
        try:
            asyncio.run_coroutine_threadsafe(
                universal.async_setup_platform(
                    self.opp, validate_config(bad_config), add_entities
                ),
                self.opp.loop,
            ).result()
        except MultipleInvalid:
            setup_ok = False
        assert not setup_ok
        assert 0 == len(entities)

        asyncio.run_coroutine_threadsafe(
            universal.async_setup_platform(
                self.opp, validate_config(config), add_entities
            ),
            self.opp.loop,
        ).result()
        assert 1 == len(entities)
        assert "test" == entities[0].name

    def test_master_state(self):
        """Test master state property."""
        config = validate_config(self.config_children_only)

        ump = universal.UniversalMediaPlayer(self.opp, **config)

        assert ump.master_state is None

    def test_master_state_with_attrs(self):
        """Test master state property."""
        config = validate_config(self.config_children_and_attr)

        ump = universal.UniversalMediaPlayer(self.opp, **config)

        assert STATE_OFF == ump.master_state
        self.opp.states.set(self.mock_state_switch_id, STATE_ON)
        assert STATE_ON == ump.master_state

    def test_master_state_with_bad_attrs(self):
        """Test master state property."""
        config = copy(self.config_children_and_attr)
        config["attributes"]["state"] = "bad.entity_id"
        config = validate_config(config)

        ump = universal.UniversalMediaPlayer(self.opp, **config)

        assert STATE_OFF == ump.master_state

    def test_active_child_state(self):
        """Test active child state property."""
        config = validate_config(self.config_children_only)

        ump = universal.UniversalMediaPlayer(self.opp, **config)
        ump.entity_id = media_player.ENTITY_ID_FORMAT.format(config["name"])
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()

        assert ump._child_state is None

        self.mock_mp_1._state = STATE_PLAYING
        self.mock_mp_1.schedule_update_op_state()
        self.opp.block_till_done()
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()
        assert self.mock_mp_1.entity_id == ump._child_state.entity_id

        self.mock_mp_2._state = STATE_PLAYING
        self.mock_mp_2.schedule_update_op_state()
        self.opp.block_till_done()
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()
        assert self.mock_mp_1.entity_id == ump._child_state.entity_id

        self.mock_mp_1._state = STATE_OFF
        self.mock_mp_1.schedule_update_op_state()
        self.opp.block_till_done()
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()
        assert self.mock_mp_2.entity_id == ump._child_state.entity_id

    def test_name(self):
        """Test name property."""
        config = validate_config(self.config_children_only)

        ump = universal.UniversalMediaPlayer(self.opp, **config)

        assert config["name"] == ump.name

    def test_polling(self):
        """Test should_poll property."""
        config = validate_config(self.config_children_only)

        ump = universal.UniversalMediaPlayer(self.opp, **config)

        assert ump.should_poll is False

    def test_state_children_only(self):
        """Test media player state with only children."""
        config = validate_config(self.config_children_only)

        ump = universal.UniversalMediaPlayer(self.opp, **config)
        ump.entity_id = media_player.ENTITY_ID_FORMAT.format(config["name"])
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()

        assert ump.state, STATE_OFF

        self.mock_mp_1._state = STATE_PLAYING
        self.mock_mp_1.schedule_update_op_state()
        self.opp.block_till_done()
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()
        assert STATE_PLAYING == ump.state

    def test_state_with_children_and_attrs(self):
        """Test media player with children and master state."""
        config = validate_config(self.config_children_and_attr)

        ump = universal.UniversalMediaPlayer(self.opp, **config)
        ump.entity_id = media_player.ENTITY_ID_FORMAT.format(config["name"])
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()

        assert STATE_OFF == ump.state

        self.opp.states.set(self.mock_state_switch_id, STATE_ON)
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()
        assert STATE_ON == ump.state

        self.mock_mp_1._state = STATE_PLAYING
        self.mock_mp_1.schedule_update_op_state()
        self.opp.block_till_done()
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()
        assert STATE_PLAYING == ump.state

        self.opp.states.set(self.mock_state_switch_id, STATE_OFF)
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()
        assert STATE_OFF == ump.state

    def test_volume_level(self):
        """Test volume level property."""
        config = validate_config(self.config_children_only)

        ump = universal.UniversalMediaPlayer(self.opp, **config)
        ump.entity_id = media_player.ENTITY_ID_FORMAT.format(config["name"])
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()

        assert ump.volume_level is None

        self.mock_mp_1._state = STATE_PLAYING
        self.mock_mp_1.schedule_update_op_state()
        self.opp.block_till_done()
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()
        assert 0 == ump.volume_level

        self.mock_mp_1._volume_level = 1
        self.mock_mp_1.schedule_update_op_state()
        self.opp.block_till_done()
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()
        assert 1 == ump.volume_level

    def test_media_image_url(self):
        """Test media_image_url property."""
        test_url = "test_url"
        config = validate_config(self.config_children_only)

        ump = universal.UniversalMediaPlayer(self.opp, **config)
        ump.entity_id = media_player.ENTITY_ID_FORMAT.format(config["name"])
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()

        assert ump.media_image_url is None

        self.mock_mp_1._state = STATE_PLAYING
        self.mock_mp_1._media_image_url = test_url
        self.mock_mp_1.schedule_update_op_state()
        self.opp.block_till_done()
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()
        # mock_mp_1 will convert the url to the api proxy url. This test
        # ensures ump passes through the same url without an additional proxy.
        assert self.mock_mp_1.entity_picture == ump.entity_picture

    def test_is_volume_muted_children_only(self):
        """Test is volume muted property w/ children only."""
        config = validate_config(self.config_children_only)

        ump = universal.UniversalMediaPlayer(self.opp, **config)
        ump.entity_id = media_player.ENTITY_ID_FORMAT.format(config["name"])
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()

        assert not ump.is_volume_muted

        self.mock_mp_1._state = STATE_PLAYING
        self.mock_mp_1.schedule_update_op_state()
        self.opp.block_till_done()
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()
        assert not ump.is_volume_muted

        self.mock_mp_1._is_volume_muted = True
        self.mock_mp_1.schedule_update_op_state()
        self.opp.block_till_done()
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()
        assert ump.is_volume_muted

    def test_sound_mode_list_children_and_attr(self):
        """Test sound mode list property w/ children and attrs."""
        config = validate_config(self.config_children_and_attr)

        ump = universal.UniversalMediaPlayer(self.opp, **config)

        assert "['music', 'movie']" == ump.sound_mode_list

        self.opp.states.set(self.mock_sound_mode_list_id, ["music", "movie", "game"])
        assert "['music', 'movie', 'game']" == ump.sound_mode_list

    def test_source_list_children_and_attr(self):
        """Test source list property w/ children and attrs."""
        config = validate_config(self.config_children_and_attr)

        ump = universal.UniversalMediaPlayer(self.opp, **config)

        assert "['dvd', 'htpc']" == ump.source_list

        self.opp.states.set(self.mock_source_list_id, ["dvd", "htpc", "game"])
        assert "['dvd', 'htpc', 'game']" == ump.source_list

    def test_sound_mode_children_and_attr(self):
        """Test sound modeproperty w/ children and attrs."""
        config = validate_config(self.config_children_and_attr)

        ump = universal.UniversalMediaPlayer(self.opp, **config)

        assert "music" == ump.sound_mode

        self.opp.states.set(self.mock_sound_mode_id, "movie")
        assert "movie" == ump.sound_mode

    def test_source_children_and_attr(self):
        """Test source property w/ children and attrs."""
        config = validate_config(self.config_children_and_attr)

        ump = universal.UniversalMediaPlayer(self.opp, **config)

        assert "dvd" == ump.source

        self.opp.states.set(self.mock_source_id, "htpc")
        assert "htpc" == ump.source

    def test_volume_level_children_and_attr(self):
        """Test volume level property w/ children and attrs."""
        config = validate_config(self.config_children_and_attr)

        ump = universal.UniversalMediaPlayer(self.opp, **config)

        assert 0 == ump.volume_level

        self.opp.states.set(self.mock_volume_id, 100)
        assert 100 == ump.volume_level

    def test_is_volume_muted_children_and_attr(self):
        """Test is volume muted property w/ children and attrs."""
        config = validate_config(self.config_children_and_attr)

        ump = universal.UniversalMediaPlayer(self.opp, **config)

        assert not ump.is_volume_muted

        self.opp.states.set(self.mock_mute_switch_id, STATE_ON)
        assert ump.is_volume_muted

    def test_supported_features_children_only(self):
        """Test supported media commands with only children."""
        config = validate_config(self.config_children_only)

        ump = universal.UniversalMediaPlayer(self.opp, **config)
        ump.entity_id = media_player.ENTITY_ID_FORMAT.format(config["name"])
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()

        assert 0 == ump.supported_features

        self.mock_mp_1._supported_features = 512
        self.mock_mp_1._state = STATE_PLAYING
        self.mock_mp_1.schedule_update_op_state()
        self.opp.block_till_done()
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()
        assert 512 == ump.supported_features

    def test_supported_features_children_and_cmds(self):
        """Test supported media commands with children and attrs."""
        config = copy(self.config_children_and_attr)
        excmd = {"service": "media_player.test", "data": {"entity_id": "test"}}
        config["commands"] = {
            "turn_on": excmd,
            "turn_off": excmd,
            "volume_up": excmd,
            "volume_down": excmd,
            "volume_mute": excmd,
            "volume_set": excmd,
            "select_sound_mode": excmd,
            "select_source": excmd,
            "repeat_set": excmd,
            "shuffle_set": excmd,
            "media_play": excmd,
            "media_pause": excmd,
            "media_stop": excmd,
            "media_next_track": excmd,
            "media_previous_track": excmd,
            "toggle": excmd,
            "clear_playlist": excmd,
        }
        config = validate_config(config)

        ump = universal.UniversalMediaPlayer(self.opp, **config)
        ump.entity_id = media_player.ENTITY_ID_FORMAT.format(config["name"])
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()

        self.mock_mp_1._state = STATE_PLAYING
        self.mock_mp_1.schedule_update_op_state()
        self.opp.block_till_done()
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()

        check_flags = (
            universal.SUPPORT_TURN_ON
            | universal.SUPPORT_TURN_OFF
            | universal.SUPPORT_VOLUME_STEP
            | universal.SUPPORT_VOLUME_MUTE
            | universal.SUPPORT_SELECT_SOUND_MODE
            | universal.SUPPORT_SELECT_SOURCE
            | universal.SUPPORT_REPEAT_SET
            | universal.SUPPORT_SHUFFLE_SET
            | universal.SUPPORT_VOLUME_SET
            | universal.SUPPORT_PLAY
            | universal.SUPPORT_PAUSE
            | universal.SUPPORT_STOP
            | universal.SUPPORT_NEXT_TRACK
            | universal.SUPPORT_PREVIOUS_TRACK
            | universal.SUPPORT_CLEAR_PLAYLIST
        )

        assert check_flags == ump.supported_features

    def test_supported_features_play_pause(self):
        """Test supported media commands with play_pause function."""
        config = copy(self.config_children_and_attr)
        excmd = {"service": "media_player.test", "data": {"entity_id": "test"}}
        config["commands"] = {"media_play_pause": excmd}
        config = validate_config(config)

        ump = universal.UniversalMediaPlayer(self.opp, **config)
        ump.entity_id = media_player.ENTITY_ID_FORMAT.format(config["name"])
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()

        self.mock_mp_1._state = STATE_PLAYING
        self.mock_mp_1.schedule_update_op_state()
        self.opp.block_till_done()
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()

        check_flags = universal.SUPPORT_PLAY | universal.SUPPORT_PAUSE

        assert check_flags == ump.supported_features

    def test_service_call_no_active_child(self):
        """Test a service call to children with no active child."""
        config = validate_config(self.config_children_and_attr)

        ump = universal.UniversalMediaPlayer(self.opp, **config)
        ump.entity_id = media_player.ENTITY_ID_FORMAT.format(config["name"])
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()

        self.mock_mp_1._state = STATE_OFF
        self.mock_mp_1.schedule_update_op_state()
        self.mock_mp_2._state = STATE_OFF
        self.mock_mp_2.schedule_update_op_state()
        self.opp.block_till_done()
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()

        asyncio.run_coroutine_threadsafe(ump.async_turn_off(), self.opp.loop).result()
        assert 0 == len(self.mock_mp_1.service_calls["turn_off"])
        assert 0 == len(self.mock_mp_2.service_calls["turn_off"])

    def test_service_call_to_child(self):
        """Test service calls that should be routed to a child."""
        config = validate_config(self.config_children_only)

        ump = universal.UniversalMediaPlayer(self.opp, **config)
        ump.entity_id = media_player.ENTITY_ID_FORMAT.format(config["name"])
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()

        self.mock_mp_2._state = STATE_PLAYING
        self.mock_mp_2.schedule_update_op_state()
        self.opp.block_till_done()
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()

        asyncio.run_coroutine_threadsafe(ump.async_turn_off(), self.opp.loop).result()
        assert 1 == len(self.mock_mp_2.service_calls["turn_off"])

        asyncio.run_coroutine_threadsafe(ump.async_turn_on(), self.opp.loop).result()
        assert 1 == len(self.mock_mp_2.service_calls["turn_on"])

        asyncio.run_coroutine_threadsafe(
            ump.async_mute_volume(True), self.opp.loop
        ).result()
        assert 1 == len(self.mock_mp_2.service_calls["mute_volume"])

        asyncio.run_coroutine_threadsafe(
            ump.async_set_volume_level(0.5), self.opp.loop
        ).result()
        assert 1 == len(self.mock_mp_2.service_calls["set_volume_level"])

        asyncio.run_coroutine_threadsafe(
            ump.async_media_play(), self.opp.loop
        ).result()
        assert 1 == len(self.mock_mp_2.service_calls["media_play"])

        asyncio.run_coroutine_threadsafe(
            ump.async_media_pause(), self.opp.loop
        ).result()
        assert 1 == len(self.mock_mp_2.service_calls["media_pause"])

        asyncio.run_coroutine_threadsafe(
            ump.async_media_stop(), self.opp.loop
        ).result()
        assert 1 == len(self.mock_mp_2.service_calls["media_stop"])

        asyncio.run_coroutine_threadsafe(
            ump.async_media_previous_track(), self.opp.loop
        ).result()
        assert 1 == len(self.mock_mp_2.service_calls["media_previous_track"])

        asyncio.run_coroutine_threadsafe(
            ump.async_media_next_track(), self.opp.loop
        ).result()
        assert 1 == len(self.mock_mp_2.service_calls["media_next_track"])

        asyncio.run_coroutine_threadsafe(
            ump.async_media_seek(100), self.opp.loop
        ).result()
        assert 1 == len(self.mock_mp_2.service_calls["media_seek"])

        asyncio.run_coroutine_threadsafe(
            ump.async_play_media("movie", "batman"), self.opp.loop
        ).result()
        assert 1 == len(self.mock_mp_2.service_calls["play_media"])

        asyncio.run_coroutine_threadsafe(ump.async_volume_up(), self.opp.loop).result()
        assert 1 == len(self.mock_mp_2.service_calls["volume_up"])

        asyncio.run_coroutine_threadsafe(
            ump.async_volume_down(), self.opp.loop
        ).result()
        assert 1 == len(self.mock_mp_2.service_calls["volume_down"])

        asyncio.run_coroutine_threadsafe(
            ump.async_media_play_pause(), self.opp.loop
        ).result()
        assert 1 == len(self.mock_mp_2.service_calls["media_play_pause"])

        asyncio.run_coroutine_threadsafe(
            ump.async_select_sound_mode("music"), self.opp.loop
        ).result()
        assert 1 == len(self.mock_mp_2.service_calls["select_sound_mode"])

        asyncio.run_coroutine_threadsafe(
            ump.async_select_source("dvd"), self.opp.loop
        ).result()
        assert 1 == len(self.mock_mp_2.service_calls["select_source"])

        asyncio.run_coroutine_threadsafe(
            ump.async_clear_playlist(), self.opp.loop
        ).result()
        assert 1 == len(self.mock_mp_2.service_calls["clear_playlist"])

        asyncio.run_coroutine_threadsafe(
            ump.async_set_repeat(True), self.opp.loop
        ).result()
        assert 1 == len(self.mock_mp_2.service_calls["repeat_set"])

        asyncio.run_coroutine_threadsafe(
            ump.async_set_shuffle(True), self.opp.loop
        ).result()
        assert 1 == len(self.mock_mp_2.service_calls["shuffle_set"])

        asyncio.run_coroutine_threadsafe(ump.async_toggle(), self.opp.loop).result()
        assert 1 == len(self.mock_mp_2.service_calls["toggle"])

    def test_service_call_to_command(self):
        """Test service call to command."""
        config = copy(self.config_children_only)
        config["commands"] = {"turn_off": {"service": "test.turn_off", "data": {}}}
        config = validate_config(config)

        service = mock_service(self.opp, "test", "turn_off")

        ump = universal.UniversalMediaPlayer(self.opp, **config)
        ump.entity_id = media_player.ENTITY_ID_FORMAT.format(config["name"])
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()

        self.mock_mp_2._state = STATE_PLAYING
        self.mock_mp_2.schedule_update_op_state()
        self.opp.block_till_done()
        asyncio.run_coroutine_threadsafe(ump.async_update(), self.opp.loop).result()

        asyncio.run_coroutine_threadsafe(ump.async_turn_off(), self.opp.loop).result()
        assert 1 == len(service)


async def test_state_template(opp):
    """Test with a simple valid state template."""
    opp.states.async_set("sensor.test_sensor", STATE_ON)

    await async_setup_component(
        opp,
        "media_player",
        {
            "media_player": {
                "platform": "universal",
                "name": "tv",
                "state_template": "{{ states.sensor.test_sensor.state }}",
            }
        },
    )
    await opp.async_block_till_done()
    assert len.opp.states.async_all()) == 2
    await opp.async_start()

    await opp.async_block_till_done()
    assert opp.states.get("media_player.tv").state == STATE_ON
    opp.states.async_set("sensor.test_sensor", STATE_OFF)
    await opp.async_block_till_done()
    assert opp.states.get("media_player.tv").state == STATE_OFF


async def test_device_class(opp):
    """Test device_class property."""
    opp.states.async_set("sensor.test_sensor", "on")

    await async_setup_component(
        opp,
        "media_player",
        {
            "media_player": {
                "platform": "universal",
                "name": "tv",
                "device_class": "tv",
            }
        },
    )
    await opp.async_block_till_done()
    assert opp.states.get("media_player.tv").attributes["device_class"] == "tv"


async def test_invalid_state_template(opp):
    """Test invalid state template sets state to None."""
    opp.states.async_set("sensor.test_sensor", "on")

    await async_setup_component(
        opp,
        "media_player",
        {
            "media_player": {
                "platform": "universal",
                "name": "tv",
                "state_template": "{{ states.sensor.test_sensor.state + x }}",
            }
        },
    )
    await opp.async_block_till_done()
    assert len.opp.states.async_all()) == 2
    await opp.async_start()

    await opp.async_block_till_done()
    assert opp.states.get("media_player.tv").state == STATE_UNKNOWN
    opp.states.async_set("sensor.test_sensor", "off")
    await opp.async_block_till_done()
    assert opp.states.get("media_player.tv").state == STATE_UNKNOWN


async def test_master_state_with_template(opp):
    """Test the state_template option."""
    opp.states.async_set("input_boolean.test", STATE_OFF)
    opp.states.async_set("media_player.mock1", STATE_OFF)

    templ = (
        '{% if states.input_boolean.test.state == "off" %}on'
        "{% else %}{{ states.media_player.mock1.state }}{% endif %}"
    )

    await async_setup_component(
        opp,
        "media_player",
        {
            "media_player": {
                "platform": "universal",
                "name": "tv",
                "state_template": templ,
            }
        },
    )

    await opp.async_block_till_done()
    assert len.opp.states.async_all()) == 3
    await opp.async_start()

    await opp.async_block_till_done()
    opp.states.get("media_player.tv").state == STATE_ON

    events = []

    opp.helpers.event.async_track_state_change_event(
        "media_player.tv", callback(lambda event: events.append(event))
    )

    context = Context()
    opp.states.async_set("input_boolean.test", STATE_ON, context=context)
    await opp.async_block_till_done()

    opp.states.get("media_player.tv").state == STATE_OFF
    assert events[0].context == context


async def test_reload(opp):
    """Test reloading the media player from yaml."""
    opp.states.async_set("input_boolean.test", STATE_OFF)
    opp.states.async_set("media_player.mock1", STATE_OFF)

    templ = (
        '{% if states.input_boolean.test.state == "off" %}on'
        "{% else %}{{ states.media_player.mock1.state }}{% endif %}"
    )

    await async_setup_component(
        opp,
        "media_player",
        {
            "media_player": {
                "platform": "universal",
                "name": "tv",
                "state_template": templ,
            }
        },
    )

    await opp.async_block_till_done()
    assert len.opp.states.async_all()) == 3
    await opp.async_start()

    await opp.async_block_till_done()
    opp.states.get("media_player.tv").state == STATE_ON

    opp.states.async_set("input_boolean.test", STATE_ON)
    await opp.async_block_till_done()

    opp.states.get("media_player.tv").state == STATE_OFF

    opp.states.async_set("media_player.master_bedroom_2", STATE_OFF)
    opp.states.async_set(
        "remote.alexander_master_bedroom",
        STATE_ON,
        {"activity_list": ["act1", "act2"], "current_activity": "act2"},
    )

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "universal/configuration.yaml",
    )
    with patch.object.opp_config, "YAML_CONFIG_FILE", yaml_path):
        await opp.services.async_call(
            "universal",
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 5

    assert opp.states.get("media_player.tv") is None
    assert opp.states.get("media_player.master_bed_tv").state == "on"
    assert opp.states.get("media_player.master_bed_tv").attributes["source"] == "act2"
    assert (
        "device_class" not in.opp.states.get("media_player.master_bed_tv").attributes
    )


def _get_fixtures_base_path():
    return path.dirname(path.dirname(path.dirname(__file__)))
