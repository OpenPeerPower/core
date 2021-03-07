"""The denonavr component."""
import logging

import voluptuous as vol

from openpeerpower import config_entries, core
from openpeerpower.const import ATTR_COMMAND, ATTR_ENTITY_ID, CONF_HOST
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import config_validation as cv, entity_registry as er
from openpeerpower.helpers.dispatcher import dispatcher_send

from .config_flow import (
    CONF_SHOW_ALL_SOURCES,
    CONF_ZONE2,
    CONF_ZONE3,
    DEFAULT_SHOW_SOURCES,
    DEFAULT_TIMEOUT,
    DEFAULT_ZONE2,
    DEFAULT_ZONE3,
    DOMAIN,
)
from .receiver import ConnectDenonAVR

CONF_RECEIVER = "receiver"
UNDO_UPDATE_LISTENER = "undo_update_listener"
SERVICE_GET_COMMAND = "get_command"

_LOGGER = logging.getLogger(__name__)

CALL_SCHEMA = vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids})

GET_COMMAND_SCHEMA = CALL_SCHEMA.extend({vol.Required(ATTR_COMMAND): cv.string})

SERVICE_TO_METHOD = {
    SERVICE_GET_COMMAND: {"method": "get_command", "schema": GET_COMMAND_SCHEMA}
}


def setup(opp: core.OpenPeerPower, config: dict):
    """Set up the denonavr platform."""

    def service_handler(service):
        method = SERVICE_TO_METHOD.get(service.service)
        data = service.data.copy()
        data["method"] = method["method"]
        dispatcher_send(opp, DOMAIN, data)

    for service in SERVICE_TO_METHOD:
        schema = SERVICE_TO_METHOD[service]["schema"]
        opp.services.register(DOMAIN, service, service_handler, schema=schema)

    return True


async def async_setup_entry(opp: core.OpenPeerPower, entry: config_entries.ConfigEntry):
    """Set up the denonavr components from a config entry."""
    opp.data.setdefault(DOMAIN, {})

    # Connect to receiver
    connect_denonavr = ConnectDenonAVR(
        opp,
        entry.data[CONF_HOST],
        DEFAULT_TIMEOUT,
        entry.options.get(CONF_SHOW_ALL_SOURCES, DEFAULT_SHOW_SOURCES),
        entry.options.get(CONF_ZONE2, DEFAULT_ZONE2),
        entry.options.get(CONF_ZONE3, DEFAULT_ZONE3),
    )
    if not await connect_denonavr.async_connect_receiver():
        raise ConfigEntryNotReady
    receiver = connect_denonavr.receiver

    undo_listener = entry.add_update_listener(update_listener)

    opp.data[DOMAIN][entry.entry_id] = {
        CONF_RECEIVER: receiver,
        UNDO_UPDATE_LISTENER: undo_listener,
    }

    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(entry, "media_player")
    )

    return True


async def async_unload_entry(
    opp: core.OpenPeerPower, config_entry: config_entries.ConfigEntry
):
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_forward_entry_unload(
        config_entry, "media_player"
    )

    opp.data[DOMAIN][config_entry.entry_id][UNDO_UPDATE_LISTENER]()

    # Remove zone2 and zone3 entities if needed
    entity_registry = await er.async_get_registry(opp)
    entries = er.async_entries_for_config_entry(entity_registry, config_entry.entry_id)
    zone2_id = f"{config_entry.unique_id}-Zone2"
    zone3_id = f"{config_entry.unique_id}-Zone3"
    for entry in entries:
        if entry.unique_id == zone2_id and not config_entry.options.get(CONF_ZONE2):
            entity_registry.async_remove(entry.entity_id)
            _LOGGER.debug("Removing zone2 from DenonAvr")
        if entry.unique_id == zone3_id and not config_entry.options.get(CONF_ZONE3):
            entity_registry.async_remove(entry.entity_id)
            _LOGGER.debug("Removing zone3 from DenonAvr")

    if unload_ok:
        opp.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


async def update_listener(
    opp: core.OpenPeerPower, config_entry: config_entries.ConfigEntry
):
    """Handle options update."""
    await opp.config_entries.async_reload(config_entry.entry_id)
