"""Tests for the lastfm sensor."""
from unittest.mock import patch

from pylast import Track
import pytest

from openpeerpower.components import sensor
from openpeerpower.components.lastfm.sensor import STATE_NOT_SCROBBLING
from openpeerpower.setup import async_setup_component


class MockUser:
    """Mock user object for pylast."""

    def __init__(self, now_playing_result):
        """Initialize the mock."""
        self._now_playing_result = now_playing_result

    def get_playcount(self):
        """Get mock play count."""
        return 1

    def get_image(self):
        """Get mock image."""
        pass

    def get_recent_tracks(self, limit):
        """Get mock recent tracks."""
        return []

    def get_top_tracks(self, limit):
        """Get mock top tracks."""
        return []

    def get_now_playing(self):
        """Get mock now playing."""
        return self._now_playing_result


@pytest.fixture(name="lastfm_network")
def lastfm_network_fixture():
    """Create fixture for LastFMNetwork."""
    with patch("pylast.LastFMNetwork") as lastfm_network:
        yield lastfm_network


async def test_update_not_playing.opp, lastfm_network):
    """Test update when no playing song."""

    lastfm_network.return_value.get_user.return_value = MockUser(None)

    assert await async_setup_component(
       .opp,
        sensor.DOMAIN,
        {"sensor": {"platform": "lastfm", "api_key": "secret-key", "users": ["test"]}},
    )
    await opp.async_block_till_done()

    entity_id = "sensor.test"

    state = opp.states.get(entity_id)

    assert state.state == STATE_NOT_SCROBBLING


async def test_update_playing.opp, lastfm_network):
    """Test update when song playing."""

    lastfm_network.return_value.get_user.return_value = MockUser(
        Track("artist", "title", None)
    )

    assert await async_setup_component(
       .opp,
        sensor.DOMAIN,
        {"sensor": {"platform": "lastfm", "api_key": "secret-key", "users": ["test"]}},
    )
    await opp.async_block_till_done()

    entity_id = "sensor.test"

    state = opp.states.get(entity_id)

    assert state.state == "artist - title"
