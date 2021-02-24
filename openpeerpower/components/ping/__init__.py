"""The ping component."""

from openpeerpower.core import callback

DOMAIN = "ping"
PLATFORMS = ["binary_sensor"]

PING_ID = "ping_id"
DEFAULT_START_ID = 129
MAX_PING_ID = 65534


@callback
def async_get_next_ping_id(opp):
    """Find the next id to use in the outbound ping.

    Must be called in async
    """
    current_id = opp.data.setdefault(DOMAIN, {}).get(PING_ID, DEFAULT_START_ID)

    if current_id == MAX_PING_ID:
        next_id = DEFAULT_START_ID
    else:
        next_id = current_id + 1

    opp.data[DOMAIN][PING_ID] = next_id

    return next_id
