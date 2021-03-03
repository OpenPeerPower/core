"""Support for Mailgun."""
import hashlib
import hmac
import json
import logging

import voluptuous as vol

from openpeerpower.const import CONF_API_KEY, CONF_DOMAIN, CONF_WEBHOOK_ID
from openpeerpower.helpers import config_entry_flow
import openpeerpower.helpers.config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_SANDBOX = "sandbox"

DEFAULT_SANDBOX = False

MESSAGE_RECEIVED = f"{DOMAIN}_message_received"

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional(DOMAIN): vol.Schema(
            {
                vol.Required(CONF_API_KEY): cv.string,
                vol.Required(CONF_DOMAIN): cv.string,
                vol.Optional(CONF_SANDBOX, default=DEFAULT_SANDBOX): cv.boolean,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Set up the Mailgun component."""
    if DOMAIN not in config:
        return True

    opp.data[DOMAIN] = config[DOMAIN]
    return True


async def handle_webhook(opp, webhook_id, request):
    """Handle incoming webhook with Mailgun inbound messages."""
    body = await request.text()
    try:
        data = json.loads(body) if body else {}
    except ValueError:
        return None

    if isinstance(data, dict) and "signature" in data:
        if await verify_webhook(opp, **data["signature"]):
            data["webhook_id"] = webhook_id
            opp.bus.async_fire(MESSAGE_RECEIVED, data)
            return

    _LOGGER.warning(
        "Mailgun webhook received an unauthenticated message - webhook_id: %s",
        webhook_id,
    )


async def verify_webhook(opp, token=None, timestamp=None, signature=None):
    """Verify webhook was signed by Mailgun."""
    if DOMAIN not in opp.data:
        _LOGGER.warning("Cannot validate Mailgun webhook, missing API Key")
        return True

    if not (token and timestamp and signature):
        return False

    hmac_digest = hmac.new(
        key=bytes(opp.data[DOMAIN][CONF_API_KEY], "utf-8"),
        msg=bytes(f"{timestamp}{token}", "utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(signature, hmac_digest)


async def async_setup_entry(opp, entry):
    """Configure based on config entry."""
    opp.components.webhook.async_register(
        DOMAIN, "Mailgun", entry.data[CONF_WEBHOOK_ID], handle_webhook
    )
    return True


async def async_unload_entry(opp, entry):
    """Unload a config entry."""
    opp.components.webhook.async_unregister(entry.data[CONF_WEBHOOK_ID])
    return True


async_remove_entry = config_entry_flow.webhook_async_remove_entry
