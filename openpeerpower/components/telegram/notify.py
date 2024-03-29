"""Telegram platform for notify component."""
import logging

import voluptuous as vol

from openpeerpower.components.notify import (
    ATTR_DATA,
    ATTR_MESSAGE,
    ATTR_TARGET,
    ATTR_TITLE,
    PLATFORM_SCHEMA,
    BaseNotificationService,
)
from openpeerpower.const import ATTR_LOCATION
from openpeerpower.helpers.reload import setup_reload_service

from . import DOMAIN as TELEGRAM_DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

DOMAIN = "telegram_bot"
ATTR_KEYBOARD = "keyboard"
ATTR_INLINE_KEYBOARD = "inline_keyboard"
ATTR_PHOTO = "photo"
ATTR_VIDEO = "video"
ATTR_VOICE = "voice"
ATTR_DOCUMENT = "document"

CONF_CHAT_ID = "chat_id"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({vol.Required(CONF_CHAT_ID): vol.Coerce(int)})


def get_service(opp, config, discovery_info=None):
    """Get the Telegram notification service."""

    setup_reload_service(opp, TELEGRAM_DOMAIN, PLATFORMS)
    chat_id = config.get(CONF_CHAT_ID)
    return TelegramNotificationService(opp, chat_id)


class TelegramNotificationService(BaseNotificationService):
    """Implement the notification service for Telegram."""

    def __init__(self, opp, chat_id):
        """Initialize the service."""
        self._chat_id = chat_id
        self.opp = opp

    def send_message(self, message="", **kwargs):
        """Send a message to a user."""
        service_data = {ATTR_TARGET: kwargs.get(ATTR_TARGET, self._chat_id)}
        if ATTR_TITLE in kwargs:
            service_data.update({ATTR_TITLE: kwargs.get(ATTR_TITLE)})
        if message:
            service_data.update({ATTR_MESSAGE: message})
        data = kwargs.get(ATTR_DATA)

        # Get keyboard info
        if data is not None and ATTR_KEYBOARD in data:
            keys = data.get(ATTR_KEYBOARD)
            keys = keys if isinstance(keys, list) else [keys]
            service_data.update(keyboard=keys)
        elif data is not None and ATTR_INLINE_KEYBOARD in data:
            keys = data.get(ATTR_INLINE_KEYBOARD)
            keys = keys if isinstance(keys, list) else [keys]
            service_data.update(inline_keyboard=keys)

        # Send a photo, video, document, voice, or location
        if data is not None and ATTR_PHOTO in data:
            photos = data.get(ATTR_PHOTO)
            photos = photos if isinstance(photos, list) else [photos]
            for photo_data in photos:
                service_data.update(photo_data)
                self.opp.services.call(DOMAIN, "send_photo", service_data=service_data)
            return
        if data is not None and ATTR_VIDEO in data:
            videos = data.get(ATTR_VIDEO)
            videos = videos if isinstance(videos, list) else [videos]
            for video_data in videos:
                service_data.update(video_data)
                self.opp.services.call(DOMAIN, "send_video", service_data=service_data)
            return
        if data is not None and ATTR_VOICE in data:
            voices = data.get(ATTR_VOICE)
            voices = voices if isinstance(voices, list) else [voices]
            for voice_data in voices:
                service_data.update(voice_data)
                self.opp.services.call(DOMAIN, "send_voice", service_data=service_data)
            return
        if data is not None and ATTR_LOCATION in data:
            service_data.update(data.get(ATTR_LOCATION))
            return self.opp.services.call(
                DOMAIN, "send_location", service_data=service_data
            )
        if data is not None and ATTR_DOCUMENT in data:
            service_data.update(data.get(ATTR_DOCUMENT))
            return self.opp.services.call(
                DOMAIN, "send_document", service_data=service_data
            )

        # Send message
        _LOGGER.debug(
            "TELEGRAM NOTIFIER calling %s.send_message with %s", DOMAIN, service_data
        )
        return self.opp.services.call(DOMAIN, "send_message", service_data=service_data)
