"""Support for tag triggers."""
import voluptuous as vol

from openpeerpower.const import CONF_PLATFORM
from openpeerpower.core import OppJob
from openpeerpower.helpers import config_validation as cv

from .const import DEVICE_ID, DOMAIN, EVENT_TAG_SCANNED, TAG_ID

TRIGGER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PLATFORM): DOMAIN,
        vol.Required(TAG_ID): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(DEVICE_ID): vol.All(cv.ensure_list, [cv.string]),
    }
)


async def async_attach_trigger(opp, config, action, automation_info):
    """Listen for tag_scanned events based on configuration."""
    tag_ids = set(config[TAG_ID])
    device_ids = set(config[DEVICE_ID]) if DEVICE_ID in config else None

    job = OppJob(action)

    async def handle_event(event):
        """Listen for tag scan events and calls the action when data matches."""
        if event.data.get(TAG_ID) not in tag_ids or (
            device_ids is not None and event.data.get(DEVICE_ID) not in device_ids
        ):
            return

        task = opp.async_run_opp_job(
            job,
            {
                "trigger": {
                    "platform": DOMAIN,
                    "event": event,
                    "description": "Tag scanned",
                }
            },
            event.context,
        )

        if task:
            await task

    return opp.bus.async_listen(EVENT_TAG_SCANNED, handle_event)
