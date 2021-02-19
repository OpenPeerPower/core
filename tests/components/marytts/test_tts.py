"""The tests for the MaryTTS speech platform."""
import asyncio
import os
import shutil
from unittest.mock import patch

from openpeerpower.components.media_player.const import (
    ATTR_MEDIA_CONTENT_ID,
    DOMAIN as DOMAIN_MP,
    SERVICE_PLAY_MEDIA,
)
import openpeerpower.components.tts as tts
from openpeerpower.config import async_process_op.core_config
from openpeerpowerr.setup import setup_component

from tests.common import assert_setup_component, get_test_home_assistant, mock_service


class TestTTSMaryTTSPlatform:
    """Test the speech component."""

    def setup_method(self):
        """Set up things to be run when tests are started."""
        self.opp = get_test_home_assistant()

        asyncio.run_coroutine_threadsafe(
            async_process_op.core_config(
                self.opp, {"internal_url": "http://example.local:8123"}
            ),
            self.opp.loop,
        )

        self.host = "localhost"
        self.port = 59125
        self.params = {
            "INPUT_TEXT": "OpenPeerPower",
            "INPUT_TYPE": "TEXT",
            "OUTPUT_TYPE": "AUDIO",
            "LOCALE": "en_US",
            "AUDIO": "WAVE_FILE",
            "VOICE": "cmu-slt-hsmm",
        }

    def teardown_method(self):
        """Stop everything that was started."""
        default_tts = self.opp.config.path(tts.DEFAULT_CACHE_DIR)
        if os.path.isdir(default_tts):
            shutil.rmtree(default_tts)

        self.opp.stop()

    def test_setup_component(self):
        """Test setup component."""
        config = {tts.DOMAIN: {"platform": "marytts"}}

        with assert_setup_component(1, tts.DOMAIN):
            setup_component(self.opp, tts.DOMAIN, config)

    def test_service_say(self):
        """Test service call say."""
        calls = mock_service(self.opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

        config = {tts.DOMAIN: {"platform": "marytts"}}

        with assert_setup_component(1, tts.DOMAIN):
            setup_component(self.opp, tts.DOMAIN, config)

        with patch(
            "openpeerpower.components.marytts.tts.MaryTTS.speak",
            return_value=b"audio",
        ) as mock_speak:
            self.opp.services.call(
                tts.DOMAIN,
                "marytts_say",
                {
                    "entity_id": "media_player.something",
                    tts.ATTR_MESSAGE: "OpenPeerPower",
                },
            )
            self.opp.block_till_done()

        mock_speak.assert_called_once()
        mock_speak.assert_called_with("OpenPeerPower", {})

        assert len(calls) == 1
        assert calls[0].data[ATTR_MEDIA_CONTENT_ID].find(".wav") != -1

    def test_service_say_with_effect(self):
        """Test service call say with effects."""
        calls = mock_service(self.opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

        config = {
            tts.DOMAIN: {"platform": "marytts", "effect": {"Volume": "amount:2.0;"}}
        }

        with assert_setup_component(1, tts.DOMAIN):
            setup_component(self.opp, tts.DOMAIN, config)

        with patch(
            "openpeerpower.components.marytts.tts.MaryTTS.speak",
            return_value=b"audio",
        ) as mock_speak:
            self.opp.services.call(
                tts.DOMAIN,
                "marytts_say",
                {
                    "entity_id": "media_player.something",
                    tts.ATTR_MESSAGE: "OpenPeerPower",
                },
            )
            self.opp.block_till_done()

        mock_speak.assert_called_once()
        mock_speak.assert_called_with("OpenPeerPower", {"Volume": "amount:2.0;"})

        assert len(calls) == 1
        assert calls[0].data[ATTR_MEDIA_CONTENT_ID].find(".wav") != -1

    def test_service_say_http_error(self):
        """Test service call say."""
        calls = mock_service(self.opp, DOMAIN_MP, SERVICE_PLAY_MEDIA)

        config = {tts.DOMAIN: {"platform": "marytts"}}

        with assert_setup_component(1, tts.DOMAIN):
            setup_component(self.opp, tts.DOMAIN, config)

        with patch(
            "openpeerpower.components.marytts.tts.MaryTTS.speak",
            side_effect=Exception(),
        ) as mock_speak:
            self.opp.services.call(
                tts.DOMAIN,
                "marytts_say",
                {
                    "entity_id": "media_player.something",
                    tts.ATTR_MESSAGE: "OpenPeerPower",
                },
            )
            self.opp.block_till_done()

        mock_speak.assert_called_once()
        assert len(calls) == 0
