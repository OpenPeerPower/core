"""Support for Twilio."""
from twilio.rest import Client
from twilio.twiml import TwiML
import voluptuous as vol

from openpeerpower.const import CONF_WEBHOOK_ID
from openpeerpower.helpers import config_entry_flow
import openpeerpower.helpers.config_validation as cv

from .const import DOMAIN

CONF_ACCOUNT_SID = "account_sid"
CONF_AUTH_TOKEN = "auth_token"

DATA_TWILIO = DOMAIN

RECEIVED_DATA = f"{DOMAIN}_data_received"

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional(DOMAIN): vol.Schema(
            {
                vol.Required(CONF_ACCOUNT_SID): cv.string,
                vol.Required(CONF_AUTH_TOKEN): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Set up the Twilio component."""
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]
    opp.data[DATA_TWILIO] = Client(
        conf.get(CONF_ACCOUNT_SID), conf.get(CONF_AUTH_TOKEN)
    )
    return True


async def handle_webhook(opp, webhook_id, request):
    """Handle incoming webhook from Twilio for inbound messages and calls."""
    data = dict(await request.post())
    data["webhook_id"] = webhook_id
    opp.bus.async_fire(RECEIVED_DATA, dict(data))

    return TwiML().to_xml()


async def async_setup_entry(opp, entry):
    """Configure based on config entry."""
    opp.components.webhook.async_register(
        DOMAIN, "Twilio", entry.data[CONF_WEBHOOK_ID], handle_webhook
    )
    return True


async def async_unload_entry(opp, entry):
    """Unload a config entry."""
    opp.components.webhook.async_unregister(entry.data[CONF_WEBHOOK_ID])
    return True


async_remove_entry = config_entry_flow.webhook_async_remove_entry
