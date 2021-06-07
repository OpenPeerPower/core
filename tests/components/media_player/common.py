"""Collection of helper methods.

All containing methods are legacy helpers that should not be used by new
components. Instead call the service directly.
"""
from openpeerpower.components.media_player.const import (
    ATTR_INPUT_SOURCE,
    ATTR_MEDIA_CONTENT_ID,
    ATTR_MEDIA_CONTENT_TYPE,
    ATTR_MEDIA_ENQUEUE,
    ATTR_MEDIA_SEEK_POSITION,
    ATTR_MEDIA_VOLUME_LEVEL,
    ATTR_MEDIA_VOLUME_MUTED,
    DOMAIN,
    SERVICE_CLEAR_PLAYLIST,
    SERVICE_PLAY_MEDIA,
    SERVICE_SELECT_SOURCE,
)
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ENTITY_MATCH_ALL,
    SERVICE_MEDIA_NEXT_TRACK,
    SERVICE_MEDIA_PAUSE,
    SERVICE_MEDIA_PLAY,
    SERVICE_MEDIA_PLAY_PAUSE,
    SERVICE_MEDIA_PREVIOUS_TRACK,
    SERVICE_MEDIA_SEEK,
    SERVICE_MEDIA_STOP,
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    SERVICE_VOLUME_DOWN,
    SERVICE_VOLUME_MUTE,
    SERVICE_VOLUME_SET,
    SERVICE_VOLUME_UP,
)
from openpeerpower.loader import bind_opp


async def async_turn_on(opp, entity_id=ENTITY_MATCH_ALL):
    """Turn on specified media player or all."""
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else {}
    await opp.services.async_call(DOMAIN, SERVICE_TURN_ON, data, blocking=True)


@bind_opp
def turn_on(opp, entity_id=ENTITY_MATCH_ALL):
    """Turn on specified media player or all."""
    opp.add_job(async_turn_on, opp, entity_id)


async def async_turn_off(opp, entity_id=ENTITY_MATCH_ALL):
    """Turn off specified media player or all."""
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else {}
    await opp.services.async_call(DOMAIN, SERVICE_TURN_OFF, data, blocking=True)


@bind_opp
def turn_off(opp, entity_id=ENTITY_MATCH_ALL):
    """Turn off specified media player or all."""
    opp.add_job(async_turn_off, opp, entity_id)


async def async_toggle(opp, entity_id=ENTITY_MATCH_ALL):
    """Toggle specified media player or all."""
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else {}
    await opp.services.async_call(DOMAIN, SERVICE_TOGGLE, data, blocking=True)


@bind_opp
def toggle(opp, entity_id=ENTITY_MATCH_ALL):
    """Toggle specified media player or all."""
    opp.add_job(async_toggle, opp, entity_id)


