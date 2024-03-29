"""Support for command line notification services."""
import logging
import subprocess

import voluptuous as vol

from openpeerpower.components.notify import PLATFORM_SCHEMA, BaseNotificationService
from openpeerpower.const import CONF_COMMAND, CONF_NAME
import openpeerpower.helpers.config_validation as cv
from openpeerpower.util.process import kill_subprocess

from .const import CONF_COMMAND_TIMEOUT, DEFAULT_TIMEOUT

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_COMMAND): cv.string,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_COMMAND_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
    }
)


def get_service(opp, config, discovery_info=None):
    """Get the Command Line notification service."""
    command = config[CONF_COMMAND]
    timeout = config[CONF_COMMAND_TIMEOUT]

    return CommandLineNotificationService(command, timeout)


class CommandLineNotificationService(BaseNotificationService):
    """Implement the notification service for the Command Line service."""

    def __init__(self, command, timeout):
        """Initialize the service."""
        self.command = command
        self._timeout = timeout

    def send_message(self, message="", **kwargs):
        """Send a message to a command line."""
        with subprocess.Popen(
            self.command,
            universal_newlines=True,
            stdin=subprocess.PIPE,
            shell=True,  # nosec # shell by design
        ) as proc:
            try:
                proc.communicate(input=message, timeout=self._timeout)
                if proc.returncode != 0:
                    _LOGGER.error("Command failed: %s", self.command)
            except subprocess.TimeoutExpired:
                _LOGGER.error("Timeout for command: %s", self.command)
                kill_subprocess(proc)
            except subprocess.SubprocessError:
                _LOGGER.error("Error trying to exec command: %s", self.command)
