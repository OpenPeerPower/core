"""Offer API to configure the Open Peer Power auth provider."""
import voluptuous as vol

from openpeerpower.auth.providers import openpeerpower as auth_op
from openpeerpower.components import websocket_api
from openpeerpower.components.websocket_api import decorators
from openpeerpower.exceptions import Unauthorized


async def async_setup(opp):
    """Enable the Open Peer Power views."""
    opp.components.websocket_api.async_register_command(websocket_create)
    opp.components.websocket_api.async_register_command(websocket_delete)
    opp.components.websocket_api.async_register_command(websocket_change_password)
    opp.components.websocket_api.async_register_command(websocket_admin_change_password)
    return True


@decorators.websocket_command(
    {
        vol.Required("type"): "config/auth_provider/openpeerpower/create",
        vol.Required("user_id"): str,
        vol.Required("username"): str,
        vol.Required("password"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_create(opp, connection, msg):
    """Create credentials and attach to a user."""
    provider = auth_op.async_get_provider(opp)
    user = await opp.auth.async_get_user(msg["user_id"])

    if user is None:
        connection.send_error(msg["id"], "not_found", "User not found")
        return

    if user.system_generated:
        connection.send_error(
            msg["id"],
            "system_generated",
            "Cannot add credentials to a system generated user.",
        )
        return

    try:
        await provider.async_add_auth(msg["username"], msg["password"])
    except auth_op.InvalidUser:
        connection.send_error(msg["id"], "username_exists", "Username already exists")
        return

    credentials = await provider.async_get_or_create_credentials(
        {"username": msg["username"]}
    )
    await opp.auth.async_link_user(user, credentials)

    connection.send_result(msg["id"])


@decorators.websocket_command(
    {
        vol.Required("type"): "config/auth_provider/openpeerpower/delete",
        vol.Required("username"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_delete(opp, connection, msg):
    """Delete username and related credential."""
    provider = auth_op.async_get_provider(opp)
    credentials = await provider.async_get_or_create_credentials(
        {"username": msg["username"]}
    )

    # if not new, an existing credential exists.
    # Removing the credential will also remove the auth.
    if not credentials.is_new:
        await opp.auth.async_remove_credentials(credentials)

        connection.send_result(msg["id"])
        return

    try:
        await provider.async_remove_auth(msg["username"])
    except auth_op.InvalidUser:
        connection.send_error(
            msg["id"], "auth_not_found", "Given username was not found."
        )
        return

    connection.send_result(msg["id"])


@decorators.websocket_command(
    {
        vol.Required("type"): "config/auth_provider/openpeerpower/change_password",
        vol.Required("current_password"): str,
        vol.Required("new_password"): str,
    }
)
@websocket_api.async_response
async def websocket_change_password(opp, connection, msg):
    """Change current user password."""
    user = connection.user
    if user is None:
        connection.send_error(msg["id"], "user_not_found", "User not found")
        return

    provider = auth_op.async_get_provider(opp)
    username = None
    for credential in user.credentials:
        if credential.auth_provider_type == provider.type:
            username = credential.data["username"]
            break

    if username is None:
        connection.send_error(
            msg["id"], "credentials_not_found", "Credentials not found"
        )
        return

    try:
        await provider.async_validate_login(username, msg["current_password"])
    except auth_op.InvalidAuth:
        connection.send_error(
            msg["id"], "invalid_current_password", "Invalid current password"
        )
        return

    await provider.async_change_password(username, msg["new_password"])

    connection.send_result(msg["id"])


@decorators.websocket_command(
    {
        vol.Required(
            "type"
        ): "config/auth_provider/openpeerpower/admin_change_password",
        vol.Required("user_id"): str,
        vol.Required("password"): str,
    }
)
@decorators.require_admin
@decorators.async_response
async def websocket_admin_change_password(opp, connection, msg):
    """Change password of any user."""
    if not connection.user.is_owner:
        raise Unauthorized(context=connection.context(msg))

    user = await opp.auth.async_get_user(msg["user_id"])

    if user is None:
        connection.send_error(msg["id"], "user_not_found", "User not found")
        return

    provider = auth_op.async_get_provider(opp)

    username = None
    for credential in user.credentials:
        if credential.auth_provider_type == provider.type:
            username = credential.data["username"]
            break

    if username is None:
        connection.send_error(
            msg["id"], "credentials_not_found", "Credentials not found"
        )
        return

    try:
        await provider.async_change_password(username, msg["password"])
        connection.send_result(msg["id"])
    except auth_op.InvalidUser:
        connection.send_error(
            msg["id"], "credentials_not_found", "Credentials not found"
        )
        return
