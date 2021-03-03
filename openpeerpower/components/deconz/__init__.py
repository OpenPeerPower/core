"""Support for deCONZ devices."""
import voluptuous as vol

from openpeerpower.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PORT,
    EVENT_OPENPEERPOWER_STOP,
)
from openpeerpower.core import callback
from openpeerpower.helpers.entity_registry import async_migrate_entries

from .config_flow import get_master_gateway
from .const import CONF_GROUP_ID_BASE, CONF_MASTER_GATEWAY, DOMAIN
from .gateway import DeconzGateway
from .services import async_setup_services, async_unload_services

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({}, extra=vol.ALLOW_EXTRA)}, extra=vol.ALLOW_EXTRA
)


async def async_setup(opp, config):
    """Old way of setting up deCONZ integrations."""
    return True


async def async_setup_entry(opp, config_entry):
    """Set up a deCONZ bridge for a config entry.

    Load config, group, light and sensor data for server information.
    Start websocket for push notification of state changes from deCONZ.
    """
    if DOMAIN not in opp.data:
        opp.data[DOMAIN] = {}

    await async_update_group_unique_id(opp, config_entry)

    if not config_entry.options:
        await async_update_master_gateway(opp, config_entry)

    gateway = DeconzGateway(opp, config_entry)

    if not await gateway.async_setup():
        return False

    opp.data[DOMAIN][config_entry.unique_id] = gateway

    await gateway.async_update_device_registry()

    await async_setup_services(opp)

    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, gateway.shutdown)

    return True


async def async_unload_entry(opp, config_entry):
    """Unload deCONZ config entry."""
    gateway = opp.data[DOMAIN].pop(config_entry.unique_id)

    if not opp.data[DOMAIN]:
        await async_unload_services(opp)

    elif gateway.master:
        await async_update_master_gateway(opp, config_entry)
        new_master_gateway = next(iter(opp.data[DOMAIN].values()))
        await async_update_master_gateway(opp, new_master_gateway.config_entry)

    return await gateway.async_reset()


async def async_update_master_gateway(opp, config_entry):
    """Update master gateway boolean.

    Called by setup_entry and unload_entry.
    Makes sure there is always one master available.
    """
    master = not get_master_gateway(opp)
    options = {**config_entry.options, CONF_MASTER_GATEWAY: master}

    opp.config_entries.async_update_entry(config_entry, options=options)


async def async_update_group_unique_id(opp, config_entry) -> None:
    """Update unique ID entities based on deCONZ groups."""
    if not (old_unique_id := config_entry.data.get(CONF_GROUP_ID_BASE)):
        return

    new_unique_id: str = config_entry.unique_id

    @callback
    def update_unique_id(entity_entry):
        """Update unique ID of entity entry."""
        if f"{old_unique_id}-" not in entity_entry.unique_id:
            return None
        return {
            "new_unique_id": entity_entry.unique_id.replace(
                old_unique_id, new_unique_id
            )
        }

    await async_migrate_entries(opp, config_entry.entry_id, update_unique_id)
    data = {
        CONF_API_KEY: config_entry.data[CONF_API_KEY],
        CONF_HOST: config_entry.data[CONF_HOST],
        CONF_PORT: config_entry.data[CONF_PORT],
    }
    opp.config_entries.async_update_entry(config_entry, data=data)
