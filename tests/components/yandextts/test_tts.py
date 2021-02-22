"""The tests for the Yandex SpeechKit speech platform."""
import asyncio
import os
import shutil

from openpeerpower.components.media_player.const import (
    DOMAIN as DOMAIN_MP,
    SERVICE_PLAY_MEDIA,
)
import openpeerpower.components.tts as tts
from openpeerpower.config import async_process_op_core_config
from openpeerpower.const import HTTP_FORBIDDEN
from openpeerpower.setup import setup_component

from tests.common import assert_setup_component, get_test_open_peer_power, mock_service
from tests.components.tts.test_init import (  # noqa: F401, pylint: disable=unused-import
    mutagen_mock,
)


class TestTTSYandexPlatform:
    """Test the speech component."""

    def setup_method(self):
        """Set up things to be run when tests are started."""
        self opp =get_test_open_peer_power()
        self._base_url = "https://tts.voicetech.yandex.net/generate?"

        asyncio.run_coroutine_threadsafe(
            async_process_op_core_config(
                self.opp, {"internal_url": "http://example.local:8123"}
            ),
            self.opp.loop,
        )

    def teardown_method(self):
        """Stop everything that was started."""
        default_tts = self.opp.config.path(tts.DEFAULT_CACHE_DIR)
        if os.path.isdir(default_tts):
            shutil.rmtree(default_tts)

        self.opp.stop()

    def test_setup_component(self):
        """Test setup component."""
        config = {tts.DOMAIN: {"platform": "yandextts", "api_key": "1234567xx"}}

        with assert_setup_component(1, tts.DOMAIN):
            setup_component(self.opp, tts.DOMAIN, config)

    def test_setup_component_without_api_key(self):
        """Test setup component without api key."""
        config = {tts.DOMAIN: {"platform": "yandextts"}}

        with assert_setup_component(0, tts.DOMAIN):
            setup_component(self.opp, tts.DOMAIN, config)

    def test_service_say(self, aioclient_mock):
        """Test service call say."""
        calls = mock_service(self.opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

        url_param = {
            "text": "OpenPeerPower",
            "lang": "en-US",
            "key": "1234567xx",
            "speaker": "zahar",
            "format": "mp3",
            "emotion": "neutral",
            "speed": 1,
        }
        aioclient_mock.get(
            self._base_url, status=200, content=b"test", params=url_param
        )

        config = {tts.DOMAIN: {"platform": "yandextts", "api_key": "1234567xx"}}

        with assert_setup_component(1, tts.DOMAIN):
            setup_component(self.opp, tts.DOMAIN, config)

        self.opp.services.call(
            tts.DOMAIN,
            "yandextts_say",
            {"entity_id": "media_player.something", tts.ATTR_MESSAGE: "OpenPeerPower"},
        )
        self.opp.block_till_done()

        assert len(aioclient_mock.mock_calls) == 1
        assert len(calls) == 1

    def test_service_say_russian_config(self, aioclient_mock):
        """Test service call say."""
        calls = mock_service(self.opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

        url_param = {
            "text": "OpenPeerPower",
            "lang": "ru-RU",
            "key": "1234567xx",
            "speaker": "zahar",
            "format": "mp3",
            "emotion": "neutral",
            "speed": 1,
        }
        aioclient_mock.get(
            self._base_url, status=200, content=b"test", params=url_param
        )

        config = {
            tts.DOMAIN: {
                "platform": "yandextts",
                "api_key": "1234567xx",
                "language": "ru-RU",
            }
        }

        with assert_setup_component(1, tts.DOMAIN):
            setup_component(self.opp, tts.DOMAIN, config)

        self.opp.services.call(
            tts.DOMAIN,
            "yandextts_say",
            {"entity_id": "media_player.something", tts.ATTR_MESSAGE: "OpenPeerPower"},
        )
        self.opp.block_till_done()

        assert len(aioclient_mock.mock_calls) == 1
        assert len(calls) == 1

    def test_service_say_russian_service(self, aioclient_mock):
        """Test service call say."""
        calls = mock_service(self.opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

        url_param = {
            "text": "OpenPeerPower",
            "lang": "ru-RU",
            "key": "1234567xx",
            "speaker": "zahar",
            "format": "mp3",
            "emotion": "neutral",
            "speed": 1,
        }
        aioclient_mock.get(
            self._base_url, status=200, content=b"test", params=url_param
        )

        config = {tts.DOMAIN: {"platform": "yandextts", "api_key": "1234567xx"}}

        with assert_setup_component(1, tts.DOMAIN):
            setup_component(self.opp, tts.DOMAIN, config)

        self.opp.services.call(
            tts.DOMAIN,
            "yandextts_say",
            {
                "entity_id": "media_player.something",
                tts.ATTR_MESSAGE: "OpenPeerPower",
                tts.ATTR_LANGUAGE: "ru-RU",
            },
        )
        self.opp.block_till_done()

        assert len(aioclient_mock.mock_calls) == 1
        assert len(calls) == 1

    def test_service_say_timeout(self, aioclient_mock):
        """Test service call say."""
        calls = mock_service(self.opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

        url_param = {
            "text": "OpenPeerPower",
            "lang": "en-US",
            "key": "1234567xx",
            "speaker": "zahar",
            "format": "mp3",
            "emotion": "neutral",
            "speed": 1,
        }
        aioclient_mock.get(
            self._base_url, status=200, exc=asyncio.TimeoutError(), params=url_param
        )

        config = {tts.DOMAIN: {"platform": "yandextts", "api_key": "1234567xx"}}

        with assert_setup_component(1, tts.DOMAIN):
            setup_component(self.opp, tts.DOMAIN, config)

        self.opp.services.call(
            tts.DOMAIN,
            "yandextts_say",
            {"entity_id": "media_player.something", tts.ATTR_MESSAGE: "OpenPeerPower"},
        )
        self.opp.block_till_done()

        assert len(calls) == 0
        assert len(aioclient_mock.mock_calls) == 1

    def test_service_say_http_error(self, aioclient_mock):
        """Test service call say."""
        calls = mock_service(self.opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

        url_param = {
            "text": "OpenPeerPower",
            "lang": "en-US",
            "key": "1234567xx",
            "speaker": "zahar",
            "format": "mp3",
            "emotion": "neutral",
            "speed": 1,
        }
        aioclient_mock.get(
            self._base_url, status=HTTP_FORBIDDEN, content=b"test", params=url_param
        )

        config = {tts.DOMAIN: {"platform": "yandextts", "api_key": "1234567xx"}}

        with assert_setup_component(1, tts.DOMAIN):
            setup_component(self.opp, tts.DOMAIN, config)

        self.opp.services.call(
            tts.DOMAIN,
            "yandextts_say",
            {"entity_id": "media_player.something", tts.ATTR_MESSAGE: "OpenPeerPower"},
        )
        self.opp.block_till_done()

        assert len(calls) == 0

    def test_service_say_specified_speaker(self, aioclient_mock):
        """Test service call say."""
        calls = mock_service(self.opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

        url_param = {
            "text": "OpenPeerPower",
            "lang": "en-US",
            "key": "1234567xx",
            "speaker": "alyss",
            "format": "mp3",
            "emotion": "neutral",
            "speed": 1,
        }
        aioclient_mock.get(
            self._base_url, status=200, content=b"test", params=url_param
        )

        config = {
            tts.DOMAIN: {
                "platform": "yandextts",
                "api_key": "1234567xx",
                "voice": "alyss",
            }
        }

        with assert_setup_component(1, tts.DOMAIN):
            setup_component(self.opp, tts.DOMAIN, config)

        self.opp.services.call(
            tts.DOMAIN,
            "yandextts_say",
            {"entity_id": "media_player.something", tts.ATTR_MESSAGE: "OpenPeerPower"},
        )
        self.opp.block_till_done()

        assert len(aioclient_mock.mock_calls) == 1
        assert len(calls) == 1

    def test_service_say_specified_emotion(self, aioclient_mock):
        """Test service call say."""
        calls = mock_service(self.opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

        url_param = {
            "text": "OpenPeerPower",
            "lang": "en-US",
            "key": "1234567xx",
            "speaker": "zahar",
            "format": "mp3",
            "emotion": "evil",
            "speed": 1,
        }
        aioclient_mock.get(
            self._base_url, status=200, content=b"test", params=url_param
        )

        config = {
            tts.DOMAIN: {
                "platform": "yandextts",
                "api_key": "1234567xx",
                "emotion": "evil",
            }
        }

        with assert_setup_component(1, tts.DOMAIN):
            setup_component(self.opp, tts.DOMAIN, config)

        self.opp.services.call(
            tts.DOMAIN,
            "yandextts_say",
            {"entity_id": "media_player.something", tts.ATTR_MESSAGE: "OpenPeerPower"},
        )
        self.opp.block_till_done()

        assert len(aioclient_mock.mock_calls) == 1
        assert len(calls) == 1

    def test_service_say_specified_low_speed(self, aioclient_mock):
        """Test service call say."""
        calls = mock_service(self.opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

        url_param = {
            "text": "OpenPeerPower",
            "lang": "en-US",
            "key": "1234567xx",
            "speaker": "zahar",
            "format": "mp3",
            "emotion": "neutral",
            "speed": "0.1",
        }
        aioclient_mock.get(
            self._base_url, status=200, content=b"test", params=url_param
        )

        config = {
            tts.DOMAIN: {"platform": "yandextts", "api_key": "1234567xx", "speed": 0.1}
        }

        with assert_setup_component(1, tts.DOMAIN):
            setup_component(self.opp, tts.DOMAIN, config)

        self.opp.services.call(
            tts.DOMAIN,
            "yandextts_say",
            {"entity_id": "media_player.something", tts.ATTR_MESSAGE: "OpenPeerPower"},
        )
        self.opp.block_till_done()

        assert len(aioclient_mock.mock_calls) == 1
        assert len(calls) == 1

    def test_service_say_specified_speed(self, aioclient_mock):
        """Test service call say."""
        calls = mock_service(self.opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

        url_param = {
            "text": "OpenPeerPower",
            "lang": "en-US",
            "key": "1234567xx",
            "speaker": "zahar",
            "format": "mp3",
            "emotion": "neutral",
            "speed": 2,
        }
        aioclient_mock.get(
            self._base_url, status=200, content=b"test", params=url_param
        )

        config = {
            tts.DOMAIN: {"platform": "yandextts", "api_key": "1234567xx", "speed": 2}
        }

        with assert_setup_component(1, tts.DOMAIN):
            setup_component(self.opp, tts.DOMAIN, config)

        self.opp.services.call(
            tts.DOMAIN,
            "yandextts_say",
            {"entity_id": "media_player.something", tts.ATTR_MESSAGE: "OpenPeerPower"},
        )
        self.opp.block_till_done()

        assert len(aioclient_mock.mock_calls) == 1
        assert len(calls) == 1

    def test_service_say_specified_options(self, aioclient_mock):
        """Test service call say with options."""
        calls = mock_service(self.opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

        url_param = {
            "text": "OpenPeerPower",
            "lang": "en-US",
            "key": "1234567xx",
            "speaker": "zahar",
            "format": "mp3",
            "emotion": "evil",
            "speed": 2,
        }
        aioclient_mock.get(
            self._base_url, status=200, content=b"test", params=url_param
        )
        config = {tts.DOMAIN: {"platform": "yandextts", "api_key": "1234567xx"}}

        with assert_setup_component(1, tts.DOMAIN):
            setup_component(self.opp, tts.DOMAIN, config)

        self.opp.services.call(
            tts.DOMAIN,
            "yandextts_say",
            {
                "entity_id": "media_player.something",
                tts.ATTR_MESSAGE: "OpenPeerPower",
                "options": {"emotion": "evil", "speed": 2},
            },
        )
        self.opp.block_till_done()

        assert len(aioclient_mock.mock_calls) == 1
        assert len(calls) == 1
