"""Collection of helper methods.

All containing methods are legacy helpers that should not be used by new
components. Instead call the service directly.
"""
from openpeerpower.components.notify import (
    ATTR_DATA,
    ATTR_MESSAGE,
    ATTR_TITLE,
    DOMAIN,
    SERVICE_NOTIFY,
)
from openpeerpower.loader import bind_opp


@bind_opp
def send_message(opp, message, title=None, data=None):
    """Send a notification message."""
    info = {ATTR_MESSAGE: message}

    if title is not None:
        info[ATTR_TITLE] = title

    if data is not None:
        info[ATTR_DATA] = data

    opp.services.call(DOMAIN, SERVICE_NOTIFY, info)
