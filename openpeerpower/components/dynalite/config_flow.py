"""Config flow to configure Dynalite hub."""
from typing import Any, Dict

from openpeerpower import config_entries
from openpeerpower.const import CONF_HOST

from .bridge import DynaliteBridge
from .const import DOMAIN, LOGGER


class DynaliteFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Dynalite config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self) -> None:
        """Initialize the Dynalite flow."""
        self.host = None

    async def async_step_import(self, import_info: Dict[str, Any]) -> Any:
        """Import a new bridge as a config entry."""
        LOGGER.debug("Starting async_step_import - %s", import_info)
        host = import_info[CONF_HOST]
        for entry in self.opp.config_entries.async_entries(DOMAIN):
            if entry.data[CONF_HOST] == host:
                if entry.data != import_info:
                    self.opp.config_entries.async_update_entry(entry, data=import_info)
                return self.async_abort(reason="already_configured")
        # New entry
        bridge = DynaliteBridge(self.opp, import_info)
        if not await bridge.async_setup():
            LOGGER.error("Unable to setup bridge - import info=%s", import_info)
            return self.async_abort(reason="no_connection")
        LOGGER.debug("Creating entry for the bridge - %s", import_info)
        return self.async_create_entry(title=host, data=import_info)
