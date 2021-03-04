"""Config flow to configure zone component.

This is no longer in use. This file is around so that existing
config entries will remain to be loaded and then automatically
migrated to the storage collection.
"""
from openpeerpower import config_entries

from .const import DOMAIN  # pylint: disable=unused-import


class ZoneConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Stub zone config flow class."""
