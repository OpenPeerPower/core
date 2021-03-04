"""Offer webhook triggered automation rules."""
from functools import partial

from aiohttp import hdrs
import voluptuous as vol

from openpeerpower.const import CONF_PLATFORM, CONF_WEBHOOK_ID
from openpeerpower.core import OppJob, callback
import openpeerpower.helpers.config_validation as cv

# mypy: allow-untyped-defs

DEPENDENCIES = ("webhook",)

TRIGGER_SCHEMA = vol.Schema(
    {vol.Required(CONF_PLATFORM): "webhook", vol.Required(CONF_WEBHOOK_ID): cv.string}
)


async def _handle_webhook(job, opp, webhook_id, request):
    """Handle incoming webhook."""
    result = {"platform": "webhook", "webhook_id": webhook_id}

    if "json" in request.headers.get(hdrs.CONTENT_TYPE, ""):
        result["json"] = await request.json()
    else:
        result["data"] = await request.post()

    result["query"] = request.query
    result["description"] = "webhook"
    opp.async_run_opp_job(job, {"trigger": result})


async def async_attach_trigger(opp, config, action, automation_info):
    """Trigger based on incoming webhooks."""
    webhook_id = config.get(CONF_WEBHOOK_ID)
    job = OppJob(action)
    opp.components.webhook.async_register(
        automation_info["domain"],
        automation_info["name"],
        webhook_id,
        partial(_handle_webhook, job),
    )

    @callback
    def unregister():
        """Unregister webhook."""
        opp.components.webhook.async_unregister(webhook_id)

    return unregister
