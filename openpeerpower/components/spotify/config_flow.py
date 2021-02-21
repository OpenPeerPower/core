"""Config flow for Spotify."""
import logging
from typing import Any, Dict, Optional

from spotipy import Spotify
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.components import persistent_notification
from openpeerpower.helpers import config_entry_oauth2_flow

from .const import DOMAIN, SPOTIFY_SCOPES


class SpotifyFlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow to handle Spotify OAuth2 authentication."""

    DOMAIN = DOMAIN
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self) -> None:
        """Instantiate config flow."""
        super().__init__()
        self.entry: Optional[Dict[str, Any]] = None

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    @property
    def extra_authorize_data(self) -> Dict[str, Any]:
        """Extra data that needs to be appended to the authorize url."""
        return {"scope": ",".join(SPOTIFY_SCOPES)}

    async def async_oauth_create_entry(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an entry for Spotify."""
        spotify = Spotify(auth=data["token"]["access_token"])

        try:
            current_user = await self.opp.async_add_executor_job(spotify.current_user)
        except Exception:  # pylint: disable=broad-except
            return self.async_abort(reason="connection_error")

        name = data["id"] = current_user["id"]

        if self.entry and self.entry["id"] != current_user["id"]:
            return self.async_abort(reason="reauth_account_mismatch")

        if current_user.get("display_name"):
            name = current_user["display_name"]
        data["name"] = name

        await self.async_set_unique_id(current_user["id"])

        return self.async_create_entry(title=name, data=data)

    async def async_step_reauth(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Perform reauth upon migration of old entries."""
        if entry:
            self.entry = entry

        persistent_notification.async_create(
            self.opp,
            f"Spotify integration for account {entry['id']} needs to be re-authenticated. Please go to the integrations page to re-configure it.",
            "Spotify re-authentication",
            "spotify_reauth",
        )

        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Confirm reauth dialog."""
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                description_placeholders={"account": self.entry["id"]},
                data_schema=vol.Schema({}),
                errors={},
            )

        persistent_notification.async_dismiss(self.opp, "spotify_reauth")

        return await self.async_step_pick_implementation(
            user_input={"implementation": self.entry["auth_implementation"]}
        )
