"""Provide configuration end points for scripts."""
from openpeerpower.components.script import DOMAIN, SCRIPT_ENTRY_SCHEMA
from openpeerpower.components.script.config import async_validate_config_item
from openpeerpower.config import SCRIPT_CONFIG_PATH
from openpeerpower.const import SERVICE_RELOAD
import openpeerpower.helpers.config_validation as cv

from . import EditKeyBasedConfigView


async def async_setup(opp):
    """Set up the script config API."""

    async def hook(action, config_key):
        """post_write_hook for Config View that reloads scripts."""
        await opp.services.async_call(DOMAIN, SERVICE_RELOAD)

    opp.http.register_view(
        EditKeyBasedConfigView(
            DOMAIN,
            "config",
            SCRIPT_CONFIG_PATH,
            cv.slug,
            SCRIPT_ENTRY_SCHEMA,
            post_write_hook=hook,
            data_validator=async_validate_config_item,
        )
    )
    return True
