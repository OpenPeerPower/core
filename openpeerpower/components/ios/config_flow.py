"""Config flow for iOS."""
from openpeerpower.helpers import config_entry_flow

from .const import DOMAIN

config_entry_flow.register_discovery_flow(DOMAIN, "Open Peer Power iOS", lambda *_: True)
