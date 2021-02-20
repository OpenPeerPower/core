"""Config flow for iOS."""
from openpeerpower import config_entries
from openpeerpower.helpers import config_entry_flow

from .const import DOMAIN

config_entry_flow.register_discovery_flow(
    DOMAIN, "Open Peer Power iOS", lambda *_: True, config_entries.CONN_CLASS_CLOUD_PUSH
)
