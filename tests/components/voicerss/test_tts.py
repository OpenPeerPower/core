"""The tests for the VoiceRSS speech platform."""
import asyncio
import os
import shutil

from openpeerpower.components.media_player.const import (
    ATTR_MEDIA_CONTENT_ID,
    DOMAIN as DOMAIN_MP,
    SERVICE_PLAY_MEDIA,
)
import openpeerpower.components.tts as tts
from openpeerpower.config import async_process_op_core_config
from openpeerpower.setup import setup_component

from tests.common import assert_setup_component, get_test_open_peer_power, mock_service
from tests.components.tts.test_init import mutagen_mock  # noqa: F401


class TestTTSVoiceRSSPlatform:
    """Test the voicerss speech component."""

    def setup_method(self):
        """Set up things to be run when tests are started."""
        self.opp = get_test_open_peer_power()

        asyncio.run_coroutine_threadsafe(
            async_process_op_core_config(
                self.opp, {"internal_url": "http://example.local:8123"}
            ),
            self.opp.loop,
        )

        self.url = "https://api.voicerss.org/"
        self.form_data = {
            "key": "1234567xx",
            "hl": "en-us",
            "c": "MP3",
            "f": "8khz_8bit_mono",
            "src": "I person is on front of your door.",
        }

    def teardown_method(self):
        """Stop everything that was started."""
        default_tts = self.opp.config.path(tts.DEFAULT_CACHE_DIR)
        if os.path.isdir(default_tts):
            shutil.rmtree(default_tts)

        self.opp.stop()

    def test_setup_component(self):
        """Test setup component."""
        config = {tts.DOMAIN: {"platform": "voicerss", "api_key": "1234567xx"}}

        with assert_setup_component(1, tts.DOMAIN):
            setup_component(self.opp, tts.DOMAIN, config)

    def test_setup_component_without_api_key(self):
        """Test setup component without api key."""
        config = {tts.DOMAIN: {"platform": "voicerss"}}

        with assert_setup_component(0, tts.DOMAIN):
            setup_component(self.opp, tts.DOMAIN, config)

    def test_service_say(self, aioclient_mock):
        """Test service call say."""
        calls = mock_service(self.opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

        aioclient_mock.post(self.url, data=self.form_data, status=200, content=b"test")

        config = {tts.DOMAIN: {"platform": "voicerss", "api_key": "1234567xx"}}

        with assert_setup_component(1, tts.DOMAIN):
            setup_component(self.opp, tts.DOMAIN, config)

        self.opp.services.call(
            tts.DOMAIN,
            "voicerss_say",
            {
                "entity_id": "media_player.something",
                tts.ATTR_MESSAGE: "I person is on front of your door.",
            },
        )
        self.opp.block_till_done()

        assert len(calls) == 1
        assert len(aioclient_mock.mock_calls) == 1
        assert aioclient_mock.mock_calls[0][2] == self.form_data
        assert calls[0].data[ATTR_MEDIA_CONTENT_ID].find(".mp3") != -1

    def test_service_say_german_config(self, aioclient_mock):
        """Test service call say with german code in the config."""
        calls = mock_service(self.opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

        self.form_data["hl"] = "de-de"
        aioclient_mock.post(self.url, data=self.form_data, status=200, content=b"test")

        config = {
            tts.DOMAIN: {
                "platform": "voicerss",
                "api_key": "1234567xx",
                "language": "de-de",
            }
        }

        with assert_setup_component(1, tts.DOMAIN):
            setup_component(self.opp, tts.DOMAIN, config)

        self.opp.services.call(
            tts.DOMAIN,
            "voicerss_say",
            {
                "entity_id": "media_player.something",
                tts.ATTR_MESSAGE: "I person is on front of your door.",
            },
        )
        self.opp.block_till_done()

        assert len(calls) == 1
        assert len(aioclient_mock.mock_calls) == 1
        assert aioclient_mock.mock_calls[0][2] == self.form_data

    def test_service_say_german_service(self, aioclient_mock):
        """Test service call say with german code in the service."""
        calls = mock_service(self.opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

        self.form_data["hl"] = "de-de"
        aioclient_mock.post(self.url, data=self.form_data, status=200, content=b"test")

        config = {tts.DOMAIN: {"platform": "voicerss", "api_key": "1234567xx"}}

        with assert_setup_component(1, tts.DOMAIN):
            setup_component(self.opp, tts.DOMAIN, config)

        self.opp.services.call(
            tts.DOMAIN,
            "voicerss_say",
            {
                "entity_id": "media_player.something",
                tts.ATTR_MESSAGE: "I person is on front of your door.",
                tts.ATTR_LANGUAGE: "de-de",
            },
        )
        self.opp.block_till_done()

        assert len(calls) == 1
        assert len(aioclient_mock.mock_calls) == 1
        assert aioclient_mock.mock_calls[0][2] == self.form_data

    def test_service_say_error(self, aioclient_mock):
        """Test service call say with http response 400."""
        calls = mock_service(self.opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

        aioclient_mock.post(self.url, data=self.form_data, status=400, content=b"test")

        config = {tts.DOMAIN: {"platform": "voicerss", "api_key": "1234567xx"}}

        with assert_setup_component(1, tts.DOMAIN):
            setup_component(self.opp, tts.DOMAIN, config)

        self.opp.services.call(
            tts.DOMAIN,
            "voicerss_say",
            {
                "entity_id": "media_player.something",
                tts.ATTR_MESSAGE: "I person is on front of your door.",
            },
        )
        self.opp.block_till_done()

        assert len(calls) == 0
        assert len(aioclient_mock.mock_calls) == 1
        assert aioclient_mock.mock_calls[0][2] == self.form_data

    def test_service_say_timeout(self, aioclient_mock):
        """Test service call say with http timeout."""
        calls = mock_service(self.opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

        aioclient_mock.post(self.url, data=self.form_data, exc=asyncio.TimeoutError())

        config = {tts.DOMAIN: {"platform": "voicerss", "api_key": "1234567xx"}}

        with assert_setup_component(1, tts.DOMAIN):
            setup_component(self.opp, tts.DOMAIN, config)

        self.opp.services.call(
            tts.DOMAIN,
            "voicerss_say",
            {
                "entity_id": "media_player.something",
                tts.ATTR_MESSAGE: "I person is on front of your door.",
            },
        )
        self.opp.block_till_done()

        assert len(calls) == 0
        assert len(aioclient_mock.mock_calls) == 1
        assert aioclient_mock.mock_calls[0][2] == self.form_data

    def test_service_say_error_msg(self, aioclient_mock):
        """Test service call say with http error api message."""
        calls = mock_service(self.opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

        aioclient_mock.post(
            self.url,
            data=self.form_data,
            status=200,
            content=b"The subscription does not support SSML!",
        )

        config = {tts.DOMAIN: {"platform": "voicerss", "api_key": "1234567xx"}}

        with assert_setup_component(1, tts.DOMAIN):
            setup_component(self.opp, tts.DOMAIN, config)

        self.opp.services.call(
            tts.DOMAIN,
            "voicerss_say",
            {
                "entity_id": "media_player.something",
                tts.ATTR_MESSAGE: "I person is on front of your door.",
            },
        )
        self.opp.block_till_done()

        assert len(calls) == 0
        assert len(aioclient_mock.mock_calls) == 1
        assert aioclient_mock.mock_calls[0][2] == self.form_data
