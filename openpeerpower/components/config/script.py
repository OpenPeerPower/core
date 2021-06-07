"""Provide configuration end points for scripts."""
from openpeerpower.components.script import DOMAIN
from openpeerpower.components.script.config import (
    SCRIPT_ENTITY_SCHEMA,
    async_validate_config_item,
)
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
        EditScriptConfigView(
            DOMAIN,
            "config",
            SCRIPT_CONFIG_PATH,
            cv.slug,
            SCRIPT_ENTITY_SCHEMA,
            post_write_hook=hook,
            data_validator=async_validate_config_item,
        )
    )
    return True


class EditScriptConfigView(EditKeyBasedConfigView):
    """Edit script config."""

    def _write_value(self, opp, data, config_key, new_value):
        """Set value."""
        data[config_key] = new_value
