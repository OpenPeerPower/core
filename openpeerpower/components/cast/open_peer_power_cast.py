"""Open Peer Power Cast integration for Cast."""
from typing import Optional

from pychromecast.controllers.homeassistant import HomeAssistantController
import voluptuous as vol

from openpeerpower import auth, config_entries, core
from openpeerpower.const import ATTR_ENTITY_ID
from openpeerpower.helpers import config_validation as cv, dispatcher
from openpeerpower.helpers.network import get_url

from .const import DOMAIN, SIGNAL_OPP_CAST_SHOW_VIEW

SERVICE_SHOW_VIEW = "show_lovelace_view"
ATTR_VIEW_PATH = "view_path"
ATTR_URL_PATH = "dashboard_path"


async def async_setup_op_cast(
    opp: core.OpenPeerPower, entry: config_entries.ConfigEntry
):
    """Set up Open Peer Power Cast."""
    user_id: Optional[str] = entry.data.get("user_id")
    user: Optional[auth.models.User] = None

    if user_id is not None:
        user = await opp.auth.async_get_user(user_id)

    if user is None:
        user = await opp.auth.async_create_system_user(
            "Open Peer Power Cast", [auth.GROUP_ID_ADMIN]
        )
        opp.config_entries.async_update_entry(
            entry, data={**entry.data, "user_id": user.id}
        )

    if user.refresh_tokens:
        refresh_token: auth.models.RefreshToken = list(user.refresh_tokens.values())[0]
    else:
        refresh_token = await opp.auth.async_create_refresh_token(user)

    async def handle_show_view(call: core.ServiceCall):
        """Handle a Show View service call."""
        opp_url = get_url(opp, require_ssl=True, prefer_external=True)

        controller = HomeAssistantController(
            # If you are developing Open Peer Power Cast, uncomment and set to your dev app id.
            # app_id="5FE44367",
            hass_url=opp_url,
            client_id=None,
            refresh_token=refresh_token.token,
        )

        dispatcher.async_dispatcher_send(
            opp,
            SIGNAL_OPP_CAST_SHOW_VIEW,
            controller,
            call.data[ATTR_ENTITY_ID],
            call.data[ATTR_VIEW_PATH],
            call.data.get(ATTR_URL_PATH),
        )

    opp.helpers.service.async_register_admin_service(
        DOMAIN,
        SERVICE_SHOW_VIEW,
        handle_show_view,
        vol.Schema(
            {
                ATTR_ENTITY_ID: cv.entity_id,
                ATTR_VIEW_PATH: str,
                vol.Optional(ATTR_URL_PATH): str,
            }
        ),
    )


async def async_remove_user(opp: core.OpenPeerPower, entry: config_entries.ConfigEntry):
    """Remove Open Peer Power Cast user."""
    user_id: Optional[str] = entry.data.get("user_id")

    if user_id is not None:
        user = await opp.auth.async_get_user(user_id)
        await opp.auth.async_remove_user(user)
