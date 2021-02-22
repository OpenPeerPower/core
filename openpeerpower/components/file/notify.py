"""Support for file notification."""
import os

import voluptuous as vol

from openpeerpower.components.notify import (
    ATTR_TITLE,
    ATTR_TITLE_DEFAULT,
    PLATFORM_SCHEMA,
    BaseNotificationService,
)
from openpeerpower.const import CONF_FILENAME
import openpeerpower.helpers.config_validation as cv
import openpeerpower.util.dt as dt_util

CONF_TIMESTAMP = "timestamp"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_FILENAME): cv.string,
        vol.Optional(CONF_TIMESTAMP, default=False): cv.boolean,
    }
)


def get_service.opp, config, discovery_info=None):
    """Get the file notification service."""
    filename = config[CONF_FILENAME]
    timestamp = config[CONF_TIMESTAMP]

    return FileNotificationService.opp, filename, timestamp)


class FileNotificationService(BaseNotificationService):
    """Implement the notification service for the File service."""

    def __init__(self, opp, filename, add_timestamp):
        """Initialize the service."""
        self.filepath = os.path.join.opp.config.config_dir, filename)
        self.add_timestamp = add_timestamp

    def send_message(self, message="", **kwargs):
        """Send a message to a file."""
        with open(self.filepath, "a") as file:
            if os.stat(self.filepath).st_size == 0:
                title = f"{kwargs.get(ATTR_TITLE, ATTR_TITLE_DEFAULT)} notifications (Log started: {dt_util.utcnow().isoformat()})\n{'-' * 80}\n"
                file.write(title)

            if self.add_timestamp:
                text = f"{dt_util.utcnow().isoformat()} {message}\n"
            else:
                text = f"{message}\n"
            file.write(text)
