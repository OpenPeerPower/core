"""Support for the cloud for text to speech service."""

from opp_net import Cloud
from opp_net.voice import MAP_VOICE, VoiceError
import voluptuous as vol

from openpeerpower.components.tts import CONF_LANG, PLATFORM_SCHEMA, Provider

from .const import DOMAIN

CONF_GENDER = "gender"

SUPPORT_LANGUAGES = list({key[0] for key in MAP_VOICE})


def validate_lang(value):
    """Validate chosen gender or language."""
    lang = value.get(CONF_LANG)

    if lang is None:
        return value

    gender = value.get(CONF_GENDER)

    if gender is None:
        gender = value[CONF_GENDER] = next(
            (chk_gender for chk_lang, chk_gender in MAP_VOICE if chk_lang == lang), None
        )

    if (lang, gender) not in MAP_VOICE:
        raise vol.Invalid("Unsupported language and gender specified.")

    return value


PLATFORM_SCHEMA = vol.All(
    PLATFORM_SCHEMA.extend(
        {
            vol.Optional(CONF_LANG): str,
            vol.Optional(CONF_GENDER): str,
        }
    ),
    validate_lang,
)


async def async_get_engine(opp, config, discovery_info=None):
    """Set up Cloud speech component."""
    cloud: Cloud = opp.data[DOMAIN]

    if discovery_info is not None:
        language = None
        gender = None
    else:
        language = config[CONF_LANG]
        gender = config[CONF_GENDER]

    return CloudProvider(cloud, language, gender)


class CloudProvider(Provider):
    """NabuCasa Cloud speech API provider."""

    def __init__(self, cloud: Cloud, language: str, gender: str):
        """Initialize cloud provider."""
        self.cloud = cloud
        self.name = "Cloud"
        self._language = language
        self._gender = gender

        if self._language is not None:
            return

        self._language, self._gender = cloud.client.prefs.tts_default_voice
        cloud.client.prefs.async_listen_updates(self._sync_prefs)

    async def _sync_prefs(self, prefs):
        """Sync preferences."""
        self._language, self._gender = prefs.tts_default_voice

    @property
    def default_language(self):
        """Return the default language."""
        return self._language

    @property
    def supported_languages(self):
        """Return list of supported languages."""
        return SUPPORT_LANGUAGES

    @property
    def supported_options(self):
        """Return list of supported options like voice, emotion."""
        return [CONF_GENDER]

    @property
    def default_options(self):
        """Return a dict include default options."""
        return {CONF_GENDER: self._gender}

    async def async_get_tts_audio(self, message, language, options=None):
        """Load TTS from NabuCasa Cloud."""
        # Process TTS
        try:
            data = await self.cloud.voice.process_tts(
                message, language, gender=options[CONF_GENDER]
            )
        except VoiceError:
            return (None, None)

        return ("mp3", data)
