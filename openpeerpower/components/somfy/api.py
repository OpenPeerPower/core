"""API for Somfy bound to Open Peer Power OAuth."""
from __future__ import annotations

from asyncio import run_coroutine_threadsafe

from pymfy.api import somfy_api

from openpeerpower import config_entries, core
from openpeerpower.helpers import config_entry_oauth2_flow


class ConfigEntrySomfyApi(somfy_api.SomfyApi):
    """Provide a Somfy API tied into an OAuth2 based config entry."""

    def __init__(
        self,
        opp: core.OpenPeerPower,
        config_entry: config_entries.ConfigEntry,
        implementation: config_entry_oauth2_flow.AbstractOAuth2Implementation,
    ) -> None:
        """Initialize the Config Entry Somfy API."""
        self.opp = opp
        self.config_entry = config_entry
        self.session = config_entry_oauth2_flow.OAuth2Session(
            opp, config_entry, implementation
        )
        super().__init__(None, None, token=self.session.token)

    def refresh_tokens(
        self,
    ) -> dict[str, str | int]:
        """Refresh and return new Somfy tokens using Open Peer Power OAuth2 session."""
        run_coroutine_threadsafe(
            self.session.async_ensure_token_valid(), self.opp.loop
        ).result()

        return self.session.token
