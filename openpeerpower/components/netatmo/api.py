"""API for Netatmo bound to OPP OAuth."""
from asyncio import run_coroutine_threadsafe

import pyatmo

from openpeerpower import config_entries, core
from openpeerpower.helpers import config_entry_oauth2_flow


class ConfigEntryNetatmoAuth(pyatmo.auth.NetatmoOAuth2):
    """Provide Netatmo authentication tied to an OAuth2 based config entry."""

    def __init__(
        self,
        opp: core.OpenPeerPower,
        config_entry: config_entries.ConfigEntry,
        implementation: config_entry_oauth2_flow.AbstractOAuth2Implementation,
    ):
        """Initialize Netatmo Auth."""
        self.opp = opp
        self.session = config_entry_oauth2_flow.OAuth2Session(
            opp, config_entry, implementation
        )
        super().__init__(token=self.session.token)

    def refresh_tokens(
        self,
    ) -> dict:
        """Refresh and return new Netatmo tokens using Open Peer Power OAuth2 session."""
        run_coroutine_threadsafe(
            self.session.async_ensure_token_valid(), self.opp.loop
        ).result()

        return self.session.token
