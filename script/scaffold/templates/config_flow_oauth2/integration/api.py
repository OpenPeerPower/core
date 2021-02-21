"""API for NEW_NAME bound to Open Peer Power OAuth."""
from asyncio import run_coroutine_threadsafe

from aiohttp import ClientSession
import my_pypi_package

from openpeerpower import core
from openpeerpower.helpers import config_entry_oauth2_flow

# TODO the following two API examples are based on our suggested best practices
# for libraries using OAuth2 with requests or aiohttp. Delete the one you won't use.
# For more info see the docs at <insert url>.


class ConfigEntryAuth(my_pypi_package.AbstractAuth):
    """Provide NEW_NAME authentication tied to an OAuth2 based config entry."""

    def __init__(
        self,
       .opp: core.OpenPeerPower,
        oauth_session: config_entry_oauth2_flow.OAuth2Session,
    ):
        """Initialize NEW_NAME Auth."""
        self.opp = opp
        self.session = oauth_session
        super().__init__(self.session.token)

    def refresh_tokens(self) -> str:
        """Refresh and return new NEW_NAME tokens using Open Peer Power OAuth2 session."""
        run_coroutine_threadsafe(
            self.session.async_ensure_token_valid(), self.opp.loop
        ).result()

        return self.session.token["access_token"]


class AsyncConfigEntryAuth(my_pypi_package.AbstractAuth):
    """Provide NEW_NAME authentication tied to an OAuth2 based config entry."""

    def __init__(
        self,
        websession: ClientSession,
        oauth_session: config_entry_oauth2_flow.OAuth2Session,
    ):
        """Initialize NEW_NAME auth."""
        super().__init__(websession)
        self._oauth_session = oauth_session

    async def async_get_access_token(self) -> str:
        """Return a valid access token."""
        if not self._oauth_session.valid_token:
            await self._oauth_session.async_ensure_token_valid()

        return self._oauth_session.token["access_token"]
