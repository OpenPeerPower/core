"""Config flow for IFTTT."""
from openpeerpower.helpers import config_entry_flow

from .const import DOMAIN

config_entry_flow.register_webhook_flow(
    DOMAIN,
    "IFTTT Webhook",
    {
        "applet_url": "https://ifttt.com/maker_webhooks",
        "docs_url": "https://www.openpeerpower.io/integrations/ifttt/",
    },
)
