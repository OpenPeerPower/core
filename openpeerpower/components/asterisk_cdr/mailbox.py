"""Support for the Asterisk CDR interface."""
import datetime
import hashlib

from openpeerpower.components.asterisk_mbox import (
    DOMAIN as ASTERISK_DOMAIN,
    SIGNAL_CDR_UPDATE,
)
from openpeerpower.components.mailbox import Mailbox
from openpeerpower.core import callback
from openpeerpower.helpers.dispatcher import async_dispatcher_connect

MAILBOX_NAME = "asterisk_cdr"


async def async_get_handler(opp, config, discovery_info=None):
    """Set up the Asterix CDR platform."""
    return AsteriskCDR(opp, MAILBOX_NAME)


class AsteriskCDR(Mailbox):
    """Asterisk VM Call Data Record mailbox."""

    def __init__(self, opp, name):
        """Initialize Asterisk CDR."""
        super().__init__(opp, name)
        self.cdr = []
        async_dispatcher_connect(self.opp, SIGNAL_CDR_UPDATE, self._update_callback)

    @callback
    def _update_callback(self, msg):
        """Update the message count in HA, if needed."""
        self._build_message()
        self.async_update()

    def _build_message(self):
        """Build message structure."""
        cdr = []
        for entry in self.opp.data[ASTERISK_DOMAIN].cdr:
            timestamp = datetime.datetime.strptime(
                entry["time"], "%Y-%m-%d %H:%M:%S"
            ).timestamp()
            info = {
                "origtime": timestamp,
                "callerid": entry["callerid"],
                "duration": entry["duration"],
            }
            sha = hashlib.sha256(str(entry).encode("utf-8")).hexdigest()
            msg = (
                f"Destination: {entry['dest']}\n"
                f"Application: {entry['application']}\n "
                f"Context: {entry['context']}"
            )
            cdr.append({"info": info, "sha": sha, "text": msg})
        self.cdr = cdr

    async def async_get_messages(self):
        """Return a list of the current messages."""
        if not self.cdr:
            self._build_message()
        return self.cdr
