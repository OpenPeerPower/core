"""The tests for the Media group platform."""
from unittest.mock import patch

import pytest

from openpeerpower.components.group import DOMAIN
from openpeerpower.components.media_player import (
    ATTR_MEDIA_CONTENT_TYPE,
    ATTR_MEDIA_SEEK_POSITION,
    ATTR_MEDIA_SHUFFLE,
    ATTR_MEDIA_VOLUME_LEVEL,
    DOMAIN as MEDIA_DOMAIN,
    SERVICE_MEDIA_PAUSE,
    SERVICE_MEDIA_SEEK,
    SERVICE_PLAY_MEDIA,
    SERVICE_SHUFFLE_SET,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    SERVICE_VOLUME_SET,
    SUPPORT_PAUSE,
    SUPPORT_PLAY,
    SUPPORT_PLAY_MEDIA,
    SUPPORT_SEEK,
    SUPPORT_STOP,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_STEP,
)
from openpeerpower.components.media_player.const import (
    ATTR_MEDIA_CONTENT_ID,
    ATTR_MEDIA_TRACK,
    ATTR_MEDIA_VOLUME_MUTED,
    SERVICE_CLEAR_PLAYLIST,
)
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    SERVICE_MEDIA_NEXT_TRACK,
    SERVICE_MEDIA_PLAY,
    SERVICE_MEDIA_PREVIOUS_TRACK,
    SERVICE_MEDIA_STOP,
    SERVICE_VOLUME_DOWN,
    SERVICE_VOLUME_MUTE,
    SERVICE_VOLUME_UP,
    STATE_OFF,
    STATE_ON,
    STATE_PAUSED,
    STATE_PLAYING,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from openpeerpower.setup import async_setup_component


@pytest.fixture(name="mock_media_seek")
def media_player_media_seek_fixture():
    """Mock demo YouTube player media seek."""
    with patch(
        "openpeerpower.components.demo.media_player.DemoYoutubePlayer.media_seek",
        autospec=True,
    ) as seek:
        yield seek


async def test_default_state(opp):
    """Test media group default state."""
    opp.states.async_set("media_player.player_1", "on")
    await async_setup_component(
        opp,
        MEDIA_DOMAIN,
        {
            MEDIA_DOMAIN: {
                "platform": DOMAIN,
                "entities": ["media_player.player_1", "media_player.player_2"],
                "name": "Media group",
            }
        },
    )
    await opp.async_block_till_done()
    await opp.async_start()
    await opp.async_block_till_done()

    state = opp.states.get("media_player.media_group")
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0
    assert state.attributes.get(ATTR_ENTITY_ID) == [
        "media_player.player_1",
        "media_player.player_2",
    ]


async def test_state_reporting(opp):
    """Test the state reporting."""
    await async_setup_component(
        opp,
        MEDIA_DOMAIN,
        {
            MEDIA_DOMAIN: {
                "platform": DOMAIN,
                "entities": ["media_player.player_1", "media_player.player_2"],
            }
        },
    )
    await opp.async_block_till_done()
    await opp.async_start()
    await opp.async_block_till_done()

    assert opp.states.get("media_player.media_group").state == STATE_UNKNOWN

    opp.states.async_set("media_player.player_1", STATE_ON)
    opp.states.async_set("media_player.player_2", STATE_UNAVAILABLE)
    await opp.async_block_till_done()
    assert opp.states.get("media_player.media_group").state == STATE_ON

    opp.states.async_set("media_player.player_1", STATE_ON)
    opp.states.async_set("media_player.player_2", STATE_OFF)
    await opp.async_block_till_done()
    assert opp.states.get("media_player.media_group").state == STATE_ON

    opp.states.async_set("media_player.player_1", STATE_OFF)
    opp.states.async_set("media_player.player_2", STATE_UNAVAILABLE)
    await opp.async_block_till_done()
    assert opp.states.get("media_player.media_group").state == STATE_OFF

    opp.states.async_set("media_player.player_1", STATE_UNAVAILABLE)
    opp.states.async_set("media_player.player_2", STATE_UNAVAILABLE)
    await opp.async_block_till_done()
    assert opp.states.get("media_player.media_group").state == STATE_UNAVAILABLE


