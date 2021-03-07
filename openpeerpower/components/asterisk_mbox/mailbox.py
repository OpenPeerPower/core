"""Support for the Asterisk Voicemail interface."""
from functools import partial
import logging

from asterisk_mbox import ServerError

from openpeerpower.components.mailbox import CONTENT_TYPE_MPEG, Mailbox, StreamError
from openpeerpower.core import callback
from openpeerpower.helpers.dispatcher import async_dispatcher_connect

from . import DOMAIN as ASTERISK_DOMAIN

_LOGGER = logging.getLogger(__name__)

SIGNAL_MESSAGE_REQUEST = "asterisk_mbox.message_request"
SIGNAL_MESSAGE_UPDATE = "asterisk_mbox.message_updated"


async def async_get_handler(opp, config, discovery_info=None):
    """Set up the Asterix VM platform."""
    return AsteriskMailbox(opp, ASTERISK_DOMAIN)


class AsteriskMailbox(Mailbox):
    """Asterisk VM Sensor."""

    def __init__(self, opp, name):
        """Initialize Asterisk mailbox."""
        super().__init__(opp, name)
        async_dispatcher_connect(self.opp, SIGNAL_MESSAGE_UPDATE, self._update_callback)

    @callback
    def _update_callback(self, msg):
        """Update the message count in HA, if needed."""
        self.async_update()

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

        client = self.opp.data[ASTERISK_DOMAIN].client
        try:
            return await self.opp.async_add_executor_job(
                partial(client.mp3, msgid, sync=True)
            )
        except ServerError as err:
            raise StreamError(err) from err

    async def async_get_messages(self):
        """Return a list of the current messages."""
        return self.opp.data[ASTERISK_DOMAIN].messages

    async def async_delete(self, msgid):
        """Delete the specified messages."""
        client = self.opp.data[ASTERISK_DOMAIN].client
        _LOGGER.info("Deleting: %s", msgid)
        await self.opp.async_add_executor_job(client.delete, msgid)
        return True
