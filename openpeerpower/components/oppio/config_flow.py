"""Config flow for Open Peer Power Supervisor integration."""
import logging

from openpeerpower import config_entries

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Open Peer Power Supervisor."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_system(self, user_input=None):
        """Handle the initial step."""
        # We only need one Opp.io config entry
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=DOMAIN.title(), data={})
