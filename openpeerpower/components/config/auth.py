"""Offer API to configure Open Peer Power auth."""
import voluptuous as vol

from openpeerpower.components import websocket_api

WS_TYPE_LIST = "config/auth/list"
SCHEMA_WS_LIST = websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
    {vol.Required("type"): WS_TYPE_LIST}
)

WS_TYPE_DELETE = "config/auth/delete"
SCHEMA_WS_DELETE = websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
    {vol.Required("type"): WS_TYPE_DELETE, vol.Required("user_id"): str}
)


async def async_setup(opp):
    """Enable the Open Peer Power views."""
    opp.components.websocket_api.async_register_command(
        WS_TYPE_LIST, websocket_list, SCHEMA_WS_LIST
    )
    opp.components.websocket_api.async_register_command(
        WS_TYPE_DELETE, websocket_delete, SCHEMA_WS_DELETE
    )
    opp.components.websocket_api.async_register_command(websocket_create)
    opp.components.websocket_api.async_register_command(websocket_update)
    return True


@websocket_api.require_admin
@websocket_api.async_response
async def websocket_list(opp, connection, msg):
    """Return a list of users."""
    result = [_user_info(u) for u in await opp.auth.async_get_users()]

    connection.send_message(websocket_api.result_message(msg["id"], result))


@websocket_api.require_admin
@websocket_api.async_response
async def websocket_delete(opp, connection, msg):
    """Delete a user."""
    if msg["user_id"] == connection.user.id:
        connection.send_message(
            websocket_api.error_message(
                msg["id"], "no_delete_self", "Unable to delete your own account"
            )
        )
        return

    user = await opp.auth.async_get_user(msg["user_id"])

    if not user:
        connection.send_message(
            websocket_api.error_message(msg["id"], "not_found", "User not found")
        )
        return

    await opp.auth.async_remove_user(user)

    connection.send_message(websocket_api.result_message(msg["id"]))


@websocket_api.require_admin
@websocket_api.async_response
@websocket_api.websocket_command(
    {
        vol.Required("type"): "config/auth/create",
        vol.Required("name"): str,
        vol.Optional("group_ids"): [str],
    }
)
async def websocket_create(opp, connection, msg):
    """Create a user."""
    user = await opp.auth.async_create_user(msg["name"], msg.get("group_ids"))

    connection.send_message(
        websocket_api.result_message(msg["id"], {"user": _user_info(user)})
    )


@websocket_api.require_admin
@websocket_api.async_response
@websocket_api.websocket_command(
    {
        vol.Required("type"): "config/auth/update",
        vol.Required("user_id"): str,
        vol.Optional("name"): str,
        vol.Optional("is_active"): bool,
        vol.Optional("group_ids"): [str],
    }
)
async def websocket_update(opp, connection, msg):
    """Update a user."""
    user = await opp.auth.async_get_user(msg.pop("user_id"))

    if not user:
        connection.send_message(
            websocket_api.error_message(
                msg["id"], websocket_api.const.ERR_NOT_FOUND, "User not found"
            )
        )
        return

    if user.system_generated:
        connection.send_message(
            websocket_api.error_message(
                msg["id"],
                "cannot_modify_system_generated",
                "Unable to update system generated users.",
            )
        )
        return

    if user.is_owner and msg["is_active"] is False:
        connection.send_message(
            websocket_api.error_message(
                msg["id"],
                "cannot_deactivate_owner",
                "Unable to deactivate owner.",
            )
        )
        return

    msg.pop("type")
    msg_id = msg.pop("id")

    await opp.auth.async_update_user(user, **msg)

    connection.send_message(
        websocket_api.result_message(msg_id, {"user": _user_info(user)})
    )


def _user_info(user):
    """Format a user."""

    ha_username = next(
        (
            cred.data.get("username")
            for cred in user.credentials
            if cred.auth_provider_type == "openpeerpower"
        ),
        None,
    )

    return {
        "id": user.id,
        "username": ha_username,
        "name": user.name,
        "is_owner": user.is_owner,
        "is_active": user.is_active,
        "system_generated": user.system_generated,
        "group_ids": [group.id for group in user.groups],
        "credentials": [{"type": c.auth_provider_type} for c in user.credentials],
    }
