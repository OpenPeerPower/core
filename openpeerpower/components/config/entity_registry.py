"""HTTP views to interact with the entity registry."""
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.components import websocket_api
from openpeerpower.components.websocket_api.const import ERR_NOT_FOUND
from openpeerpower.components.websocket_api.decorators import (
    async_response,
    require_admin,
)
from openpeerpower.core import callback
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.entity_registry import async_get_registry


async def async_setup(opp):
    """Enable the Entity Registry views."""
    opp.components.websocket_api.async_register_command(websocket_list_entities)
    opp.components.websocket_api.async_register_command(websocket_get_entity)
    opp.components.websocket_api.async_register_command(websocket_update_entity)
    opp.components.websocket_api.async_register_command(websocket_remove_entity)
    return True


@async_response
@websocket_api.websocket_command({vol.Required("type"): "config/entity_registry/list"})
async def websocket_list_entities(opp, connection, msg):
    """Handle list registry entries command.

    Async friendly.
    """
    registry = await async_get_registry(opp)
    connection.send_message(
        websocket_api.result_message(
            msg["id"], [_entry_dict(entry) for entry in registry.entities.values()]
        )
    )


@async_response
@websocket_api.websocket_command(
    {
        vol.Required("type"): "config/entity_registry/get",
        vol.Required("entity_id"): cv.entity_id,
    }
)
async def websocket_get_entity(opp, connection, msg):
    """Handle get entity registry entry command.

    Async friendly.
    """
    registry = await async_get_registry(opp)
    entry = registry.entities.get(msg["entity_id"])

    if entry is None:
        connection.send_message(
            websocket_api.error_message(msg["id"], ERR_NOT_FOUND, "Entity not found")
        )
        return

    connection.send_message(
        websocket_api.result_message(msg["id"], _entry_ext_dict(entry))
    )


@require_admin
@async_response
@websocket_api.websocket_command(
    {
        vol.Required("type"): "config/entity_registry/update",
        vol.Required("entity_id"): cv.entity_id,
        # If passed in, we update value. Passing None will remove old value.
        vol.Optional("name"): vol.Any(str, None),
        vol.Optional("icon"): vol.Any(str, None),
        vol.Optional("area_id"): vol.Any(str, None),
        vol.Optional("new_entity_id"): str,
        # We only allow setting disabled_by user via API.
        vol.Optional("disabled_by"): vol.Any("user", None),
    }
)
async def websocket_update_entity(opp, connection, msg):
    """Handle update entity websocket command.

    Async friendly.
    """
    registry = await async_get_registry(opp)

    if msg["entity_id"] not in registry.entities:
        connection.send_message(
            websocket_api.error_message(msg["id"], ERR_NOT_FOUND, "Entity not found")
        )
        return

    changes = {}

    for key in ("name", "icon", "area_id", "disabled_by"):
        if key in msg:
            changes[key] = msg[key]

    if "new_entity_id" in msg and msg["new_entity_id"] != msg["entity_id"]:
        changes["new_entity_id"] = msg["new_entity_id"]
        if opp.states.get(msg["new_entity_id"]) is not None:
            connection.send_message(
                websocket_api.error_message(
                    msg["id"],
                    "invalid_info",
                    "Entity with this ID is already registered",
                )
            )
            return

    if "disabled_by" in msg and msg["disabled_by"] is None:
        entity = registry.entities[msg["entity_id"]]
        if entity.device_id:
            device_registry = await opp.helpers.device_registry.async_get_registry()
            device = device_registry.async_get(entity.device_id)
            if device.disabled:
                connection.send_message(
                    websocket_api.error_message(
                        msg["id"], "invalid_info", "Device is disabled"
                    )
                )
                return

    try:
        if changes:
            entry = registry.async_update_entity(msg["entity_id"], **changes)
    except ValueError as err:
        connection.send_message(
            websocket_api.error_message(msg["id"], "invalid_info", str(err))
        )
        return
    result = {"entity_entry": _entry_ext_dict(entry)}
    if "disabled_by" in changes and changes["disabled_by"] is None:
        config_entry = opp.config_entries.async_get_entry(entry.config_entry_id)
        if config_entry and not config_entry.supports_unload:
            result["require_restart"] = True
        else:
            result["reload_delay"] = config_entries.RELOAD_AFTER_UPDATE_DELAY
    connection.send_result(msg["id"], result)


@require_admin
@async_response
@websocket_api.websocket_command(
    {
        vol.Required("type"): "config/entity_registry/remove",
        vol.Required("entity_id"): cv.entity_id,
    }
)
async def websocket_remove_entity(opp, connection, msg):
    """Handle remove entity websocket command.

    Async friendly.
    """
    registry = await async_get_registry(opp)

    if msg["entity_id"] not in registry.entities:
        connection.send_message(
            websocket_api.error_message(msg["id"], ERR_NOT_FOUND, "Entity not found")
        )
        return

    registry.async_remove(msg["entity_id"])
    connection.send_message(websocket_api.result_message(msg["id"]))


@callback
def _entry_dict(entry):
    """Convert entry to API format."""
    return {
        "config_entry_id": entry.config_entry_id,
        "device_id": entry.device_id,
        "area_id": entry.area_id,
        "disabled_by": entry.disabled_by,
        "entity_id": entry.entity_id,
        "name": entry.name,
        "icon": entry.icon,
        "platform": entry.platform,
    }


@callback
def _entry_ext_dict(entry):
    """Convert entry to API format."""
    data = _entry_dict(entry)
    data["original_name"] = entry.original_name
    data["original_icon"] = entry.original_icon
    data["unique_id"] = entry.unique_id
    data["capabilities"] = entry.capabilities
    return data
