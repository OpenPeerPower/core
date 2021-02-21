"""Support for a demo mailbox."""
from hashlib import sha1
import logging
import os

from openpeerpower.components.mailbox import CONTENT_TYPE_MPEG, Mailbox, StreamError
from openpeerpower.util import dt

_LOGGER = logging.getLogger(__name__)

MAILBOX_NAME = "DemoMailbox"


async def async_get_handler.opp, config, discovery_info=None):
    """Set up the Demo mailbox."""
    return DemoMailbox.opp, MAILBOX_NAME)


class DemoMailbox(Mailbox):
    """Demo Mailbox."""

    def __init__(self,.opp, name):
        """Initialize Demo mailbox."""
        super().__init__.opp, name)
        self._messages = {}
        txt = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
        for idx in range(0, 10):
            msgtime = int(dt.as_timestamp(dt.utcnow()) - 3600 * 24 * (10 - idx))
            msgtxt = f"Message {idx + 1}. {txt * (1 + idx * (idx % 2))}"
            msgsha = sha1(msgtxt.encode("utf-8")).hexdigest()
            msg = {
                "info": {
                    "origtime": msgtime,
                    "callerid": "John Doe <212-555-1212>",
                    "duration": "10",
                },
                "text": msgtxt,
                "sha": msgsha,
            }
            self._messages[msgsha] = msg

    @property
    def media_type(self):
        """Return the supported media type."""
        return CONTENT_TYPE_MPEG

    @property
    def can_delete(self):
        """Return if messages can be deleted."""
        return True

    @property
    def has_media(self):
        """Return if messages have attached media files."""
        return True

    async def async_get_media(self, msgid):
        """Return the media blob for the msgid."""
        if msgid not in self._messages:
            raise StreamError("Message not found")

        audio_path = os.path.join(os.path.dirname(__file__), "tts.mp3")
        with open(audio_path, "rb") as file:
            return file.read()

    async def async_get_messages(self):
        """Return a list of the current messages."""
        return sorted(
            self._messages.values(),
            key=lambda item: item["info"]["origtime"],
            reverse=True,
        )

    async def async_delete(self, msgid):
        """Delete the specified messages."""
        if msgid in self._messages:
            _LOGGER.info("Deleting: %s", msgid)
            del self._messages[msgid]
        self.async_update()
        return True