async def test_supported_features(opp):
    """Test supported features reporting."""
    pause_play_stop = SUPPORT_PAUSE | SUPPORT_PLAY | SUPPORT_STOP
    play_media = SUPPORT_PLAY_MEDIA
    volume = SUPPORT_VOLUME_MUTE | SUPPORT_VOLUME_SET | SUPPORT_VOLUME_STEP

    await async_setup_component(
        opp,
        MEDIA_DOMAIN,
        {
            MEDIA_DOMAIN: {
                "platform": DOMAIN,
                "entities": ["media_player.player_1", "media_player.player_2"],
            }
        },
    )
    await opp.async_block_till_done()
    await opp.async_start()
    await opp.async_block_till_done()

    opp.states.async_set(
        "media_player.player_1", STATE_ON, {ATTR_SUPPORTED_FEATURES: 0}
    )
    await opp.async_block_till_done()
    state = opp.states.get("media_player.media_group")
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0

    opp.states.async_set(
        "media_player.player_1",
        STATE_ON,
        {ATTR_SUPPORTED_FEATURES: pause_play_stop},
    )
    await opp.async_block_till_done()
    state = opp.states.get("media_player.media_group")
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == pause_play_stop

    opp.states.async_set(
        "media_player.player_2",
        STATE_OFF,
        {ATTR_SUPPORTED_FEATURES: play_media | volume},
    )
    await opp.async_block_till_done()
    state = opp.states.get("media_player.media_group")
    assert (
        state.attributes[ATTR_SUPPORTED_FEATURES]
        == pause_play_stop | play_media | volume
    )

    opp.states.async_set(
        "media_player.player_2", STATE_OFF, {ATTR_SUPPORTED_FEATURES: play_media}
    )
    await opp.async_block_till_done()
    state = opp.states.get("media_player.media_group")
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == pause_play_stop | play_media


