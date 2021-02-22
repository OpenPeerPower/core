"""Support for sending data to Logentries webhook endpoint."""
import json
import logging

import requests
import voluptuous as vol

from openpeerpower.const import CONF_TOKEN, EVENT_STATE_CHANGED
from openpeerpower.helpers import state as state_helper
import openpeerpower.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "logentries"

DEFAULT_HOST = "https://webhook.logentries.com/noformat/logs/"

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_TOKEN): cv.string})}, extra=vol.ALLOW_EXTRA
)


def setup(opp, config):
    """Set up the Logentries component."""
    conf = config[DOMAIN]
    token = conf.get(CONF_TOKEN)
    le_wh = f"{DEFAULT_HOST}{token}"

    def logentries_event_listener(event):
        """Listen for new messages on the bus and sends them to Logentries."""
        state = event.data.get("new_state")
        if state is None:
            return
        try:
            _state = state_helper.state_as_number(state)
        except ValueError:
            _state = state.state
        json_body = [
            {
                "domain": state.domain,
                "entity_id": state.object_id,
                "attributes": dict(state.attributes),
                "time": str(event.time_fired),
                "value": _state,
            }
        ]
        try:
            payload = {"host": le_wh, "event": json_body}
            requests.post(le_wh, data=json.dumps(payload), timeout=10)
        except requests.exceptions.RequestException as error:
            _LOGGER.exception("Error sending to Logentries: %s", error)

    opp.bus.listen(EVENT_STATE_CHANGED, logentries_event_listener)

    return True
