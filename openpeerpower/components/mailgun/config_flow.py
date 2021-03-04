"""Config flow for Mailgun."""
from openpeerpower.helpers import config_entry_flow

from .const import DOMAIN

config_entry_flow.register_webhook_flow(
    DOMAIN,
    "Mailgun Webhook",
    {
        "mailgun_url": "https://documentation.mailgun.com/en/latest/user_manual.html#webhooks",
        "docs_url": "https://www.openpeerpower.io/integrations/mailgun/",
    },
)
