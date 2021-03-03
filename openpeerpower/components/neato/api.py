"""API for Neato Botvac bound to Open Peer Power OAuth."""
from asyncio import run_coroutine_threadsafe

import pybotvac

from openpeerpower import config_entries, core
from openpeerpower.helpers import config_entry_oauth2_flow


class ConfigEntryAuth(pybotvac.OAuthSession):
    """Provide Neato Botvac authentication tied to an OAuth2 based config entry."""

    def __init__(
        self,
        opp: core.OpenPeerPower,
        config_entry: config_entries.ConfigEntry,
        implementation: config_entry_oauth2_flow.AbstractOAuth2Implementation,
    ):
        """Initialize Neato Botvac Auth."""
        self.opp = opp
        self.session = config_entry_oauth2_flow.OAuth2Session(
            opp, config_entry, implementation
        )
        super().__init__(self.session.token, vendor=pybotvac.Neato())

    def refresh_tokens(self) -> str:
        """Refresh and return new Neato Botvac tokens using Open Peer Power OAuth2 session."""
        run_coroutine_threadsafe(
            self.session.async_ensure_token_valid(), self.opp.loop
        ).result()

        return self.session.token["access_token"]


class NeatoImplementation(config_entry_oauth2_flow.LocalOAuth2Implementation):
    """Neato implementation of LocalOAuth2Implementation.

    We need this class because we have to add client_secret and scope to the authorization request.
    """

    @property
    def extra_authorize_data(self) -> dict:
        """Extra data that needs to be appended to the authorize url."""
        return {"client_secret": self.client_secret}

    async def async_generate_authorize_url(self, flow_id: str) -> str:
        """Generate a url for the user to authorize.

        We must make sure that the plus signs are not encoded.
        """
        url = await super().async_generate_authorize_url(flow_id)
        return f"{url}&scope=public_profile+control_robots+maps"