async def async_volume_up(opp, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command for volume up."""
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else {}
    await opp.services.async_call(DOMAIN, SERVICE_VOLUME_UP, data, blocking=True)


@bind_opp
def volume_up(opp, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command for volume up."""
    opp.add_job(async_volume_up, opp, entity_id)


async def async_volume_down(opp, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command for volume down."""
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else {}
    await opp.services.async_call(DOMAIN, SERVICE_VOLUME_DOWN, data, blocking=True)


@bind_opp
def volume_down(opp, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command for volume down."""
    opp.add_job(async_volume_down, opp, entity_id)


async def async_mute_volume(opp, mute, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command for muting the volume."""
    data = {ATTR_MEDIA_VOLUME_MUTED: mute}

    if entity_id:
        data[ATTR_ENTITY_ID] = entity_id

    await opp.services.async_call(DOMAIN, SERVICE_VOLUME_MUTE, data, blocking=True)


@bind_opp
def mute_volume(opp, mute, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command for muting the volume."""
    opp.add_job(async_mute_volume, opp, mute, entity_id)


async def async_set_volume_level(opp, volume, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command for setting the volume."""
    data = {ATTR_MEDIA_VOLUME_LEVEL: volume}

    if entity_id:
        data[ATTR_ENTITY_ID] = entity_id

    await opp.services.async_call(DOMAIN, SERVICE_VOLUME_SET, data, blocking=True)


@bind_opp
def set_volume_level(opp, volume, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command for setting the volume."""
    opp.add_job(async_set_volume_level, opp, volume, entity_id)


async def async_media_play_pause(opp, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command for play/pause."""
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else {}
    await opp.services.async_call(
        DOMAIN, SERVICE_MEDIA_PLAY_PAUSE, data, blocking=True
    )


@bind_opp
def media_play_pause(opp, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command for play/pause."""
    opp.add_job(async_media_play_pause, opp, entity_id)


async def async_media_play(opp, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command for play/pause."""
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else {}
    await opp.services.async_call(DOMAIN, SERVICE_MEDIA_PLAY, data, blocking=True)


@bind_opp
def media_play(opp, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command for play/pause."""
    opp.add_job(async_media_play, opp, entity_id)


async def async_media_pause(opp, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command for pause."""
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else {}
    await opp.services.async_call(DOMAIN, SERVICE_MEDIA_PAUSE, data, blocking=True)


@bind_opp
def media_pause(opp, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command for pause."""
    opp.add_job(async_media_pause, opp, entity_id)


async def async_media_stop(opp, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command for stop."""
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else {}
    await opp.services.async_call(DOMAIN, SERVICE_MEDIA_STOP, data, blocking=True)


@bind_opp
def media_stop(opp, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command for stop."""
    opp.add_job(async_media_stop, opp, entity_id)


async def async_media_next_track(opp, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command for next track."""
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else {}
    await opp.services.async_call(
        DOMAIN, SERVICE_MEDIA_NEXT_TRACK, data, blocking=True
    )


@bind_opp
def media_next_track(opp, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command for next track."""
    opp.add_job(async_media_next_track, opp, entity_id)


async def async_media_previous_track(opp, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command for prev track."""
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else {}
    await opp.services.async_call(
        DOMAIN, SERVICE_MEDIA_PREVIOUS_TRACK, data, blocking=True
    )


@bind_opp
def media_previous_track(opp, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command for prev track."""
    opp.add_job(async_media_previous_track, opp, entity_id)


async def async_media_seek(opp, position, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command to seek in current playing media."""
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else {}
    data[ATTR_MEDIA_SEEK_POSITION] = position
    await opp.services.async_call(DOMAIN, SERVICE_MEDIA_SEEK, data, blocking=True)


@bind_opp
def media_seek(opp, position, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command to seek in current playing media."""
    opp.add_job(async_media_seek, opp, position, entity_id)


async def async_play_media(
    opp, media_type, media_id, entity_id=ENTITY_MATCH_ALL, enqueue=None
):
    """Send the media player the command for playing media."""
    data = {ATTR_MEDIA_CONTENT_TYPE: media_type, ATTR_MEDIA_CONTENT_ID: media_id}

    if entity_id:
        data[ATTR_ENTITY_ID] = entity_id

    if enqueue:
        data[ATTR_MEDIA_ENQUEUE] = enqueue

    await opp.services.async_call(DOMAIN, SERVICE_PLAY_MEDIA, data, blocking=True)


@bind_opp
def play_media(opp, media_type, media_id, entity_id=ENTITY_MATCH_ALL, enqueue=None):
    """Send the media player the command for playing media."""
    opp.add_job(async_play_media, opp, media_type, media_id, entity_id, enqueue)


async def async_select_source(opp, source, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command to select input source."""
    data = {ATTR_INPUT_SOURCE: source}

    if entity_id:
        data[ATTR_ENTITY_ID] = entity_id

    await opp.services.async_call(DOMAIN, SERVICE_SELECT_SOURCE, data, blocking=True)


@bind_opp
def select_source(opp, source, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command to select input source."""
    opp.add_job(async_select_source, opp, source, entity_id)


async def async_clear_playlist(opp, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command for clear playlist."""
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else {}
    await opp.services.async_call(DOMAIN, SERVICE_CLEAR_PLAYLIST, data, blocking=True)


@bind_opp
def clear_playlist(opp, entity_id=ENTITY_MATCH_ALL):
    """Send the media player the command for clear playlist."""
    opp.add_job(async_clear_playlist, opp, entity_id)
