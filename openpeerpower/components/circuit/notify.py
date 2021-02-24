"""Unify Circuit platform for notify component."""
import logging

from circuit_webhook import Circuit

from openpeerpower.components.notify import BaseNotificationService
from openpeerpower.const import CONF_URL

_LOGGER = logging.getLogger(__name__)


def get_service(opp, config, discovery_info=None):
    """Get the Unify Circuit notification service."""
    if discovery_info is None:
        return None

    return CircuitNotificationService(discovery_info)


class CircuitNotificationService(BaseNotificationService):
    """Implement the notification service for Unify Circuit."""

    def __init__(self, config):
        """Initialize the service."""
        self.webhook_url = config[CONF_URL]

    def send_message(self, message=None, **kwargs):
        """Send a message to the webhook."""

        webhook_url = self.webhook_url

        if webhook_url and message:
            try:
                circuit_message = Circuit(url=webhook_url)
                circuit_message.post(text=message)
            except RuntimeError as err:
                _LOGGER.error("Could not send notification. Error: %s", err)
