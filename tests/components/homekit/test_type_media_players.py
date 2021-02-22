"""Test different accessory types: Media Players."""

from openpeerpower.components.homekit.const import (
    ATTR_KEY_NAME,
    ATTR_VALUE,
    CHAR_REMOTE_KEY,
    CONF_FEATURE_LIST,
    EVENT_HOMEKIT_TV_REMOTE_KEY_PRESSED,
    FEATURE_ON_OFF,
    FEATURE_PLAY_PAUSE,
    FEATURE_PLAY_STOP,
    FEATURE_TOGGLE_MUTE,
    KEY_ARROW_RIGHT,
)
from openpeerpower.components.homekit.type_media_players import (
    MediaPlayer,
    TelevisionMediaPlayer,
)
from openpeerpower.components.media_player import DEVICE_CLASS_TV
from openpeerpower.components.media_player.const import (
    ATTR_INPUT_SOURCE,
    ATTR_INPUT_SOURCE_LIST,
    ATTR_MEDIA_VOLUME_LEVEL,
    ATTR_MEDIA_VOLUME_MUTED,
    DOMAIN,
)
from openpeerpower.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    EVENT_OPENPEERPOWER_START,
    STATE_IDLE,
    STATE_OFF,
    STATE_ON,
    STATE_PAUSED,
    STATE_PLAYING,
    STATE_STANDBY,
)
from openpeerpower.core import CoreState
from openpeerpower.helpers import entity_registry

from tests.common import async_mock_service


