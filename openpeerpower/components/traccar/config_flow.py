"""Config flow for Traccar."""
from openpeerpower.helpers import config_entry_flow

from .const import DOMAIN

config_entry_flow.register_webhook_flow(
    DOMAIN,
    "Traccar Webhook",
    {"docs_url": "https://www.openpeerpower.io/integrations/traccar/"},
)
