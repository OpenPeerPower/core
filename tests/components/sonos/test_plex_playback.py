"""Tests for the Sonos Media Player platform."""
from unittest.mock import patch

import pytest

from openpeerpower.components.media_player.const import (
    ATTR_MEDIA_CONTENT_ID,
    ATTR_MEDIA_CONTENT_TYPE,
    DOMAIN as MP_DOMAIN,
    MEDIA_TYPE_MUSIC,
    SERVICE_PLAY_MEDIA,
)
from openpeerpower.components.plex.const import PLEX_URI_SCHEME
from openpeerpower.const import ATTR_ENTITY_ID
from openpeerpower.exceptions import OpenPeerPowerError

from .test_media_player import setup_platform


async def test_plex_play_media(
   .opp,
    config_entry,
    config,
):
    """Test playing media via the Plex integration."""
    await setup_platform.opp, config_entry, config)
    media_player = "media_player.zone_a"
    media_content_id = (
        '{"library_name": "Music", "artist_name": "Artist", "album_name": "Album"}'
    )

    with patch(
        "openpeerpower.components.sonos.media_player.play_on_sonos"
    ) as mock_play:
        # Test successful Plex service call
        assert await opp.services.async_call(
            MP_DOMAIN,
            SERVICE_PLAY_MEDIA,
            {
                ATTR_ENTITY_ID: media_player,
                ATTR_MEDIA_CONTENT_TYPE: MEDIA_TYPE_MUSIC,
                ATTR_MEDIA_CONTENT_ID: f"{PLEX_URI_SCHEME}{media_content_id}",
            },
            blocking=True,
        )

        assert len(mock_play.mock_calls) == 1
        assert mock_play.mock_calls[0][1][1] == MEDIA_TYPE_MUSIC
        assert mock_play.mock_calls[0][1][2] == media_content_id
        assert mock_play.mock_calls[0][1][3] == "Zone A"

        # Test failed Plex service call
        mock_play.reset_mock()
        mock_play.side_effect = OpenPeerPowerError

        with pytest.raises(OpenPeerPowerError):
            await opp.services.async_call(
                MP_DOMAIN,
                SERVICE_PLAY_MEDIA,
                {
                    ATTR_ENTITY_ID: media_player,
                    ATTR_MEDIA_CONTENT_TYPE: MEDIA_TYPE_MUSIC,
                    ATTR_MEDIA_CONTENT_ID: f"{PLEX_URI_SCHEME}{media_content_id}",
                },
                blocking=True,
            )
        assert mock_play.called