async def test_media_player_set_state.opp, hk_driver, events):
    """Test if accessory and HA are updated accordingly."""
    config = {
        CONF_FEATURE_LIST: {
            FEATURE_ON_OFF: None,
            FEATURE_PLAY_PAUSE: None,
            FEATURE_PLAY_STOP: None,
            FEATURE_TOGGLE_MUTE: None,
        }
    }
    entity_id = "media_player.test"

    opp.states.async_set(
        entity_id,
        None,
        {ATTR_SUPPORTED_FEATURES: 20873, ATTR_MEDIA_VOLUME_MUTED: False},
    )
    await opp.async_block_till_done()
    acc = MediaPlayer.opp, hk_driver, "MediaPlayer", entity_id, 2, config)
    await acc.run()
    await opp.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 8  # Switch

    assert acc.chars[FEATURE_ON_OFF].value is False
    assert acc.chars[FEATURE_PLAY_PAUSE].value is False
    assert acc.chars[FEATURE_PLAY_STOP].value is False
    assert acc.chars[FEATURE_TOGGLE_MUTE].value is False

    opp.states.async_set(entity_id, STATE_ON, {ATTR_MEDIA_VOLUME_MUTED: True})
    await opp.async_block_till_done()
    assert acc.chars[FEATURE_ON_OFF].value is True
    assert acc.chars[FEATURE_TOGGLE_MUTE].value is True

    opp.states.async_set(entity_id, STATE_OFF)
    await opp.async_block_till_done()
    assert acc.chars[FEATURE_ON_OFF].value is False

    opp.states.async_set(entity_id, STATE_ON)
    await opp.async_block_till_done()
    assert acc.chars[FEATURE_ON_OFF].value is True

    opp.states.async_set(entity_id, STATE_STANDBY)
    await opp.async_block_till_done()
    assert acc.chars[FEATURE_ON_OFF].value is False

    opp.states.async_set(entity_id, STATE_PLAYING)
    await opp.async_block_till_done()
    assert acc.chars[FEATURE_PLAY_PAUSE].value is True
    assert acc.chars[FEATURE_PLAY_STOP].value is True

    opp.states.async_set(entity_id, STATE_PAUSED)
    await opp.async_block_till_done()
    assert acc.chars[FEATURE_PLAY_PAUSE].value is False

    opp.states.async_set(entity_id, STATE_IDLE)
    await opp.async_block_till_done()
    assert acc.chars[FEATURE_PLAY_STOP].value is False

    # Set from HomeKit
    call_turn_on = async_mock_service.opp, DOMAIN, "turn_on")
    call_turn_off = async_mock_service.opp, DOMAIN, "turn_off")
    call_media_play = async_mock_service.opp, DOMAIN, "media_play")
    call_media_pause = async_mock_service.opp, DOMAIN, "media_pause")
    call_media_stop = async_mock_service.opp, DOMAIN, "media_stop")
    call_toggle_mute = async_mock_service.opp, DOMAIN, "volume_mute")

    await opp.async_add_executor_job(
        acc.chars[FEATURE_ON_OFF].client_update_value, True
    )
    await opp.async_block_till_done()
    assert call_turn_on
    assert call_turn_on[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] is None

    await opp.async_add_executor_job(
        acc.chars[FEATURE_ON_OFF].client_update_value, False
    )
    await opp.async_block_till_done()
    assert call_turn_off
    assert call_turn_off[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] is None

    await opp.async_add_executor_job(
        acc.chars[FEATURE_PLAY_PAUSE].client_update_value, True
    )
    await opp.async_block_till_done()
    assert call_media_play
    assert call_media_play[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 3
    assert events[-1].data[ATTR_VALUE] is None

    await opp.async_add_executor_job(
        acc.chars[FEATURE_PLAY_PAUSE].client_update_value, False
    )
    await opp.async_block_till_done()
    assert call_media_pause
    assert call_media_pause[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 4
    assert events[-1].data[ATTR_VALUE] is None

    await opp.async_add_executor_job(
        acc.chars[FEATURE_PLAY_STOP].client_update_value, True
    )
    await opp.async_block_till_done()
    assert call_media_play
    assert call_media_play[1].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 5
    assert events[-1].data[ATTR_VALUE] is None

    await opp.async_add_executor_job(
        acc.chars[FEATURE_PLAY_STOP].client_update_value, False
    )
    await opp.async_block_till_done()
    assert call_media_stop
    assert call_media_stop[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 6
    assert events[-1].data[ATTR_VALUE] is None

    await opp.async_add_executor_job(
        acc.chars[FEATURE_TOGGLE_MUTE].client_update_value, True
    )
    await opp.async_block_till_done()
    assert call_toggle_mute
    assert call_toggle_mute[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_toggle_mute[0].data[ATTR_MEDIA_VOLUME_MUTED] is True
    assert len(events) == 7
    assert events[-1].data[ATTR_VALUE] is None

    await opp.async_add_executor_job(
        acc.chars[FEATURE_TOGGLE_MUTE].client_update_value, False
    )
    await opp.async_block_till_done()
    assert call_toggle_mute
    assert call_toggle_mute[1].data[ATTR_ENTITY_ID] == entity_id
    assert call_toggle_mute[1].data[ATTR_MEDIA_VOLUME_MUTED] is False
    assert len(events) == 8
    assert events[-1].data[ATTR_VALUE] is None


async def test_media_player_television.opp, hk_driver, events, caplog):
    """Test if television accessory and HA are updated accordingly."""
    entity_id = "media_player.television"

    # Supports 'select_source', 'volume_step', 'turn_on', 'turn_off',
    #       'volume_mute', 'volume_set', 'pause'
    opp.states.async_set(
        entity_id,
        None,
        {
            ATTR_DEVICE_CLASS: DEVICE_CLASS_TV,
            ATTR_SUPPORTED_FEATURES: 3469,
            ATTR_MEDIA_VOLUME_MUTED: False,
            ATTR_INPUT_SOURCE_LIST: ["HDMI 1", "HDMI 2", "HDMI 3", "HDMI 4"],
        },
    )
    await opp.async_block_till_done()
    acc = TelevisionMediaPlayer.opp, hk_driver, "MediaPlayer", entity_id, 2, None)
    await acc.run()
    await opp.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 31  # Television

    assert acc.char_active.value == 0
    assert acc.char_remote_key.value == 0
    assert acc.char_input_source.value == 0
    assert acc.char_mute.value is False

    opp.states.async_set(entity_id, STATE_ON, {ATTR_MEDIA_VOLUME_MUTED: True})
    await opp.async_block_till_done()
    assert acc.char_active.value == 1
    assert acc.char_mute.value is True

    opp.states.async_set(entity_id, STATE_OFF)
    await opp.async_block_till_done()
    assert acc.char_active.value == 0

    opp.states.async_set(entity_id, STATE_ON)
    await opp.async_block_till_done()
    assert acc.char_active.value == 1

    opp.states.async_set(entity_id, STATE_STANDBY)
    await opp.async_block_till_done()
    assert acc.char_active.value == 0

    opp.states.async_set(entity_id, STATE_ON, {ATTR_INPUT_SOURCE: "HDMI 2"})
    await opp.async_block_till_done()
    assert acc.char_input_source.value == 1

    opp.states.async_set(entity_id, STATE_ON, {ATTR_INPUT_SOURCE: "HDMI 3"})
    await opp.async_block_till_done()
    assert acc.char_input_source.value == 2

    opp.states.async_set(entity_id, STATE_ON, {ATTR_INPUT_SOURCE: "HDMI 5"})
    await opp.async_block_till_done()
    assert acc.char_input_source.value == 0
    assert caplog.records[-2].levelname == "WARNING"

    # Set from HomeKit
    call_turn_on = async_mock_service.opp, DOMAIN, "turn_on")
    call_turn_off = async_mock_service.opp, DOMAIN, "turn_off")
    call_media_play = async_mock_service.opp, DOMAIN, "media_play")
    call_media_pause = async_mock_service.opp, DOMAIN, "media_pause")
    call_media_play_pause = async_mock_service.opp, DOMAIN, "media_play_pause")
    call_toggle_mute = async_mock_service.opp, DOMAIN, "volume_mute")
    call_select_source = async_mock_service.opp, DOMAIN, "select_source")
    call_volume_up = async_mock_service.opp, DOMAIN, "volume_up")
    call_volume_down = async_mock_service.opp, DOMAIN, "volume_down")
    call_volume_set = async_mock_service.opp, DOMAIN, "volume_set")

    await opp.async_add_executor_job(acc.char_active.client_update_value, 1)
    await opp.async_block_till_done()
    assert call_turn_on
    assert call_turn_on[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] is None

    await opp.async_add_executor_job(acc.char_active.client_update_value, 0)
    await opp.async_block_till_done()
    assert call_turn_off
    assert call_turn_off[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] is None

    await opp.async_add_executor_job(acc.char_remote_key.client_update_value, 11)
    await opp.async_block_till_done()
    assert call_media_play_pause
    assert call_media_play_pause[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 3
    assert events[-1].data[ATTR_VALUE] is None

    opp.states.async_set(entity_id, STATE_PLAYING)
    await opp.async_block_till_done()
    await opp.async_add_executor_job(acc.char_remote_key.client_update_value, 11)
    await opp.async_block_till_done()
    assert call_media_pause
    assert call_media_pause[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 4
    assert events[-1].data[ATTR_VALUE] is None

    await opp.async_add_executor_job(acc.char_remote_key.client_update_value, 10)
    await opp.async_block_till_done()
    assert len(events) == 4
    assert events[-1].data[ATTR_VALUE] is None

    opp.states.async_set(entity_id, STATE_PAUSED)
    await opp.async_block_till_done()
    await opp.async_add_executor_job(acc.char_remote_key.client_update_value, 11)
    await opp.async_block_till_done()
    assert call_media_play
    assert call_media_play[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 5
    assert events[-1].data[ATTR_VALUE] is None

    await opp.async_add_executor_job(acc.char_mute.client_update_value, True)
    await opp.async_block_till_done()
    assert call_toggle_mute
    assert call_toggle_mute[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_toggle_mute[0].data[ATTR_MEDIA_VOLUME_MUTED] is True
    assert len(events) == 6
    assert events[-1].data[ATTR_VALUE] is None

    await opp.async_add_executor_job(acc.char_mute.client_update_value, False)
    await opp.async_block_till_done()
    assert call_toggle_mute
    assert call_toggle_mute[1].data[ATTR_ENTITY_ID] == entity_id
    assert call_toggle_mute[1].data[ATTR_MEDIA_VOLUME_MUTED] is False
    assert len(events) == 7
    assert events[-1].data[ATTR_VALUE] is None

    await opp.async_add_executor_job(acc.char_input_source.client_update_value, 1)
    await opp.async_block_till_done()
    assert call_select_source
    assert call_select_source[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_select_source[0].data[ATTR_INPUT_SOURCE] == "HDMI 2"
    assert len(events) == 8
    assert events[-1].data[ATTR_VALUE] is None

    await opp.async_add_executor_job(acc.char_volume_selector.client_update_value, 0)
    await opp.async_block_till_done()
    assert call_volume_up
    assert call_volume_up[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 9
    assert events[-1].data[ATTR_VALUE] is None

    await opp.async_add_executor_job(acc.char_volume_selector.client_update_value, 1)
    await opp.async_block_till_done()
    assert call_volume_down
    assert call_volume_down[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 10
    assert events[-1].data[ATTR_VALUE] is None

    await opp.async_add_executor_job(acc.char_volume.client_update_value, 20)
    await opp.async_block_till_done()
    assert call_volume_set[0]
    assert call_volume_set[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_volume_set[0].data[ATTR_MEDIA_VOLUME_LEVEL] == 20
    assert len(events) == 11
    assert events[-1].data[ATTR_VALUE] is None

    events = []

    def listener(event):
        events.append(event)

    opp.bus.async_listen(EVENT_HOMEKIT_TV_REMOTE_KEY_PRESSED, listener)

    await opp.async_add_executor_job(acc.char_remote_key.client_update_value, 20)
    await opp.async_block_till_done()

    await opp.async_add_executor_job(acc.char_remote_key.client_update_value, 7)
    await opp.async_block_till_done()

    assert len(events) == 1
    assert events[0].data[ATTR_KEY_NAME] == KEY_ARROW_RIGHT


async def test_media_player_television_basic.opp, hk_driver, events, caplog):
    """Test if basic television accessory and HA are updated accordingly."""
    entity_id = "media_player.television"

    # Supports turn_on', 'turn_off'
    opp.states.async_set(
        entity_id,
        None,
        {ATTR_DEVICE_CLASS: DEVICE_CLASS_TV, ATTR_SUPPORTED_FEATURES: 384},
    )
    await opp.async_block_till_done()
    acc = TelevisionMediaPlayer.opp, hk_driver, "MediaPlayer", entity_id, 2, None)
    await acc.run()
    await opp.async_block_till_done()

    assert acc.chars_tv == [CHAR_REMOTE_KEY]
    assert acc.chars_speaker == []
    assert acc.support_select_source is False

    opp.states.async_set(entity_id, STATE_ON, {ATTR_MEDIA_VOLUME_MUTED: True})
    await opp.async_block_till_done()
    assert acc.char_active.value == 1

    opp.states.async_set(entity_id, STATE_OFF)
    await opp.async_block_till_done()
    assert acc.char_active.value == 0

    opp.states.async_set(entity_id, STATE_ON, {ATTR_INPUT_SOURCE: "HDMI 3"})
    await opp.async_block_till_done()
    assert acc.char_active.value == 1

    assert not caplog.messages or "Error" not in caplog.messages[-1]


async def test_media_player_television_supports_source_select_no_sources(
    opp. hk_driver, events, caplog
):
    """Test if basic tv that supports source select but is missing a source list."""
    entity_id = "media_player.television"

    # Supports turn_on', 'turn_off'
    opp.states.async_set(
        entity_id,
        None,
        {ATTR_DEVICE_CLASS: DEVICE_CLASS_TV, ATTR_SUPPORTED_FEATURES: 3469},
    )
    await opp.async_block_till_done()
    acc = TelevisionMediaPlayer.opp, hk_driver, "MediaPlayer", entity_id, 2, None)
    await acc.run()
    await opp.async_block_till_done()

    assert acc.support_select_source is False


async def test_tv_restore.opp, hk_driver, events):
    """Test setting up an entity from state in the event registry."""
    opp.state = CoreState.not_running

    registry = await entity_registry.async_get_registry.opp)

    registry.async_get_or_create(
        "media_player",
        "generic",
        "1234",
        suggested_object_id="simple",
        device_class=DEVICE_CLASS_TV,
    )
    registry.async_get_or_create(
        "media_player",
        "generic",
        "9012",
        suggested_object_id="all_info_set",
        capabilities={
            ATTR_INPUT_SOURCE_LIST: ["HDMI 1", "HDMI 2", "HDMI 3", "HDMI 4"],
        },
        supported_features=3469,
        device_class=DEVICE_CLASS_TV,
    )

    opp.bus.async_fire(EVENT_OPENPEERPOWER_START, {})
    await opp.async_block_till_done()

    acc = TelevisionMediaPlayer(
        opp. hk_driver, "MediaPlayer", "media_player.simple", 2, None
    )
    assert acc.category == 31
    assert acc.chars_tv == [CHAR_REMOTE_KEY]
    assert acc.chars_speaker == []
    assert acc.support_select_source is False
    assert not hasattr(acc, "char_input_source")

    acc = TelevisionMediaPlayer(
        opp. hk_driver, "MediaPlayer", "media_player.all_info_set", 2, None
    )
    assert acc.category == 31
    assert acc.chars_tv == [CHAR_REMOTE_KEY]
    assert acc.chars_speaker == [
        "Name",
        "Active",
        "VolumeControlType",
        "VolumeSelector",
        "Volume",
    ]
    assert acc.support_select_source is True
    assert acc.char_input_source is not None
