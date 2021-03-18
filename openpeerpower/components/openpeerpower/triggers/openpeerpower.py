"""Offer Open Peer Power core automation rules."""
import voluptuous as vol

from openpeerpower.const import CONF_EVENT, CONF_PLATFORM, EVENT_OPENPEERPOWER_STOP
from openpeerpower.core import OppJob, callback

# mypy: allow-untyped-defs

EVENT_START = "start"
EVENT_SHUTDOWN = "shutdown"

TRIGGER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PLATFORM): "openpeerpower",
        vol.Required(CONF_EVENT): vol.Any(EVENT_START, EVENT_SHUTDOWN),
    }
)


async def async_attach_trigger(opp, config, action, automation_info):
    """Listen for events based on configuration."""
    event = config.get(CONF_EVENT)
    job = OppJob(action)

    if event == EVENT_SHUTDOWN:

        @callback
        def opp_shutdown(event):
            """Execute when Open Peer Power is shutting down."""
            opp.async_run_opp_job(
                job,
                {
                    "trigger": {
                        "platform": "openpeerpower",
                        "event": event,
                        "description": "Open Peer Power stopping",
                    }
                },
                event.context,
            )

        return opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, opp_shutdown)

    # Automation are enabled while opp is starting up, fire right away
    # Check state because a config reload shouldn't trigger it.
    if automation_info["open_peer_power_start"]:
        opp.async_run_opp_job(
            job,
            {
                "trigger": {
                    "platform": "openpeerpower",
                    "event": event,
                    "description": "Open Peer Power starting",
                }
            },
        )

    return lambda: None
