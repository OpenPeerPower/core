"""The tests for the TTS component."""
from unittest.mock import patch

import pytest
import yarl

import openpeerpower.components.media_player as media_player
from openpeerpower.components.media_player.const import (
    DOMAIN as DOMAIN_MP,
    SERVICE_PLAY_MEDIA,
)
import openpeerpower.components.notify as notify
import openpeerpower.components.tts as tts
from openpeerpower.config import async_process_op_core_config
from openpeerpower.setup import async_setup_component

from tests.common import assert_setup_component, async_mock_service


def relative_url(url):
    """Convert an absolute url to a relative one."""
    return str(yarl.URL(url).relative())


@pytest.fixture(autouse=True)
def mutagen_mock():
    """Mock writing tags."""
    with patch(
        "openpeerpower.components.tts.SpeechManager.write_tags",
        side_effect=lambda *args: args[1],
    ):
        yield


@pytest.fixture(autouse=True)
async def internal_url_mock.opp):
    """Mock internal URL of the instance."""
    await async_process_op_core_config(
        opp,
        {"internal_url": "http://example.local:8123"},
    )


async def test_setup_platform.opp):
    """Set up the tts platform ."""
    config = {
        notify.DOMAIN: {
            "platform": "tts",
            "name": "tts_test",
            "tts_service": "tts.demo_say",
            "media_player": "media_player.demo",
        }
    }
    with assert_setup_component(1, notify.DOMAIN):
        assert await async_setup_component(opp, notify.DOMAIN, config)

    assert opp.services.has_service(notify.DOMAIN, "tts_test")


async def test_setup_component_and_test_service.opp):
    """Set up the demo platform and call service."""
    calls = async_mock_service(opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

    config = {
        tts.DOMAIN: {"platform": "demo"},
        media_player.DOMAIN: {"platform": "demo"},
        notify.DOMAIN: {
            "platform": "tts",
            "name": "tts_test",
            "tts_service": "tts.demo_say",
            "media_player": "media_player.demo",
            "language": "en",
        },
    }

    with assert_setup_component(1, tts.DOMAIN):
        assert await async_setup_component(opp, tts.DOMAIN, config)

    with assert_setup_component(1, notify.DOMAIN):
        assert await async_setup_component(opp, notify.DOMAIN, config)

    await opp.services.async_call(
        notify.DOMAIN,
        "tts_test",
        {
            tts.ATTR_MESSAGE: "There is someone at the door.",
        },
        blocking=True,
    )

    await opp.async_block_till_done()

    assert len(calls) == 1