async def test_service_calls(opp, mock_media_seek):
    """Test service calls."""
    await async_setup_component(
        opp,
        MEDIA_DOMAIN,
        {
            MEDIA_DOMAIN: [
                {"platform": "demo"},
                {
                    "platform": DOMAIN,
                    "entities": [
                        "media_player.bedroom",
                        "media_player.kitchen",
                        "media_player.living_room",
                    ],
                },
            ]
        },
    )
    await opp.async_block_till_done()
    await opp.async_start()
    await opp.async_block_till_done()

    assert opp.states.get("media_player.media_group").state == STATE_PLAYING
    await opp.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "media_player.media_group"},
        blocking=True,
    )

    await opp.async_block_till_done()
    assert opp.states.get("media_player.bedroom").state == STATE_OFF
    assert opp.states.get("media_player.kitchen").state == STATE_OFF
    assert opp.states.get("media_player.living_room").state == STATE_OFF

    await opp.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "media_player.media_group"},
        blocking=True,
    )
    await opp.async_block_till_done()
    assert opp.states.get("media_player.bedroom").state == STATE_PLAYING
    assert opp.states.get("media_player.kitchen").state == STATE_PLAYING
    assert opp.states.get("media_player.living_room").state == STATE_PLAYING

    await opp.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_MEDIA_PAUSE,
        {ATTR_ENTITY_ID: "media_player.media_group"},
        blocking=True,
    )
    await opp.async_block_till_done()
    assert opp.states.get("media_player.bedroom").state == STATE_PAUSED
    assert opp.states.get("media_player.kitchen").state == STATE_PAUSED
    assert opp.states.get("media_player.living_room").state == STATE_PAUSED

    await opp.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_MEDIA_PLAY,
        {ATTR_ENTITY_ID: "media_player.media_group"},
        blocking=True,
    )
    await opp.async_block_till_done()
    assert opp.states.get("media_player.bedroom").state == STATE_PLAYING
    assert opp.states.get("media_player.kitchen").state == STATE_PLAYING
    assert opp.states.get("media_player.living_room").state == STATE_PLAYING

    # ATTR_MEDIA_TRACK is not supported by bedroom and living_room players
    assert opp.states.get("media_player.kitchen").attributes[ATTR_MEDIA_TRACK] == 1
    await opp.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_MEDIA_NEXT_TRACK,
        {ATTR_ENTITY_ID: "media_player.media_group"},
        blocking=True,
    )
    await opp.async_block_till_done()
    assert opp.states.get("media_player.kitchen").attributes[ATTR_MEDIA_TRACK] == 2

    await opp.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_MEDIA_PREVIOUS_TRACK,
        {ATTR_ENTITY_ID: "media_player.media_group"},
        blocking=True,
    )
    await opp.async_block_till_done()
    assert opp.states.get("media_player.kitchen").attributes[ATTR_MEDIA_TRACK] == 1

    await opp.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_PLAY_MEDIA,
        {
            ATTR_ENTITY_ID: "media_player.media_group",
            ATTR_MEDIA_CONTENT_TYPE: "some_type",
            ATTR_MEDIA_CONTENT_ID: "some_id",
        },
    )
    await opp.async_block_till_done()
    assert (
        opp.states.get("media_player.bedroom").attributes[ATTR_MEDIA_CONTENT_ID]
        == "some_id"
    )
    # media_player.kitchen is skipped because it always returns "bounzz-1"
    assert (
        opp.states.get("media_player.living_room").attributes[ATTR_MEDIA_CONTENT_ID]
        == "some_id"
    )

    state = opp.states.get("media_player.media_group")
    assert state.attributes[ATTR_SUPPORTED_FEATURES] & SUPPORT_SEEK
    assert not mock_media_seek.called

    await opp.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_MEDIA_SEEK,
        {
            ATTR_ENTITY_ID: "media_player.media_group",
            ATTR_MEDIA_SEEK_POSITION: 100,
        },
    )
    await opp.async_block_till_done()
    assert mock_media_seek.called

    assert (
        opp.states.get("media_player.bedroom").attributes[ATTR_MEDIA_VOLUME_LEVEL] == 1
    )
    assert (
        opp.states.get("media_player.kitchen").attributes[ATTR_MEDIA_VOLUME_LEVEL] == 1
    )
    assert (
        opp.states.get("media_player.living_room").attributes[ATTR_MEDIA_VOLUME_LEVEL]
        == 1
    )
    await opp.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_VOLUME_SET,
        {
            ATTR_ENTITY_ID: "media_player.media_group",
            ATTR_MEDIA_VOLUME_LEVEL: 0.5,
        },
        blocking=True,
    )
    await opp.async_block_till_done()
    assert (
        opp.states.get("media_player.bedroom").attributes[ATTR_MEDIA_VOLUME_LEVEL]
        == 0.5
    )
    assert (
        opp.states.get("media_player.kitchen").attributes[ATTR_MEDIA_VOLUME_LEVEL]
        == 0.5
    )
    assert (
        opp.states.get("media_player.living_room").attributes[ATTR_MEDIA_VOLUME_LEVEL]
        == 0.5
    )

    await opp.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_VOLUME_UP,
        {ATTR_ENTITY_ID: "media_player.media_group"},
        blocking=True,
    )
    await opp.async_block_till_done()
    assert (
        opp.states.get("media_player.bedroom").attributes[ATTR_MEDIA_VOLUME_LEVEL]
        == 0.6
    )
    assert (
        opp.states.get("media_player.kitchen").attributes[ATTR_MEDIA_VOLUME_LEVEL]
        == 0.6
    )
    assert (
        opp.states.get("media_player.living_room").attributes[ATTR_MEDIA_VOLUME_LEVEL]
        == 0.6
    )

    await opp.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_VOLUME_DOWN,
        {ATTR_ENTITY_ID: "media_player.media_group"},
        blocking=True,
    )
    await opp.async_block_till_done()
    assert (
        opp.states.get("media_player.bedroom").attributes[ATTR_MEDIA_VOLUME_LEVEL]
        == 0.5
    )
    assert (
        opp.states.get("media_player.kitchen").attributes[ATTR_MEDIA_VOLUME_LEVEL]
        == 0.5
    )
    assert (
        opp.states.get("media_player.living_room").attributes[ATTR_MEDIA_VOLUME_LEVEL]
        == 0.5
    )

    assert (
        opp.states.get("media_player.bedroom").attributes[ATTR_MEDIA_VOLUME_MUTED]
        is False
    )
    assert (
        opp.states.get("media_player.kitchen").attributes[ATTR_MEDIA_VOLUME_MUTED]
        is False
    )
    assert (
        opp.states.get("media_player.living_room").attributes[ATTR_MEDIA_VOLUME_MUTED]
        is False
    )
    await opp.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_VOLUME_MUTE,
        {ATTR_ENTITY_ID: "media_player.media_group", ATTR_MEDIA_VOLUME_MUTED: True},
        blocking=True,
    )
    await opp.async_block_till_done()
    assert (
        opp.states.get("media_player.bedroom").attributes[ATTR_MEDIA_VOLUME_MUTED]
        is True
    )
    assert (
        opp.states.get("media_player.kitchen").attributes[ATTR_MEDIA_VOLUME_MUTED]
        is True
    )
    assert (
        opp.states.get("media_player.living_room").attributes[ATTR_MEDIA_VOLUME_MUTED]
        is True
    )

    assert (
        opp.states.get("media_player.bedroom").attributes[ATTR_MEDIA_SHUFFLE] is False
    )
    assert (
        opp.states.get("media_player.kitchen").attributes[ATTR_MEDIA_SHUFFLE] is False
    )
    assert (
        opp.states.get("media_player.living_room").attributes[ATTR_MEDIA_SHUFFLE]
        is False
    )
    await opp.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_SHUFFLE_SET,
        {ATTR_ENTITY_ID: "media_player.media_group", ATTR_MEDIA_SHUFFLE: True},
        blocking=True,
    )
    await opp.async_block_till_done()
    assert (
        opp.states.get("media_player.bedroom").attributes[ATTR_MEDIA_SHUFFLE] is True
    )
    assert (
        opp.states.get("media_player.kitchen").attributes[ATTR_MEDIA_SHUFFLE] is True
    )
    assert (
        opp.states.get("media_player.living_room").attributes[ATTR_MEDIA_SHUFFLE]
        is True
    )

    assert opp.states.get("media_player.bedroom").state == STATE_PLAYING
    assert opp.states.get("media_player.kitchen").state == STATE_PLAYING
    assert opp.states.get("media_player.living_room").state == STATE_PLAYING
    await opp.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_CLEAR_PLAYLIST,
        {ATTR_ENTITY_ID: "media_player.media_group"},
        blocking=True,
    )
    await opp.async_block_till_done()
    # SERVICE_CLEAR_PLAYLIST is not supported by bedroom and living_room players
    assert opp.states.get("media_player.kitchen").state == STATE_OFF

    await opp.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_MEDIA_PLAY,
        {ATTR_ENTITY_ID: "media_player.kitchen"},
        blocking=True,
    )
    await opp.async_block_till_done()
    assert opp.states.get("media_player.bedroom").state == STATE_PLAYING
    assert opp.states.get("media_player.kitchen").state == STATE_PLAYING
    assert opp.states.get("media_player.living_room").state == STATE_PLAYING
    await opp.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_MEDIA_STOP,
        {ATTR_ENTITY_ID: "media_player.media_group"},
        blocking=True,
    )
    await opp.async_block_till_done()
    assert opp.states.get("media_player.bedroom").state == STATE_OFF
    assert opp.states.get("media_player.kitchen").state == STATE_OFF
    assert opp.states.get("media_player.living_room").state == STATE_OFF


async def test_nested_group(opp):
    """Test nested media group."""
    opp.states.async_set("media_player.player_1", "on")
    await async_setup_component(
        opp,
        MEDIA_DOMAIN,
        {
            MEDIA_DOMAIN: [
                {
                    "platform": DOMAIN,
                    "entities": ["media_player.group_1"],
                    "name": "Nested Group",
                },
                {
                    "platform": DOMAIN,
                    "entities": ["media_player.player_1", "media_player.player_2"],
                    "name": "Group 1",
                },
            ]
        },
    )
    await opp.async_block_till_done()
    await opp.async_start()
    await opp.async_block_till_done()

    state = opp.states.get("media_player.group_1")
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_ENTITY_ID) == [
        "media_player.player_1",
        "media_player.player_2",
    ]

    state = opp.states.get("media_player.nested_group")
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_ENTITY_ID) == ["media_player.group_1"]
