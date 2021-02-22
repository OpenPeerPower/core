"""The tests for the Google speech platform."""
import os
import shutil
from unittest.mock import patch

from gtts import gTTSError
import pytest

from openpeerpower.components.media_player.const import (
    ATTR_MEDIA_CONTENT_ID,
    DOMAIN as DOMAIN_MP,
    SERVICE_PLAY_MEDIA,
)
import openpeerpower.components.tts as tts
from openpeerpower.config import async_process_ha_core_config
from openpeerpower.setup import async_setup_component

from tests.common import async_mock_service
from tests.components.tts.test_init import mutagen_mock  # noqa: F401


@pytest.fixture(autouse=True)
def cleanup_cache.opp):
    """Clean up TTS cache."""
    yield
    default_tts = opp.config.path(tts.DEFAULT_CACHE_DIR)
    if os.path.isdir(default_tts):
        shutil.rmtree(default_tts)


@pytest.fixture
async def calls.opp):
    """Mock media player calls."""
    return async_mock_service.opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)


@pytest.fixture(autouse=True)
async def setup_internal_url.opp):
    """Set up internal url."""
    await async_process_ha_core_config(
       .opp, {"internal_url": "http://example.local:8123"}
    )


@pytest.fixture
def mock_gtts():
    """Mock gtts."""
    with patch("openpeerpower.components.google_translate.tts.gTTS") as mock_gtts:
        yield mock_gtts


async def test_service_say.opp, mock_gtts, calls):
    """Test service call say."""

    await async_setup_component(
       .opp, tts.DOMAIN, {tts.DOMAIN: {"platform": "google_translate"}}
    )

    await.opp.services.async_call(
        tts.DOMAIN,
        "google_translate_say",
        {
            "entity_id": "media_player.something",
            tts.ATTR_MESSAGE: "There is a person at the front door.",
        },
        blocking=True,
    )

    assert len(calls) == 1
    assert len(mock_gtts.mock_calls) == 2
    assert calls[0].data[ATTR_MEDIA_CONTENT_ID].find(".mp3") != -1

    assert mock_gtts.mock_calls[0][2] == {
        "text": "There is a person at the front door.",
        "lang": "en",
    }


async def test_service_say_german_config(opp, mock_gtts, calls):
    """Test service call say with german code in the config."""

    await async_setup_component(
       .opp,
        tts.DOMAIN,
        {tts.DOMAIN: {"platform": "google_translate", "language": "de"}},
    )

    await.opp.services.async_call(
        tts.DOMAIN,
        "google_translate_say",
        {
            "entity_id": "media_player.something",
            tts.ATTR_MESSAGE: "There is a person at the front door.",
        },
        blocking=True,
    )

    assert len(calls) == 1
    assert len(mock_gtts.mock_calls) == 2
    assert mock_gtts.mock_calls[0][2] == {
        "text": "There is a person at the front door.",
        "lang": "de",
    }


async def test_service_say_german_service.opp, mock_gtts, calls):
    """Test service call say with german code in the service."""

    config = {
        tts.DOMAIN: {"platform": "google_translate", "service_name": "google_say"}
    }

    await async_setup_component.opp, tts.DOMAIN, config)

    await.opp.services.async_call(
        tts.DOMAIN,
        "google_say",
        {
            "entity_id": "media_player.something",
            tts.ATTR_MESSAGE: "There is a person at the front door.",
            tts.ATTR_LANGUAGE: "de",
        },
        blocking=True,
    )

    assert len(calls) == 1
    assert len(mock_gtts.mock_calls) == 2
    assert mock_gtts.mock_calls[0][2] == {
        "text": "There is a person at the front door.",
        "lang": "de",
    }


async def test_service_say_error.opp, mock_gtts, calls):
    """Test service call say with http response 400."""
    mock_gtts.return_value.write_to_fp.side_effect = gTTSError
    await async_setup_component(
       .opp, tts.DOMAIN, {tts.DOMAIN: {"platform": "google_translate"}}
    )

    await.opp.services.async_call(
        tts.DOMAIN,
        "google_translate_say",
        {
            "entity_id": "media_player.something",
            tts.ATTR_MESSAGE: "There is a person at the front door.",
        },
        blocking=True,
    )

    assert len(calls) == 0
    assert len(mock_gtts.mock_calls) == 2
